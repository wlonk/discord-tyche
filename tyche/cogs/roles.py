from random import choice
from discord.ext.commands import Cog, command

from ..api import fetch
from ..constants import AFFIRMATIVES, NEGATIVES


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


class Roles(Cog):
    @command()
    async def list(self, ctx):
        """
        List all cosmetic roles on the current server.
        """
        guild_acceptable_roles = await fetch("roles", ctx.message.guild.id)
        acceptable_roles = ", ".join(sorted(
            f"`{r.name}`"
            for r in ctx.message.guild.roles
            if r.name in guild_acceptable_roles
        ))
        message = f"I can add or remove these roles from you: {acceptable_roles}"
        await ctx.send(message)

    @command()
    async def role(self, ctx, desired_role):
        """
        Add a cosmetic role to the current user.
        """
        role = await is_acceptable(desired_role, ctx)
        if role:
            await ctx.send(choice(AFFIRMATIVES))
            await ctx.message.author.add_roles(role)
        else:
            await ctx.send(choice(NEGATIVES))

    @command()
    async def unrole(self, ctx, desired_role):
        """
        Remove a cosmetic role from the current user.
        """
        role = await is_acceptable(desired_role, ctx)
        if role:
            await ctx.send(choice(AFFIRMATIVES))
            await ctx.message.author.remove_roles(role)
        else:
            await ctx.send(choice(NEGATIVES))
