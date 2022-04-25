from enum import Enum, auto
import random


class Direction(Enum):
    NORTH = auto()
    SOUTH = auto()
    EAST = auto()
    WEST = auto()

    def __str__(self):
        return self.name[0]

    @staticmethod
    def get_rand_dir():
        return random.choice(Direction.get_all())

    @staticmethod
    def get_all():
        return [Direction.NORTH, Direction.SOUTH, Direction.WEST, Direction.EAST]

    def get_opp_dir(self):
        if self == Direction.NORTH:
            return Direction.SOUTH
        elif self == Direction.SOUTH:
            return Direction.NORTH
        elif self == Direction.EAST:
            return Direction.WEST
        elif self == Direction.WEST:
            return Direction.EAST

    def get_perp_dir(self):
        if self in [Direction.NORTH, Direction.SOUTH]:
            return [Direction.WEST, Direction.EAST]
        elif self in [Direction.WEST, Direction.EAST]:
            return [Direction.NORTH, Direction.SOUTH]

    def is_opp_dir(self, other):
        return other == self.get_opp_dir()

    def is_perp_dir(self, other):
        return other in self.get_perp_dir()

    def turn_left(self):
        if self == Direction.NORTH:
            return Direction.WEST
        elif self == Direction.SOUTH:
            return Direction.EAST
        elif self == Direction.EAST:
            return Direction.NORTH
        elif self == Direction.WEST:
            return Direction.SOUTH

    def turn_right(self):
        if self == Direction.NORTH:
            return Direction.EAST
        elif self == Direction.SOUTH:
            return Direction.WEST
        elif self == Direction.EAST:
            return Direction.SOUTH
        elif self == Direction.WEST:
            return Direction.NORTH

    def to_char(self):
        return str(self)
