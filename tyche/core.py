import asyncio
import json
import os
from random import choice
# When we're 3.7:
# from contextlib import AsyncExitStack

import aiohttp
import discord
from discord.ext.commands import Bot

from .ytdl import create_ytdl_source
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
    "You betcha!",
    "But of course.",
]


NEGATIVES = [
    "I'm so, so sorry, but no.",
    "I can't do that, Dave.",
    "Nah.",
    "Pffff. No.",
    "It is with the greatest regret that I inform you I cannot.",
    "Nuh-uh.",
    "ope nope nope nope nope nope nope nope nope nope nope nop",
]


# TODO: replace with Redis brain?
VOICE_CHANNELS = {}


async def fetch(url, guild_id):
    headers = {
        "Authorization": f"Token {API_KEY}",
    }
    params = {
        "server_id": guild_id,
    }
    full_url = f"{API_ROOT}{url}/"
    # When we're 3.7:
    # async with AsyncExitStack() as stack:
    #     session = await stack.enter_async_context(aiohttp.ClientSession())
    #     response = await stack.enter_async_context(
    #         session.get(url, params={"guild_id": guild_id})
    #     )
    async with aiohttp.ClientSession() as session:
        async with session.get(full_url, headers=headers, params=params) as response:
            return await response.text()


async def get_prefix(bot, message):
    payload = await fetch("prefix", message.guild.id)
    return json.loads(payload)["prefix"]


async def is_acceptable(role_name, context):
    guild_acceptable_roles = await fetch("roles", context.message.guild.id)
    acceptable_roles = [
        r
        for r in context.message.guild.roles
        if r.name in guild_acceptable_roles
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
        f"Connected to {str(len(client.guilds))} guilds"
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


def _is_streaming(member):
    return any(isinstance(act, discord.Streaming) for act in member.activities)


@client.event
async def on_member_update(before, after):
    is_before_streaming = _is_streaming(before)
    is_after_streaming = _is_streaming(after)
    change_in_streaming = is_before_streaming != is_after_streaming

    if not change_in_streaming:
        return

    response = await fetch("streaming_role", after.guild.id)
    response = json.loads(response)
    streaming_role = response["streaming_role"]
    streaming_role_requires = response["streaming_role_requires"]
    if streaming_role:
        avilable_roles = {
            r.name: r
            for r
            in after.guild.roles
        }
        streaming_role = avilable_roles.get(streaming_role, None)
        if not streaming_role:
            # Bail early if role missing:
            return
        if not _is_streaming(after):
            await after.remove_roles(streaming_role)
        user_roles = [
            role.name
            for role
            in after.roles
        ]
        if streaming_role_requires and streaming_role_requires not in user_roles:
            return
        if _is_streaming(after):
            await after.add_roles(streaming_role)


@client.command()
async def play(ctx, url):
    """
    Play audio from the given YouTube URL in the current user's voice channel.
    """
    await ctx.send(choice(AFFIRMATIVES))
    channel = ctx.message.author.voice.channel
    if channel:
        voice = await channel.connect()
        source = await create_ytdl_source(voice, url)
        VOICE_CHANNELS[channel.id] = voice
        voice.volume = 0.1
        voice.play(source)


@client.command()
async def pause(ctx):
    """
    Pause playing audio in the current user's voice channel.
    """
    channel = ctx.message.author.voice.channel
    if channel:
        voice = VOICE_CHANNELS.get(channel.id)
        if voice:
            await ctx.send(choice(AFFIRMATIVES))
            voice.pause()
        else:
            await ctx.send(choice(NEGATIVES))


@client.command()
async def resume(ctx):
    """
    Resume playing audio in the current user's voice channel.
    """
    channel = ctx.message.author.voice.channel
    if channel:
        voice = VOICE_CHANNELS.get(channel.id)
        if voice:
            await ctx.send(choice(AFFIRMATIVES))
            voice.resume()
        else:
            await ctx.send(choice(NEGATIVES))


@client.command()
async def stop(ctx):
    """
    Stop playing audio in the current user's voice channel.
    """
    channel = ctx.message.author.voice.channel
    if channel:
        voice = VOICE_CHANNELS.get(channel.id)
        if voice:
            await ctx.send(choice(AFFIRMATIVES))
            voice.stop()
        else:
            await ctx.send(choice(NEGATIVES))


@client.command()
async def vol(ctx, volume):
    """
    Adjust Tyche's volume in the current user's voice channel. Valid values are between
    0.0 and 2.0, inclusive.
    """
    channel = ctx.message.author.voice.channel
    try:
        volume = float(volume)
    except ValueError:
        await ctx.send("That's not a number.")
        return
    if channel:
        voice = VOICE_CHANNELS.get(channel.id)
        if voice and 0.0 <= volume <= 2.0:
            await ctx.send(choice(AFFIRMATIVES))
            voice.volume = volume
        else:
            await ctx.send(choice(NEGATIVES))


@client.command()
async def leave(ctx):
    """
    Leave the current user's voice channel.
    """
    channel = ctx.message.author.voice.channel
    if channel:
        voice = VOICE_CHANNELS.get(channel.id)
        if voice:
            await voice.disconnect()
            VOICE_CHANNELS.pop(channel.id)


@client.command()
async def role(ctx, desired_role):
    """
    Add a cosmetic role to the current user.
    """
    role = await is_acceptable(desired_role, ctx)
    if role:
        await ctx.send(choice(AFFIRMATIVES))
        await ctx.message.author.add_roles(role)
    else:
        await ctx.send(choice(NEGATIVES))


@client.command()
async def unrole(ctx, desired_role):
    """
    Remove a cosmetic role from the current user.
    """
    role = await is_acceptable(desired_role, ctx)
    if role:
        await ctx.send(choice(AFFIRMATIVES))
        await ctx.message.author.remove_roles(role)
    else:
        await ctx.send(choice(NEGATIVES))


@client.command()
async def roll(ctx, *dice):
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
                await ctx.send(result)
                return
        except ParseError:
            pass


def run():
    client.run(os.environ["DISCORD_TOKEN"])
