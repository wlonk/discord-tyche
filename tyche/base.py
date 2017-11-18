from collections import namedtuple
from random import randint


Roll = namedtuple('Roll', ('number', 'sides', 'modifier'))


class Base:
    def parse(self, dice):
        raise NotImplementedError

    def render(self, results, context):
        raise NotImplementedError

    def do_roll(self, context):
        return [randint(1, context.sides) for _ in range(context.number)]

    def roll(self, dice):
        context = self.parse(dice)
        results = self.do_roll(context)
        return self.render(results, context)
