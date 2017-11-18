import re

from .base import Base, Roll
from .errors import ParseError


class Generic(Base):
    DICE = re.compile(r'(\d+)?d(\d+)(?:\s*([+-])\s*(\d+))?')

    def parse(self, dice):
        groups = self.DICE.match(dice)
        if not groups:
            raise ParseError(f"Invalid dice: {dice}")
        try:
            number = int(groups.group(1) or 1)
            sides = int(groups.group(2))
            polarity = -1 if groups.group(3) == '-' else 1
            modifier = int(groups.group(4) or 0) * polarity
        except ValueError:
            raise ParseError(f"Invalid dice: {dice}")
        return Roll(number, sides, modifier)

    def render(self, results, context):
        str_results = ", ".join(str(x) for x in results)
        show_mod = ""
        if context.modifier:
            show_mod = f" [{context.modifier:+}] "
        total = sum(results) + context.modifier
        return f"{str_results}{show_mod} (total {total})"
