from discord.ext.commands import Cog, command


# TODO: Store this in Redis
LFCS = []

# TODO: On Redis timeout:
# Print whole lfc list to lfc channel (gotten from API)


class LookingForCrew(Cog):
    def _format_lfc_message(self, obj):
        header = "**Currently looking for crew:**"
        message = '\n'.join(
            "{username} looking for {number} {activity}".format(
                username=msg["username"],
                number=msg["number"],
                activity=msg["activity"],
            )
            for msg
            in obj
        ) or "No one looking for crew."
        return f">>> {header}\n{message}"

    @command()
    async def looking(self, ctx, number, *activity):
        """
        Temporary command for testing.
        """
        # Create lfc JSON object
        obj = {
            "username": ctx.message.author.name,
            "number": number,
            "activity": " ".join(activity),
        }
        # Put it in Redis
        LFCS.append(obj)
        # Print whole lfc list to lfc channel (gotten from API)
        await ctx.send(self._format_lfc_message(LFCS))

    @command()
    async def done(self, ctx, *args):
        """
        Temporary command for testing.
        """
        # Remove lfc object from Redis
        global LFCS
        LFCS = [
            lfc
            for lfc
            in LFCS
            if lfc["username"] != ctx.message.author.name
        ]
        # Print whole lfc list to lfc channel (gotten from API)
        await ctx.send(self._format_lfc_message(LFCS))


