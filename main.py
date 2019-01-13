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

def add_points(channel, user, amount):
	with open('./channels.json') as channels_file:
		content = json.load(channels_file)
		token = content[channel]['token']
		channel = content[channel]['id']
	r = requests.put(f'https://api.streamelements.com/kappa/v2/points/{channel}/{user}/{amount}',
	headers = {"Authorization":token},
	)
	logger.info(r.text)

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
		await self.handle_commands(message)

	###################
	# ON COMMAND ERROR
	###################
	async def event_command_error(self, ctx, error):
		if isinstance(error, commands.TwitchCommandNotFound):
			pass
		else:
			logger.error(f"{error} - {ctx.channel.name}")

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

	########################
	# CLOSE BETTING COMMAND
	########################
	@commands.twitch_command(aliases=['close'])
	async def close_command(self, message):
		if message.message.tags['mod'] == 1 or any(message.author.name in s for s in channels):
			close_channel = message.channel.name
			win_votes = 0
			loss_votes = 0
			total_wager = 0

			with open(f'./{close_channel}_betters.json', 'r+') as betters_file:
				contents = json.load(betters_file)

				contents['is_open'] = 0
				betters_file.seek(0)
				json.dump(contents, betters_file, separators=(',', ': '), indent=4)
				betters_file.truncate()

				logger.info(f"Betting closed - {message.channel.name}")
				await message.send("Betting closed!")

			if len(contents['betters']) != 0:
				for user in contents['betters']:
					if user['outcome'] == 'win':
						win_votes += 1
					else:
						loss_votes += 1

					total_wager += int(user['wager'])

				w_percentage = (win_votes / len(contents['betters'])) * 100
				l_percentage = (loss_votes / len(contents['betters'])) * 100

				logger.info(f"{total_wager} Points bet | {win_votes}({w_percentage:.1f}%) voted win | {loss_votes}({l_percentage:.1f}%) voted lose")
				await message.send(f"{total_wager} Points bet | {win_votes}({w_percentage:.1f}%) voted win | {loss_votes}({l_percentage:.1f}%) voted lose")


	####################
	# ENTER BET COMMAND
	####################
	@commands.twitch_command(aliases=['bet', 'guess'])
	async def bet_command(self, message, outcome, wager):
		bet_channel = message.channel.name
		users = []
		with open(f'./{bet_channel}_betters.json', 'r+') as betters_file:
			contents = json.load(betters_file)
			is_open = contents['is_open']

			if is_open == 0:
				logger.error(f"{message.author.name} tried to bet while betting is closed")
				await message.send(f"{message.author.name}, betting is closed")
				return

			if outcome not in ['win', 'loss', 'lose']:
				logger.error(f"Bet attempt with non-accepted outcome by {message.author.name}")
				await message.send(f"{message.author.name}, please enter an accepted outcome ('win', 'loss', 'lose').")
				return

			if wager == 'all':
				wager = str(check_points(bet_channel, message.author.name))

			if wager.isdigit() == False:
				logger.error(f"Bet attempt with non-digit wager by {message.author.name}")
				await message.send(f"{message.author.name}, your wager is not a number")
				return

			if check_points(bet_channel, message.author.name) < int(wager):
				logger.error(f"{message.author.name} tried to enter with insufficient points")
				await message.send(f"{message.author.name}, you do not have enough points")
				return

			if len(contents['betters']) != 0:
				for user in contents['betters']:
					users.append(user['user'])

				if message.author.name in users:
					logger.error(f"{message.author.name} tried to bet, but they have already entered")
					await message.send(f"{message.author.name}, you can only bet once")
					return

			betDict = {
				'user': message.author.name,
				'outcome': outcome,
				'wager': wager
			}
			contents['betters'].append(betDict)
			add_points(bet_channel, message.author.name, int(wager) * -1)

			betters_file.seek(0)
			json.dump(contents, betters_file, separators=(',', ': '), indent=4)
			betters_file.truncate()

			logger.info(f"Entered {message.author.name} betting {outcome} with a {wager} Point wager")
			await message.send(f"Entered {message.author.name} betting {outcome} with a {wager} Point wager")

	@commands.twitch_command(aliases=['win'])
	async def win_command(self, message):
		if message.message.tags['mod'] == 1 or any(message.author.name in s for s in channels):
			channel = message.channel.name
			win_bets = 0
			points_won = 0
			points_lost = 0
			with open(f"{channel}_betters.json") as betters_file:
				contents = json.load(betters_file)

				is_open = contents['is_open']

				if is_open == 0:
					logger.info(f"Game won - {channel}")
					await message.send("Win! PogChamp")

					if len(contents['betters']) != 0:
						for user in contents['betters']:
							if user['outcome'] == 'win':
								win_bets += 1
								add_points(channel, user['user'], int(user['wager']))
								points_won += int(user['wager'])
							else:
								add_points(channel, user['user'], int(user['wager']) * -1)
								points_lost += int(user['wager'])

						percentage = (win_bets / len(contents['betters'])) * 100

						logger.info(str("%.2f" % percentage)+f"% of people got it right. {str(points_won)} Points won. {str(points_lost)} Points lost.")
						await message.send(str("%.2f" % percentage)+f"% of people got it right. {str(points_won)} Points won. {str(points_lost)} Points lost.")

					else:
						logger.info(f"No one has bet - {channel}")
						await message.send("No one has bet!")
				else:
					logger.info(f"Betting is still open - {channel}")
					await message.send("Betting is still open!")

	@commands.twitch_command(aliases=['loss', 'lose'])
	async def loss_command(self, message):
		if message.message.tags['mod'] == 1 or any(message.author.name in s for s in channels):
			channel = message.channel.name
			loss_bets = 0
			points_won = 0
			points_lost = 0
			with open(f"{channel}_betters.json") as betters_file:
				contents = json.load(betters_file)

				is_open = contents['is_open']

				if is_open == 0:
					logger.info(f"Game lost - {channel}")
					await message.send("Loss! BibleThump")

					if len(contents['betters']) != 0:
						for user in contents['betters']:
							if user['outcome'] == 'win':
								add_points(channel, user['user'], int(user['wager']) * -1)
								points_lost += int(user['wager'])
							else:
								loss_bets += 1
								add_points(channel, user['user'], int(user['wager']))
								points_won += int(user['wager'])

						percentage = (loss_bets / len(contents['betters'])) * 100

						logger.info(str("%.2f" % percentage)+f"% of people got it right. {str(points_won)} Points won. {str(points_lost)} Points lost.")
						await message.send(str("%.2f" % percentage)+f"% of people got it right. {str(points_won)} Points won. {str(points_lost)} Points lost.")

					else:
						logger.info(f"No one has bet - {channel}")
						await message.send("No one has bet!")
				else:
					logger.info(f"Betting is still open - {channel}")
					await message.send("Betting is still open!")

	@commands.twitch_command(aliases=['status'])
	async def status_command(self, message):
		if message.message.tags['mod'] == 1 or any(message.author.name in s for s in channels):
			channel = message.channel.name
			with open(f"{channel}_betters.json") as betters_file:
				contents = json.load(betters_file)
				is_open = contents['is_open']

				if is_open == 0:
					logger.info(f"Betting is closed. {str(len(contents['betters']))} betters in list. - {channel}")
					await message.send(f"Betting is closed. {str(len(contents['betters']))} betters in list.")
				else:
					logger.info(f"Betting is open. {str(len(contents['betters']))} betters in list. - {channel}")
					await message.send(f"Betting is open. {str(len(contents['betters']))} betters in list.")


	@commands.twitch_command(aliases=['strawpoll'])
	async def strawpoll_command(self, message, question, *options):
		if message.message.tags['mod'] == 1 or any(message.author.name in s for s in channels):
			api = strawpoll.API()
			topoll = strawpoll.Poll(question, list(options), multi=False)
			return_poll = await api.submit_poll(poll=topoll)
			logger.info(f"Created poll: {return_poll.url} - {message.channel.name}")
			await message.send(return_poll.url)

	@commands.twitch_command(aliases=['print'])
	async def print_command(self, message):
		channel = message.channel.name
		form_message = "Betters: "
		with open(f"{channel}_betters.json") as betters_file:
			contents = json.load(betters_file)
			if len(contents['betters']) == 0:
				await message.send("No betters in list!")
				logger.warning("No betters in list on print command")
				return
			for user in contents['betters']:
				form_message += f"'{user['user']}: {user['outcome']} {user['wager']}', "

			await message.send(form_message)
			logger.info(f"Sent print command to {channel} as {form_message}")


# RUN IT
bot = Botto()
bot.run()