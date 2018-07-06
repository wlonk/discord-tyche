import os

from random import choice

import discord
from discord.ext.commands import Bot

from .errors import ParseError
from .generic import Generic
from .wod import WoD
from .pbta import PbtA


BACKENDS = [
    Generic(),
    WoD(),
    PbtA(),
]


AFFIRMATIVES = [
    'Cool.',
    'On it.',
    'Sure thing.',
    'Aye aye.',
    "I'll try my best.",
    "UGH. Fine.",
    "Yessiree!"
]

# These should be configurable, not hard-coded:
ACCEPTABLE_ROLES = [
    'he/him',
    'she/her',
    'they/them',
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


def parse_message(message):
    return message.split(None, 1)[1]


def is_acceptable(role_name, context):
    acceptable_roles = [
        r
        for r
        in context.message.server.role_hierarchy
        if r.name in ACCEPTABLE_ROLES
    ]
    try:
        return next(r for r in acceptable_roles if r.name == role_name)
    except StopIteration:
        return None


@client.event
async def on_command(command, context):
    if command.name == 'role' or command.name == 'unrole':
        behavior = {
            'role': 'add_roles',
            'unrole': 'remove_roles',
        }[command.name]
        role_name = parse_message(context.message.clean_content)
        role = is_acceptable(role_name, context)
        if role:
            await getattr(client, behavior)(
                context.message.author,
                role,
            )


@client.command()
async def role(desired_role):
    await client.say(choice(AFFIRMATIVES))


@client.command()
async def unrole(desired_role):
    await client.say(choice(AFFIRMATIVES))


@client.command()
async def roll(*dice):
    """
    Roll dice.

    XdY(+/-Z)  generic dice roller
    X(eY)(r)   Chronicles of Darkness roller
    +/-X       Powered by the Apocalypse roller
    """
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
