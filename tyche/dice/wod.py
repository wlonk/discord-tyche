import re
from random import randint
from collections import namedtuple

from ..base import Base
from ..errors import ParseError


Roll = namedtuple('Roll', ('number', 'sides', 'explode_at', 'is_rote'))


class WoD(Base):
    DICE = re.compile(r'(\d+)(?:e(\d+))?(r?)')

    def parse(self, dice):
        groups = self.DICE.match(dice)
        if not groups:
            raise ParseError(f"Invalid dice: {dice}")
        try:
            number = int(groups.group(1))
            sides = 10
            explode_at = int(groups.group(2) or 10)
            if not (7 <= explode_at < 11):
                raise ParseError(f"Invalid explode: {explode_at}")
            is_rote = bool(groups.group(3) or False)
        except ValueError:
            raise ParseError(f"Invalid dice: {dice}")
        return Roll(number, sides, explode_at, is_rote)

    def render(self, result, context):
        sorted_results = ", ".join(map(str, reversed(sorted(result))))
        successes = len([die for die in result if die >= 7])
        botches = len([die for die in result if die == 1])
        if botches and not successes:
            result_type = "Dramatic failure"
        elif not successes:
            result_type = "Failure"
        elif successes < 5:
            result_type = f"Success [{successes}]"
        else:
            result_type = f"Exceptional success [{successes}]"
        return f"{result_type}\n({sorted_results})"

    def do_roll(self, context):
        results = [randint(1, context.sides) for _ in range(context.number)]
        # Get explodables before rote, but actually explode after rote,
        # as rerolled dice from a rote aren't eligible for explosion:
        explodables = [
            die
            for die
            in results
            if die >= context.explode_at
        ]

        if context.is_rote:
            successes = [
                die
                for die
                in results
                if die >= 7
            ]
            rerolls = [
                randint(1, context.sides)
                for _
                in range(len(results) - len(successes))
            ]
            results = successes + rerolls

        while any(explodables):
            new_dice = [
                randint(1, context.sides)
                for _
                in range(len(explodables))
            ]
            explodables = [
                die
                for die
                in new_dice
                if die >= context.explode_at
            ]
            results += new_dice
        return results
