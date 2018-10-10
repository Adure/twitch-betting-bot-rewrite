from twitchio.ext import commands
import requests
import sys
import os
from pathlib import Path
import random
import re
import json
import logging
import strawpoll
from auth import jwt_token, access_token, token, api_token

#jwt_token = jwt_token

access_token = access_token
r = requests.get('https://api.twitch.tv/helix/users?login=adure_bot',
headers={'Authorization':access_token}
)
channel_id = r.json()

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('logs.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

## HELPER FUNCTIONS ##
################################################################################
def restart_program():
	python = sys.executable
	os.execl(python, python, *sys.argv)

def check_points(channel, user):
	with open('./channels.json') as channels_file:
		content = json.load(channels_file)
		channel = content[channel]['id']
	r = requests.get(f'https://api.streamelements.com/kappa/v2/points/{channel}/{user}')
	point_amount = r.json()["points"]
	logger.info(f"{user} has {point_amount} points")
	return point_amount

################################################################################

with open('./channels.json', 'r+') as channels_file:
	global channels
	channels = json.load(channels_file)
	channels = channels['channels']

class Botto(commands.TwitchBot):
	def __init__(self):
		super().__init__(prefix=['!', '?'], irc_token=token, api_token=api_token, client_id=channel_id, nick='adure_bot', initial_channels=channels)

	#################
	# ON READY EVENT
	#################
	async def event_ready(self):
		logger.info("Ready!")

	###################
	# ON MESSAGE EVENT
	###################
	async def event_message(self, message):
		print(f"{message.author.name}: {message.content}")
		await self.process_commands(message)

	##################
	# RESTART COMMAND
	##################
	@commands.twitch_command(aliases=['restart'])
	async def restart_command(self, message):
		if message.message.tags['mod'] == 1 or any(message.author.name in s for s in channels):
			logger.info("Restarting...")
			await message.send("HeyGuys cya")
			restart_program()

	#######################
	# OPEN BETTING COMMAND
	#######################
	@commands.twitch_command(aliases=['open'])
	async def open_command(self, message):
		if message.message.tags['mod'] == 1 or any(message.author.name in s for s in channels):
			open_channel = message.channel.name
			betters_file_path = Path(f"./{open_channel}_betters.json")

			if betters_file_path.exists():
				with open(betters_file_path, 'w+') as betters_file:
					bettersDict = {
						'is_open': 1,
						'betters': []
					}
					betters_file.seek(0)
					json.dump(bettersDict, betters_file, separators=(',', ': '), indent=4)
					betters_file.truncate()
					logger.info(f"Cleared {open_channel}_betters.json file")

			else:
				with open(f"./{open_channel}_betters.json", 'w+') as new_betters_file:
					bettersDict = {
						'is_open': 1,
						'betters': []
					}
					json.dump(bettersDict, new_betters_file, separators=(',', ': '), indent=4)
					logger.info(f"Created {open_channel}_betters.json file")


			logger.info(f"Betting open - {message.channel.name}")
			await message.send("Betting open! Use '!bet <outcome> <wager>' to bet on the game (!howtobet)")

	####################
	# ENTER BET COMMAND
	####################
	@commands.twitch_command(aliases=['bet', 'guess'])
	async def bet_command(self, message, outcome, wager):
		bet_channel = message.channel.name
		with open(f'./{bet_channel}_betters.json') as betters_file:
			contents = json.load(betters_file)
			is_open = contents['is_open']

		# if the betting has been opened
		if is_open == 1:
			# if they entered an accepted outcome
			if outcome in ['win', 'loss', 'lose']:
				# if the wager is a number
				if wager.isdigit() == True:
					# if they have enough points to make the bet
					if check_points(bet_channel, message.author.name) >= int(wager):
						# open betters json file
						with open(f'./{bet_channel}_betters.json', 'r+') as betters_file:
							contents = json.load(betters_file)

							# if the betters list isnt empty
							if len(contents['betters']) >= 1:
								for user in contents['betters']:
									# if the user trying to bet has already entered
									if user['user'] == message.author.name:
										logger.error(f"{message.author.name} tried to bet, but they have already entered")
										await message.send(f"{message.author.name}, you can only bet once")
										break
									else:
										betDict = {
											'user': message.author.name,
											'outcome': outcome,
											'wager': wager
										}
										contents['betters'].append(betDict)

										betters_file.seek(0)
										json.dump(contents, betters_file, separators=(',', ': '), indent=4)
										betters_file.truncate()

										logger.info(f"Entered {message.author.name} betting {outcome} with a {wager} Point wager")
										await message.send(f"Entered {message.author.name} betting {outcome} with a {wager} Point wager")
							else:
								betDict = {
									'user': message.author.name,
									'outcome': outcome,
									'wager': wager
								}
								contents['betters'].append(betDict)

								betters_file.seek(0)
								json.dump(contents, betters_file, separators=(',', ': '), indent=4)
								betters_file.truncate()

								logger.info(f"Entered {message.author.name} betting {outcome} with a {wager} Point wager")
								await message.send(f"Entered {message.author.name} betting {outcome} with a {wager} Point wager")

					# user doesnt have enough points
					else:
						logger.error(f"{message.author.name} tried to enter with insufficient points")
						await message.send(f"{message.author.name}, you do not have enough points")
				# user tried to enter with non-digit wager
				else:
					logger.error(f"Bet attempt with non-digit wager by {message.author.name}")
					await message.send(f"{message.author.name}, your wager is not a number")
			# user tried to enter with non-accepted outcome
			else:
				logger.error(f"Bet attempt with non-accepted outcome by {message.author.name}")
				await message.send(f"{message.author.name}, please enter an accepted outcome ('win', 'loss', 'lose').")
		# user tried to bet while betting was closed
		else:
			logger.error(f"{message.author.name} tried to bet while betting is closed")
			await message.send(f"{message.author.name}, betting is closed")


# RUN IT
bot = Botto()
bot.run()