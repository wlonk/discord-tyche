import os
import asyncio

from random import choice

import discord
from discord.ext.commands import Bot

from .errors import ParseError
from .generic import Generic
from .wod import WoD
from .pbta import PbtA


if not discord.opus.is_loaded():
    # Default on OS X installed by brew install opus
    default = '/usr/local/Cellar/opus/1.2.1/lib/libopus.dylib'
    discord.opus.load_opus(os.environ.get('LIBOPUS', default))


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

NEGATIVES = [
    "I can't do that, Dave.",
    "Nah.",
    "Pffff. No.",
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



VOICE_CHANNELS = {}


@client.command(pass_context=True)
async def play(ctx, url):
    await client.say(choice(AFFIRMATIVES))
    channel = ctx.message.author.voice.voice_channel
    if channel:
        voice = await client.join_voice_channel(channel)
        player = await voice.create_ytdl_player(url)
        VOICE_CHANNELS[channel.id] = player
        player.volume = 0.1
        player.start()


@client.command(pass_context=True)
async def pause(ctx):
    channel = ctx.message.author.voice.voice_channel
    if channel:
        player = VOICE_CHANNELS.get(channel.id)
        if player:
            await client.say(choice(AFFIRMATIVES))
            player.pause()
        else:
            await client.say(choice(NEGATIVES))


@client.command(pass_context=True)
async def resume(ctx):
    await client.say(choice(AFFIRMATIVES))
    channel = ctx.message.author.voice.voice_channel
    if channel:
        player = VOICE_CHANNELS.get(channel.id)
        if player:
            await client.say(choice(AFFIRMATIVES))
            player.resume()
        else:
            await client.say(choice(NEGATIVES))


@client.command(pass_context=True)
async def stop(ctx):
    await client.say(choice(AFFIRMATIVES))
    channel = ctx.message.author.voice.voice_channel
    if channel:
        player = VOICE_CHANNELS.get(channel.id)
        if player:
            await client.say(choice(AFFIRMATIVES))
            player.stop()
        else:
            await client.say(choice(NEGATIVES))


@client.command(pass_context=True)
async def role(ctx, desired_role):
    role = is_acceptable(desired_role, ctx)
    if role:
        await client.say(choice(AFFIRMATIVES))
        await client.add_roles(ctx.message.author, role)
    else:
        await client.say(choice(NEGATIVES))


@client.command(pass_context=True)
async def unrole(ctx, desired_role):
    role = is_acceptable(desired_role, ctx)
    if role:
        await client.say(choice(AFFIRMATIVES))
        await client.remove_roles(ctx.message.author, role)
    else:
        await client.say(choice(NEGATIVES))


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
    try:
        client.run(os.environ['DISCORD_TOKEN'])
    except:
        asyncio.run(client.logout())
