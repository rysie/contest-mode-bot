from django.db.models import Q
from django.utils.timezone import make_aware
from datetime import datetime

import praw
import prawcore
import logging

from prawcore.exceptions import NotFound, Forbidden

from bot.models import Redditor, Subreddit, Submission


logger = logging.getLogger('contest-bot')


def is_removed_or_deleted(
        submission: praw.reddit.Submission
) -> bool:
    # account deleted
    if submission.author is None:
        # post deleted, account may or may not be deleted
        if submission.selftext == '[deleted]':
            return True

        # post removed and account deleted
        if submission.selftext == '[removed]':
            return True

        return True

    # post removed
    if submission.selftext == '[removed]':
        return True

    # submission exists
    return False


def create_redditor(
        redditor_name: str
) -> Redditor:
    redditor = Redditor(
        name=redditor_name,
    )
    redditor.save()

    return redditor


def get_redditor(
        redditor_name: str
) -> Redditor:
    redditor = Redditor.objects.filter(Q(name=redditor_name)).first()

    if redditor is None:
        redditor = create_redditor(redditor_name)

    return redditor


def create_subreddit(
        subreddit_name: str
) -> Subreddit:
    subreddit = Subreddit(
        name=subreddit_name,
    )
    subreddit.save()

    return subreddit


def get_subreddit(
        subreddit_name: str
) -> Subreddit:
    subreddit = Subreddit.objects.filter(Q(name=subreddit_name)).first()

    if subreddit is None:
        subreddit = create_subreddit(subreddit_name)

    return subreddit


def create_submission(
        submission_praw: praw.reddit.Submission,
        redditor: Redditor,
        subreddit: Subreddit
) -> Submission:
    dt = make_aware(datetime.fromtimestamp(submission_praw.created_utc))

    if hasattr(submission_praw, 'link_flair_template_id'):
        link_flair_template_id = submission_praw.link_flair_template_id
    else:
        link_flair_template_id = None

    submission = Submission(
        author=redditor,
        created_at=dt,
        deleted=is_removed_or_deleted(submission_praw),
        original_flair_template_id=link_flair_template_id,
        submission_id=submission_praw.id,
        subreddit=subreddit,
        title=submission_praw.title,
        upvotes=int(submission_praw.score),
    )

    submission.save()

    return submission


def submission_exists(
        submission_praw: praw.reddit.Submission
) -> bool:
    return isinstance(
        Submission.objects.filter(Q(submission_id=submission_praw.id)).first(),
        Submission
    )


def handle_new_submission(
        submission_praw: praw.reddit.Submission
) -> None:
    if not submission_exists(submission_praw):
        logger.info(f'Creating new submission: {submission_praw.id} '
                    f'({submission_praw.author.name}: {submission_praw.title})')

        redditor = get_redditor(submission_praw.author.name)
        subreddit = get_subreddit(submission_praw.subreddit.display_name)
        create_submission(submission_praw, redditor, subreddit)
    else:
        logger.info(f'Submission {submission_praw.id} already exists')

    return None


#
# Remove sticky submission having 'Contest Winner' flair and restore original flair.
# If none of the submissions have 'Contest Winner' flair, remove second sticky.
# This is to make sure that we have place to stick winner's post (max 2 sticky submissions are allowed).
#
def reset_subreddit_state(
        reddit_instance: praw.Reddit,
        subreddit_name: str,
        flair: str=False,
) -> None:
    sticky = {}

    logger.info(f'Resetting r/{subreddit_name} state...')

    try:
        sticky[1] = reddit_instance.subreddit(subreddit_name).sticky(1)
        logger.info(f'Sticky post #1: {sticky[1].title} by {sticky[1].author.name}')
    except NotFound:
        logger.info(f'Sticky post #1: not found')
        sticky[1] = None
    except prawcore.exceptions.PrawcoreException as exception:
        logger.error(f'PrawcoreException when fetching sticky posts (1): {exception}')

    try:
        sticky[2] = reddit_instance.subreddit(subreddit_name).sticky(2)
        logger.info(f'Sticky post #2: {sticky[2].title} by {sticky[2].author.name}')
    except NotFound:
        logger.info(f'Sticky post #2: not found')
        sticky[2] = None
    except prawcore.exceptions.PrawcoreException as exception:
        logger.error(f'PrawcoreException when fetching sticky posts (2): {exception}')

    try:
        if isinstance(sticky[1], praw.reddit.Submission) and sticky[1].link_flair_template_id == flair:
            logger.info(f'Remove distinguish flag from sticky #1 {sticky[1].title} (flair {flair} found)')

            submission_object = Submission.objects.filter(submission_id=sticky[1].id).first()
            if isinstance(submission_object, Submission) and submission_object.original_flair_template_id:
                sticky[1].flair.select(submission_object.original_flair_template_id)
            else:
                sticky[1].flair.select(None)

            sticky[1].mod.sticky(state=False)
            return None

        if isinstance(sticky[2], praw.reddit.Submission) and sticky[2].link_flair_template_id == flair:
            logger.info(f'Remove distinguish flag from sticky #2 {sticky[2].title} (flair {flair} found)')

            submission_object = Submission.objects.filter(submission_id=sticky[2].id).first()
            if isinstance(submission_object, Submission) and submission_object.original_flair_template_id:
                sticky[2].flair.select(submission_object.original_flair_template_id)
            else:
                sticky[2].flair.select(None)

            sticky[2].mod.sticky(state=False)
            return None

        if isinstance(sticky[1], praw.reddit.Submission) and isinstance(sticky[2], praw.reddit.Submission):
            logger.info(f'No flaired stickies, force remove distinguish flag from sticky #2')
            sticky[2].mod.sticky(state=False)
            return None

    except Forbidden:
        logger.error(f'Can\'t remove sticky, check moderator privileges!')
        return None

    except prawcore.exceptions.PrawcoreException as exception:
        logger.error(f'PrawcoreException during sticky removal: {exception}')
        return None

    logger.info(f'Cool, we already have a free slot for sticky!')

    return None


#
# Make submission sticky and flair it with 'Contest Winner' flair
#
def promote_submission(
        reddit_instance: praw.Reddit,
        best_submission: Submission,
        flair: str,
) -> None:
    logger.info(f'Promoting best submission in '
                f'r/{best_submission.subreddit.name} '
                f'{best_submission.title} by {best_submission.author.name}...')

    praw_submission = reddit_instance.submission(best_submission.submission_id)

    try:
        praw_submission.flair.select(flair)
        praw_submission.mod.sticky(state=True)
        best_submission.currently_promoted = True
        best_submission.save()
    except Forbidden:
        logger.error(f'Can\'t add sticky or flair submission, check moderator privileges!')
        return None
    except prawcore.exceptions.PrawcoreException as exception:
        logger.error(f'PrawcoreException during setting sticky: {exception}')
        return None

    logger.info(f'Added sticky and flaired.')

    return None
