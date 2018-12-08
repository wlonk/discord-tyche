import asyncio
import json
import os
from random import choice
# When we're 3.7:
# from contextlib import AsyncExitStack

import aiohttp
import discord
from discord.ext.commands import Bot

from .errors import ParseError
from .generic import Generic
from .pbta import PbtA
from .wod import WoD

if not discord.opus.is_loaded():
    # Default on OS X installed by brew install opus
    default = "/usr/local/Cellar/opus/1.2.1/lib/libopus.dylib"
    discord.opus.load_opus(os.environ.get("LIBOPUS", default))


API_ROOT = os.environ.get("API_ROOT", "http://localhost:8000/api/")
API_KEY = os.environ.get("API_KEY", "invalid key")


BACKENDS = [Generic(), WoD(), PbtA()]


AFFIRMATIVES = [
    "Cool.",
    "On it.",
    "Sure thing.",
    "Aye aye.",
    "I'll try my best.",
    "UGH. Fine.",
    "Yessiree!",
]


NEGATIVES = [
    "I'm so, so sorry, but no.",
    "I can't do that, Dave.",
    "Nah.",
    "Pffff. No.",
]


# TODO: replace with Redis brain?
VOICE_CHANNELS = {}


async def fetch(url, server_id):
    # async with AsyncExitStack() as stack:
    #     session = await stack.enter_async_context(aiohttp.ClientSession())
    #     response = await stack.enter_async_context(
    #         session.get(url, params={"server_id": server_id})
    #     )
    headers = {
        "Authorization": f"Token {API_KEY}",
    }
    params = {
        "server_id": server_id,
    }
    full_url = f"{API_ROOT}{url}/"
    async with aiohttp.ClientSession() as session:
        async with session.get(full_url, headers=headers, params=params) as response:
            return await response.text()


async def get_prefix(bot, message):
    payload = await fetch("prefix", message.server.id)
    return json.loads(payload)["prefix"]


async def is_acceptable(role_name, context):
    server_acceptable_roles = await fetch("roles", context.message.server.id)
    acceptable_roles = [
        r
        for r in context.message.server.role_hierarchy
        if r.name in server_acceptable_roles
    ]
    try:
        return next(r for r in acceptable_roles if r.name == role_name)
    except StopIteration:
        return None


# Ready Bot One!

client = Bot(
    description="Tyche, the diceroller", command_prefix=get_prefix, pm_help=True
)


@client.event
async def on_ready():
    print(
        f"Logged in as {client.user.name} (ID:{client.user.id}) | "
        f"Connected to {str(len(client.servers))} servers"
    )
    print(f"Communicating with {API_ROOT}")
    print("--------")
    print(f"Current Discord.py Version: {discord.__version__}")
    print("--------")
    print(f"Use this link to invite {client.user.name}:")
    print(
        f"https://discordapp.com/oauth2/authorize"
        f"?client_id={client.user.id}&scope=bot&permissions=8"
    )


@client.event
async def on_member_update(before, after):
    before_stream = before.game and before.game.type == 1
    after_stream = after.game and after.game.type == 1
    change_in_streaming = before_stream != after_stream
    if not change_in_streaming:
        return

    response = await fetch("streaming_role", after.server.id)
    response = json.loads(response)
    streaming_role = response["streaming_role"]
    streaming_role_requires = response["streaming_role_requires"]
    if streaming_role:
        avilable_roles = {
            r.name: r
            for r
            in after.server.role_hierarchy
        }
        streaming_role = avilable_roles.get(streaming_role, None)
        if not streaming_role:
            # Bail early if role missing:
            return
        if (after.game and after.game.type != 1) or after.game is None:
            await client.remove_roles(after, streaming_role)
        user_roles = [
            role.name
            for role
            in after.roles
        ]
        if streaming_role_requires and streaming_role_requires not in user_roles:
            return
        if after.game and after.game.type == 1:
            await client.add_roles(after, streaming_role)


@client.command(pass_context=True)
async def play(ctx, url):
    """
    Play audio from the given YouTube URL in the current user's voice channel.
    """
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
    """
    Pause playing audio in the current user's voice channel.
    """
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
    """
    Resume playing audio in the current user's voice channel.
    """
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
    """
    Stop playing audio in the current user's voice channel.
    """
    channel = ctx.message.author.voice.voice_channel
    if channel:
        player = VOICE_CHANNELS.get(channel.id)
        if player:
            await client.say(choice(AFFIRMATIVES))
            player.stop()
        else:
            await client.say(choice(NEGATIVES))


@client.command(pass_context=True)
async def vol(ctx, volume):
    """
    Adjust Tyche's volume in the current user's voice channel. Valid values are between
    0.0 and 2.0, inclusive.
    """
    channel = ctx.message.author.voice.voice_channel
    try:
        volume = float(volume)
    except ValueError:
        await client.say("That's not a number.")
        return
    if channel:
        player = VOICE_CHANNELS.get(channel.id)
        if player and 0.0 <= volume <= 2.0:
            await client.say(choice(AFFIRMATIVES))
            player.volume = volume
        else:
            await client.say(choice(NEGATIVES))


@client.command(pass_context=True)
async def leave(ctx):
    """
    Leave the current user's voice channel.
    """
    channel = ctx.message.author.voice.voice_channel
    if channel:
        player = VOICE_CHANNELS.get(channel.id)
        if player:
            await client.voice.disconnect()
            VOICE_CHANNELS.pop(channel.id)


@client.command(pass_context=True)
async def role(ctx, desired_role):
    """
    Add a cosmetic role to the current user.
    """
    role = await is_acceptable(desired_role, ctx)
    if role:
        await client.say(choice(AFFIRMATIVES))
        await client.add_roles(ctx.message.author, role)
    else:
        await client.say(choice(NEGATIVES))


@client.command(pass_context=True)
async def unrole(ctx, desired_role):
    """
    Remove a cosmetic role from the current user.
    """
    role = await is_acceptable(desired_role, ctx)
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
    result = ""
    for backend in BACKENDS:
        try:
            result = backend.roll(" ".join(dice))
            if result:
                await client.say(result)
                return
        except ParseError:
            pass


def run():
    client.run(os.environ["DISCORD_TOKEN"])
