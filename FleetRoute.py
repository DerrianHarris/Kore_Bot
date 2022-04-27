from typing import Tuple, List

from Directions import Direction
from kaggle_environments.helpers import Point

RouteEntry = Tuple[int, Direction]
Route = List[RouteEntry]


class FleetRoute:
    def __init__(self, path: Route):
        self.path = path

    def to_flight_plan(self):
        flight_plan = ""
        for i in range(len(self.path)):
            entry = self.path[i]
            length = entry[0]
            if length <= 0:
                continue
            direction = entry[1]
            flight_string = f"{direction}{'' if length == 1 or i >= len(self.path) - 1 else length - 1}"
            flight_plan += flight_string
        return flight_plan

    def is_valid(self):
        return len(self.to_flight_plan()) > 0

    @staticmethod
    def to_point(from_point: Point, to_point: Point, board_size: int):
        abs_delta, dirs = FleetRoute.get_initial_path_info(from_point, to_point, board_size)
        return FleetRoute.crowbar(abs_delta.x, dirs[0], abs_delta.y, dirs[1])

    @staticmethod
    def to_point_rect(from_point: Point, to_point: Point,board_size: int):
        abs_delta, dirs = FleetRoute.get_initial_path_info(from_point, to_point, board_size)
        return FleetRoute.rectangle(abs_delta.x, dirs[0], abs_delta.y, dirs[1])

    @staticmethod
    def get_initial_path_info(from_point: Point, to_point: Point, board_size: int):
        delta = to_point - from_point
        abs_delta = delta.map(abs)
        mag_delta = Point(1 if to_point.x > from_point.x else -1, 1 if to_point.y > from_point.y else -1)
        dir_delta = Point(mag_delta.x if abs_delta.x < board_size * .5 else -mag_delta.x,
                          mag_delta.y if abs_delta.y < board_size * .5 else -mag_delta.y)
        dirs = (Direction.EAST if dir_delta.x == 1 else Direction.WEST, Direction.NORTH if dir_delta.y == 1 else Direction.SOUTH)
        return abs_delta, dirs



    # These return to the shipyard
    @staticmethod
    def line(length: int, direction: Direction):
        return FleetRoute([(length, direction)])

    @staticmethod
    def yo_yo(length: int, direction: Direction):
        return FleetRoute.crowbar(length, direction, 1,direction.get_opp_dir())

    @staticmethod
    def rectangle(length_one: int, direction_one: Direction, length_two: int, direction_two: Direction):
        return FleetRoute(
            [(length_one, direction_one), (length_two, direction_two), (length_one, direction_one.get_opp_dir()),
             (length_two, direction_two.get_opp_dir())])

    @staticmethod
    def square(length: int, direction_one: Direction, direction_two: Direction):
        return FleetRoute.rectangle(length, direction_one, length, direction_two)

    # These don't return to the shipyard
    @staticmethod
    def crowbar(length_one: int, direction_one: Direction, length_two: int,direction_two: Direction):
        return FleetRoute([(length_one, direction_one), (length_two, direction_two)])
