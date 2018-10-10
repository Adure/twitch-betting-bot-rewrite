from twitchio.ext import commands
import requests
import sys
import os
import random
import re
import json
import logging
import strawpoll
from auth import jwt_token, access_token, token, api_token

jwt_token = jwt_token

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

with open('./channels.json', 'r+') as channels_file:
	global channels
	channels = json.load(channels_file)
	channels = channels['channels']

class Botto(commands.TwitchBot):
	def __init__(self):
		super().__init__(prefix=['!', '?'], irc_token=token, api_token=api_token, client_id=channel_id, nick='adure_bot', initial_channels=channels)

	async def event_ready(self):
		logger.info("Ready!")

	async def event_message(self, message):
		print(f"{message.author.name}: {message.content}")
		await self.process_commands(message)

	@commands.twitch_command(aliases=['open'])
	async def open_command(self, message):
		if message.message.tags['mod'] == 1 or any(message.author.name in s for s in channels):
			with open('./channels.json') as channels_file:
				contents = json.load(channels_file)
				is_open = contents[message.channel.name]['is_open']
				print(is_open)

			logger.info(f"Betting open - {message.channel.name}")
			await message.send("Betting open! Use '!bet <outcome> <wager>' to bet on the game (!howtobet)")

	@commands.twitch_command(aliases=['bet', 'guess'])
	async def bet_command(self, message, outcome, wager):
		channel = message.channel.name
		with open(f'./{channel}_betters.json') as betters_file:
			contents = json.load(betters_file)
			is_open = contents['is_open']

		if is_open == 1:
			if outcome in ['win', 'loss', 'lose']:
				if wager.isdigit() == True:
					print("success!")
				else:
					await message.send(f"Error - {message.author.name}, your wager is not a number")
					logger.error(f"Bet attempt with non-digit wager by {message.author.name}")
			else:
				await message.send(f"Error - {message.author.name}, please enter an accepted outcome ('win', 'loss', 'lose').")
				logger.error(f"Bet attempt with non-accepted outcome by {message.author.name}")


bot = Botto()
bot.run()