import os

import discord
from discord.ext.commands import Bot

from .errors import ParseError
from .generic import Generic
from .wod import WoD


BACKENDS = [
    Generic(),
    WoD(),
]


client = Bot(
    description="Tyche, the diceroller",
    command_prefix="?",
    pm_help=True,
)


@client.event
async def on_ready():
    print(
        f'Logged in as {client.user.name} (ID:{client.user.id}) | '
        f'Connected to {str(len(client.servers))} servers'
    )
    print('--------')
    print(f'Current Discord.py Version: {discord.__version__}')
    print('--------')
    print(f'Use this link to invite {client.user.name}:')
    print(
        f'https://discordapp.com/oauth2/authorize'
        f'?client_id={client.user.id}&scope=bot&permissions=8'
    )


@client.command()
async def roll(*dice):
    result = ''
    for backend in BACKENDS:
        try:
            result = backend.roll(' '.join(dice))
            if result:
                await client.say(result)
                return
        except ParseError:
            pass


def run():
    client.run(os.environ['DISCORD_TOKEN'])
