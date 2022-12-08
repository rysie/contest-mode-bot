from django.core.management.base import BaseCommand
from typing import List
import prawcore

from threading import Event, Thread
from bot.management.commands._wiki_config import fetch_config as fetch_wiki_config
from bot.management.commands._auth import authenticate_reddit_client
from bot.management.commands._handle_submission import handle_new_submission
from bot.management.commands._run_contest import run_contest

import praw
from prawcore.exceptions import PrawcoreException

import logging

logger = logging.getLogger('contest-bot')

INTERVAL_STREAM_WATCH = 10
INTERVAL_RUN_CONTEST = 60


#
# Watch for new submissions and add them to DB
#
class WatchSubredditsStream(Thread):
    def __init__(
            self,
            stop_flag: Event,
            reddit_instance: praw.Reddit,
            subreddits_list: List[praw.reddit.Subreddit]
    ):
        Thread.__init__(self)
        self.stopped = stop_flag
        self.reddit_instance = reddit_instance
        self.subreddits_list = subreddits_list
        self.streams = {}

        for subreddit in subreddits_list:
            self.streams[subreddit.display_name] = subreddit.stream.submissions(pause_after=0)

    def run(self):
        while not self.stopped.wait(INTERVAL_STREAM_WATCH):
            for key in self.streams:
                stream = self.streams[key]

                for submission in stream:
                    if submission is None:
                        break

                    if submission.author is None:
                        continue

                    try:
                        handle_new_submission(submission)

                    except PrawcoreException:
                        logger.info(f'Error fetching info for {submission.name} ({submission.title})')


#
# Run the contest!
# Continuously check for possible winner.
#
class RunContest(Thread):
    def __init__(
            self,
            stop_flag: Event,
            reddit_instance: praw.Reddit,
            subreddits_list: List[praw.reddit.Subreddit]
    ):
        Thread.__init__(self)
        self.stopped = stop_flag
        self.reddit_instance = reddit_instance
        self.subreddits_list = subreddits_list

    def run(self):
        while not self.stopped.wait(INTERVAL_RUN_CONTEST):
            wiki_config = fetch_wiki_config(self.subreddits_list)
            run_contest(self.reddit_instance, self.subreddits_list, wiki_config)


class Command(BaseCommand):
    help = 'Run Contest Mode Bot'
    try:
        reddit_instance = authenticate_reddit_client()
        my_subreddits = list(
            filter(
                lambda sub: not sub.display_name.startswith('u_'), reddit_instance.user.moderator_subreddits()
            )
        )

    except prawcore.exceptions.PrawcoreException as exception:
        logger.error(f'PrawcoreException during bot startup: {exception}')

    def handle(self, *args, **options):
        logger.info('-' * 10 + f' starting bot')

        stop_flag = Event()

        thread_watch_subreddits = WatchSubredditsStream(stop_flag, self.reddit_instance, self.my_subreddits)
        thread_run_contest = RunContest(stop_flag, self.reddit_instance, self.my_subreddits)

        thread_watch_subreddits.start()
        thread_run_contest.start()

        try:
            print('Press Ctrl+C to exit')

        except KeyboardInterrupt:
            stop_flag.set()
            logger.info('-' * 10 + f' bot killed.')
