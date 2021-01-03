import asyncio
from collections import defaultdict
from pathlib import Path
from discord import Embed, Colour, utils
from discord.ext.commands import Cog, command
from emoji import emojize
from yaml import safe_load

from ..models import EmojiMessage


e = lambda s: emojize(s, use_aliases=True)

MESSAGE_CACHE = {}


class Admin(Cog):
    def __init__(self, client):
        self.client = client

    def _is_admin(self, member, channel):
        return member.permissions_in(channel).administrator

    def relevant_emoji_change(self, message_id, emoji, user_id, emoji_map) -> bool:
        right_message = message_id in self.messages.keys()
        right_emoji = str(emoji) in emoji_map.keys()
        not_myself = user_id != self.client.user.id
        return right_message and right_emoji and not_myself

    @command(hidden=True)
    async def clear(self, ctx):
        if self._is_admin(ctx.author, ctx.channel):
            async for message in ctx.channel.history(oldest_first=False):
                if not message.pinned:
                    await message.delete()
                    await asyncio.sleep(2)

    async def initialize_message_store(self):
        # {
        #   [message.id]: {
        #     [emoji]: [role]
        #   }
        # }
        self.messages = defaultdict(dict)
        async for message in EmojiMessage.all():
            self.messages[message.message_id][message.emoji] = message.role

        await self.set_all_add_remove_events()

    async def update_message_store(self):
        await EmojiMessage.all().delete()
        for message_id, emoji_map in self.messages.items():
            for emoji, role in emoji_map.items():
                await EmojiMessage.create(message_id=message_id, emoji=emoji, role=role)

    async def set_all_add_remove_events(self):
        for message_id, emoji_map in self.messages.items():
            self.set_add_remove_events(emoji_map)
            print(f"Added emoji reaction events for {message_id}")

    @command(hidden=True)
    async def rules(self, ctx):
        rules = (Path(__file__).parent / "../../transneptune-rules.yml").resolve()
        with rules.open() as f:
            parsed_message = safe_load(f.read()[len("rules\n"):])

        if not parsed_message:
            print(f"No rules at {rules}!")
            return
        guild = utils.find(
            lambda x: parsed_message.get("guild", None) == x.id,
            self.client.guilds
        )
        if not guild:
            return
        channel = utils.find(
            lambda x: parsed_message.get("channel", None) == x.name,
            guild.text_channels,
        )
        if not channel:
            return
        title = parsed_message["title"]
        description = parsed_message["description"]
        color = Colour.from_rgb(*parsed_message["color"]).value
        emoji_map = {
            e(f":{k}:"): v
            for k, v
            in parsed_message["emoji_map"].items()
        }

        embed = Embed.from_dict({
            "color": color,
            "title": title,
            "description": description,
        })
        message = await channel.send(content=None, embed=embed)
        self.messages[message.id] = emoji_map
        await self.update_message_store()
        for key in emoji_map.keys():
            await message.add_reaction(key)

        self.set_add_remove_events(emoji_map)

    def set_add_remove_events(self, emoji_map):
        @self.client.event
        async def on_raw_reaction_add(payload):
            guild = self.client.get_guild(payload.guild_id)
            if not guild:
                print("Missing guild")
                return
            user = await guild.fetch_member(payload.user_id)
            if not user:
                print("Missing user")
                return

            message_id = payload.message_id
            emoji = payload.emoji.name
            if self.relevant_emoji_change(message_id, emoji, user.id, emoji_map):
                await self._add_user_role(
                    guild,
                    emoji_map[emoji],
                    user,
                )

        @self.client.event
        async def on_raw_reaction_remove(payload):
            guild = self.client.get_guild(payload.guild_id)
            if not guild:
                print("Missing guild")
                return
            user = await guild.fetch_member(payload.user_id)
            if not user:
                print("Missing user")
                return

            message_id = payload.message_id
            emoji = payload.emoji.name
            if self.relevant_emoji_change(message_id, emoji, user.id, emoji_map):
                await self._remove_user_role(
                    guild,
                    emoji_map[emoji],
                    user,
                )

    async def _add_user_role(self, guild, role_name, user):
        role = utils.find(
            lambda r: r.name == role_name,
            getattr(guild, "roles", []),
        )
        role and await user.add_roles(role)

    async def _remove_user_role(self, guild, role_name, user):
        role = utils.find(
            lambda r: r.name == role_name,
            getattr(guild, "roles", []),
        )
        role and await user.remove_roles(role)
