from discord.ext.commands import Cog, command


from ..errors import ParseError
from ..dice.generic import Generic
from ..dice.pbta import PbtA
from ..dice.wod import WoD

BACKENDS = [Generic(), WoD(), PbtA()]


class Rolls(Cog):
    @command()
    async def roll(self, ctx, *dice):
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

