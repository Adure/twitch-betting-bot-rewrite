# twitch-betting-bot-rewrite

Twitch bot which allows viewers to bet points on the outcome of a streamer's current game, whether they will win or lose, using StreamElements' loyaly points. You can also create custom votes allowing viewers to bet on the outcome of something in the stream, with an optional wager and custom outcomes.

## Commands
All commands can also be invoked with `?` as a prefix.

| Mod-only | Command                                              | Description |
| :------: | ---------------------------------------------------- | ----------- |
| Yes      | `!open`                                              | Opens betting and clears betters list.
| Yes      | `!close`                                             | Closes betting and prints information on number of betters, percent of win bets to loss bets, and amount of points bet.
| No       | `!bet <outcome> <wager>`                             | Enter your bet and subtract the wager amount from your account.
| Yes      | `!win`                                               | Sets game as win and awards points to all users who bet win.
| Yes      | `!loss`                                              | Sets game as loss and awards points to all users who bet loss.
| Yes      | `!status`                                            | Prints whether betting is open or closed, and how many people have bet.
| No       | `!print`                                             | Prints the current list of betters along with their outcome and wager.
| Yes      | `!createvote "<question>" <outcome1> <outcome2> ...` | Create vote with the inputted question and outcomes. You can supply as many outcomes as needed. Outcomes comprised of two or more words need to be wrapped in speech marks.
| Yes      | `!endvote <outcome>`                                 | Ends voting and awards the wager amount to all users who correctly voted on the outcome.
| No       | `!vote <outcome> <wager>` (wager is optional)        | Enter into the currently running vote with your outcome and optional wager.


## Examples
```
!bet win 500

!createvote "Will the streamer do this in 30 seconds?" yes no

!vote yes 200

!endvote yes
```