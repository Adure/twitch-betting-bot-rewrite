# twitch-betting-bot-rewrite

Twitch bot which allows viewers to bet points on the outcome of a streamer's current game, whether they will win or lose, using StreamElements' loyalty points. You can also create custom votes allowing viewers to bet on the outcome of something in the stream, with an optional wager and custom outcomes.

## Commands
Commands marked with 'M' are mod-only commands. All commands can also be invoked with `?` as a prefix.
```
M - !open
                # Opens betting and clears betters list
M - !close
                # Closes betting and prints information on number of betters,
                  percent of win bets to loss bets, and amount of points bet
!bet <outcome> <wager>
                # Enter your bet and subtract the wager amount from your account
M - !win
                # Sets game as win and awards points to all users who bet win
M - !loss
                # Sets game as loss and awards points to all users who bet loss
M - !status
                # Prints whether betting is open or closed, and how many people have bet
!print
                # Prints the current list of betters along with their outcome and wager
M - !createvote "<question>" <outcome1> <outcome2> ...
                # Create vote with the inputted question and outcomes. You can supply as many outcomes as needed.
                  Outcomes comprised of two or more words need to be wrapped in speech marks.
M - !endvote <outcome>
                # Ends voting and awards the wager amount to all users who correctly voted on the outcome
!vote <outcome> <wager>  (wager is optional)
                # Enter into the currently running vote with your outcome and optional wager
```

## Examples
```
!bet win 500

!createvote "Will the streamer do this in 30 seconds?" yes no

!vote yes 200

!endvote yes
```