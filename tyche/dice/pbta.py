import re

from ..base import Base, Roll
from ..errors import ParseError


class PbtA(Base):
    DICE = re.compile(r'([+-])(\d+)')

    def parse(self, dice):
        groups = self.DICE.match(dice)
        if not groups:
            raise ParseError(f"Invalid dice: {dice}")
        try:
            number = 2
            polarity = -1 if groups.group(1) == '-' else 1
            modifier = int(groups.group(2)) * polarity
            sides = 6
        except ValueError:
            raise ParseError(f"Invalid dice: {dice}")
        return Roll(number, sides, modifier)

    def render(self, result, context):
        result = sum(result) + context.modifier
        if result < 7:
            return f"Miss [{result}]"
        if 7 <= result < 10:
            return f"Weak hit [{result}]"
        if 10 <= result < 12:
            return f"Strong hit [{result}]"
        return f"Exceptional hit [{result}]"
