import json
import os

import discord
from discord.ext.commands import Bot, Cog, command

from .api import fetch, get_prefix, API_ROOT
from .models import init as db_init
from .cogs.music import Music
from .cogs.roles import Roles
from .cogs.rolls import Rolls
from .cogs.lfc import LookingForCrew
from .cogs.admin import Admin

if not discord.opus.is_loaded():
    # Default on OS X installed by brew install opus
    default = "/usr/local/Cellar/opus/1.2.1/lib/libopus.dylib"
    discord.opus.load_opus(os.environ.get("LIBOPUS", default))


# Ready Bot One!

client = Bot(description="Tyche, the diceroller", command_prefix=get_prefix)

# Set up cogs:
client.add_cog(Music())
client.add_cog(Roles())
client.add_cog(Rolls())
client.add_cog(LookingForCrew())
admin_cog = Admin(client)
client.add_cog(admin_cog)


@client.event
async def on_ready():
    await db_init()
    await admin_cog.initialize_message_store()
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
    """
    This does a few things:
        1. Detects if there's a change in streaming status. If not, it
           bails.
        2. Detects if the server has a streaming role configured. If
           not, it bails.
        3. If the user has begun streaming, it applies the streaming
           role to them (only if they have the prerequisite role, if any
           such is configured).
        4. If the user has ceased streaming, it removes the streaming
           role from them.
    """
    is_before_streaming = _is_streaming(before)
    is_after_streaming = _is_streaming(after)
    change_in_streaming = is_before_streaming != is_after_streaming

    if not change_in_streaming:
        return

    response = await fetch("streaming_role", after.guild.id)
    response = json.loads(response)
    streaming_role_name = response["streaming_role"]
    streaming_role_requires = response["streaming_role_requires"]
    if streaming_role_name:
        avilable_roles = {
            r.name: r
            for r
            in after.guild.roles
        }
        streaming_role = avilable_roles.get(streaming_role_name, None)
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
async def ping(ctx):
    """
    Respond with pong.
    """
    await ctx.send("pong")


def run():
    client.run(os.environ["DISCORD_TOKEN"])
