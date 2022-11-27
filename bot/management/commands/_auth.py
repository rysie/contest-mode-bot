import praw
from brain.settings import env


# Simple auth mechanism, change it to token auth
def authenticate_reddit_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=env('PRAW_CLIENT_ID'),
        client_secret=env('PRAW_CLIENT_SECRET'),
        password=env('PRAW_PASSWORD'),
        username=env('PRAW_USERNAME'),
        user_agent=env('PRAW_USER_AGENT'),
    )
