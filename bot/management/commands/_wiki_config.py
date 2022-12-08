import yaml
import praw
import prawcore
import logging
from typing import List


logger = logging.getLogger('contest-bot')


# Default configuration for subreddits
default_config = {
    'enabled': False,
    'window': '1 day',
    'winner_actions': {
        'sticky': True,
        'flair': False,
    },
}


# Apply defaults if required config keys are missing
def apply_defaults(parsed: dict) -> dict:
    for key in default_config.keys():
        if key not in parsed.keys():
            parsed[key] = default_config[key]

    return parsed


# Fetch configuration from subreddits wiki
def fetch_config(subreddits_list: List[praw.reddit.Subreddit]) -> dict:
    config_dictionary = {}

    for subreddit in subreddits_list:
        logger.info(f'Fetching config for subreddit %s' % subreddit.display_name)

        try:
            s = subreddit.wiki['botconfig/contest']
            parsed = yaml.safe_load(s.content_md)
            config_dictionary[subreddit.display_name] = apply_defaults(parsed)

        except prawcore.exceptions.NotFound:
            config_dictionary[subreddit.display_name] = default_config
            logger.error(f'Config not found for subreddit %s' % subreddit.display_name)

        except prawcore.exceptions.PrawcoreException as exception:
            logger.error(f'PrawcoreException {exception}')

    return config_dictionary
