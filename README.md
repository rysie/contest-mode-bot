#### Contest mode for Reddit submissions
# contest-mode-bot

This is a Python bot for Reddit that provides a **continuous contest** for submissions. 

The bot checks posts within a certain timeframe (1 day by default, configurable), picks the best one by the number 
of upvotes and makes it sticky + flairs it with specified `flair_template_id`.

The bot runs checks every minute, so the contest is continuous, and the winner can change anytime depending on 
the number of current upvotes. When bot detects winner change, existing winner gets removed from pinned position, their
original post flair gets restored, and the new winner takes their place.

Due to Reddit limitations, there are only 2 slots available for pinned (sticky) posts (#1 and #2). 
Because of that, when the bot is running and both slots are taken, **it will remove pinned post #2** to make place 
for contest winner. 

### Using the bot

1. Invite the bot as subreddit moderator (Manage Wiki Pages, Manage Posts & Comments). 
2. Add /botconfig/contest wiki page (https://www.reddit.com/r/<subreddit>/about/wiki/botconfig/contest/)
3. Put the following YAML config in the wiki:
```
enabled: true
window: 1 day
winner_actions:
  flair: replace-this-with-your-flair-template-id
```

The bot will read wiki configuration every iteration, just before picking the winner. To stop the bot, simply set 
`enabled` attribute to `false`.
