import os
import re
from random import randint

import discord
from discord.ext.commands import Bot


BASIC_DICE = re.compile(r'(\d+)?d(\d+)(?:\s*([+-])\s*(\d+))?')


def parse(diceable):
    groups = BASIC_DICE.match(diceable)
    if not groups:
        return 0, 0, 0
    try:
        number = int(groups.group(1) or 1)
        sides = int(groups.group(2))
        polarity = -1 if groups.group(3) == '-' else 1
        print(groups.group(3))
        modifier = int(groups.group(4) or 0) * polarity
    except ValueError:
        return 0, 0, 0
    return number, sides, modifier


client = Bot(
    description="Tyche, the diceroller",
    command_prefix="!",
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
async def roll(*args):
    """
    !roll XdY(+/-Z)

    Rolll X dice of size Y, showing each die, and the total plus or minus Z.
    """
    number, sides, modifier = parse(' '.join(args))
    results = [randint(1, sides) for _ in range(number)]
    str_results = ', '.join(str(x) for x in results)
    total = sum(results) + modifier
    report = f"{str_results} (total {total})"
    await client.say(report)

if __name__ == '__main__':
    client.run(os.environ['DISCORD_TOKEN'])
