from django.db.models import QuerySet
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from typing import List

import praw
import prawcore
import logging
import re

from bot.models import Subreddit, Submission
from bot.management.commands._handle_submission \
    import is_removed_or_deleted, reset_subreddit_state, promote_submission

logger = logging.getLogger('contest-bot')


#
# Determine window frame for the submission to compare against
#
def get_min_date(max_date: datetime, window: str) -> datetime:
    window_numeric = int(re.sub('[^0-9]', '', window))

    if 'minute' in window:
        return max_date - timedelta(minutes=window_numeric)

    if 'hour' in window:
        return max_date - timedelta(hours=window_numeric)

    if 'day' in window:
        return max_date - timedelta(days=window_numeric)

    if 'week' in window:
        return max_date - timedelta(weeks=window_numeric)

    return max_date


#
# Fetch submissions in defined time window
#
def get_submissions_in_window(
        reddit_instance: praw.Reddit,
        subreddit: praw.reddit.Subreddit,
        window: str
) -> QuerySet:
    max_date = datetime.today()
    min_date = get_min_date(max_date, window)
    submission_ids = []

    subreddit_object = Subreddit.objects.filter(name=subreddit.display_name).first()

    saved_submissions = Submission.objects.filter(
        created_at__gt=make_aware(min_date),
        created_at__lt=make_aware(max_date),
        subreddit=subreddit_object,
        deleted=False,
    )

    logger.info(f'Getting info for {len(saved_submissions)} submissions in {subreddit.display_name}')

    for saved_submission in saved_submissions:
        submission_ids.append(saved_submission.submission_id)
        submission_ids_for_praw = [i if i.startswith('t3_') else f't3_{i}' for i in submission_ids]

        try:
            for praw_submission in reddit_instance.info(submission_ids_for_praw):
                submission = Submission.objects.filter(submission_id=praw_submission.id).first()

                if is_removed_or_deleted(praw_submission):
                    submission.deleted = True
                else:
                    submission.upvotes = int(praw_submission.score)

                submission.save()

        except prawcore.exceptions.PrawcoreException as exception:
            logger.error(f'PrawcoreException during fetching list of '
                         f'subreddits (get_submissions_in_window): {exception}')

    logger.info(f'Done fetching subreddit info')

    return Submission.objects.filter(
        created_at__gt=make_aware(min_date),
        created_at__lt=make_aware(max_date),
        subreddit=subreddit_object,
        deleted=False,
    ).order_by('-upvotes')


#
# Main process for picking the winner
#
def run_contest(
        reddit_instance: praw.Reddit,
        subreddits_list: List[praw.reddit.Subreddit],
        wiki_config: dict
) -> None:
    for subreddit in subreddits_list:
        subreddit_config = wiki_config[subreddit.display_name]

        if not subreddit_config['enabled']:
            logger.info(f'Processing disabled for r/{subreddit.display_name}')
            continue

        submissions = get_submissions_in_window(reddit_instance, subreddit, subreddit_config['window'])
        best_submission = submissions.first()

        # Check if the best submission is not currently promoted
        # to avoid unnecessary resetting subreddit and promoting again
        if isinstance(best_submission, Submission) and not best_submission.currently_promoted:
            logger.info(f'Best submission changed: "{best_submission.title}" '
                        f'by {best_submission.author.name} '
                        f'({best_submission.upvotes} upvotes)')

            subreddit_object = Subreddit.objects.filter(name=subreddit).first()

            for promoted_submission in Submission.objects.filter(subreddit=subreddit_object, currently_promoted=True):
                promoted_submission.currently_promoted = False
                promoted_submission.save()

            reset_subreddit_state(
                reddit_instance,
                best_submission.subreddit.name,
                subreddit_config['winner_actions']['flair']
            )

            promote_submission(
                reddit_instance,
                best_submission,
                subreddit_config['winner_actions']['flair']
            )

    return None
