# from typing import Tuple, List
import math
import re
from enum import Enum, auto
from os import error

from Directions import Direction
from kaggle_environments.helpers import Point


# RouteEntry = Tuple[int, Direction]
# Route = List[RouteEntry]

class FleetRouteType(Enum):
    RECTANGLE = auto()
    CROWBAR = auto()


class FleetRoute:
    def __init__(self, path):
        self.path = path

    def to_flight_plan(self):
        flight_plan = ""
        dist_traveled = 0
        for i in range(len(self.path)):
            entry = self.path[i]
            length, direction = entry
            if length <= 0:
                continue
            flight_string = f"{direction}{'' if length == 1 or i >= len(self.path) - 1 else length - 1}"
            flight_plan += flight_string
            dist_traveled += length
        return flight_plan, dist_traveled - 1

    def is_valid(self, curr_turn: int, max_turn: int):
        flight_plan_str, dist_traveled = self.to_flight_plan()
        return len(flight_plan_str) > 0 and dist_traveled + curr_turn < max_turn

    @staticmethod
    def from_flight_plan(flight_plan: str):
        split_flight_plan = re.findall(r'[NSWE]\d+|[NSEW]', flight_plan)
        fleet_route = []
        for entry in split_flight_plan:
            dir = entry[0]
            length = 1
            if len(entry) > 1:
                length += int(entry[1:])
            fleet_route.append((length, Direction.from_char(dir)))
        return fleet_route

    @staticmethod
    def get_future_pos_from_flight_plan(position: Point, flight_plan: str, board_size: int,
                                        starting_dir: Direction = None, max_look_ahead: int = math.inf) -> Point:
        if starting_dir:
            flight_plan = starting_dir.to_char() + flight_plan
        fleet_route = FleetRoute.from_flight_plan(flight_plan)
        dx = 0
        dy = 0
        turns = min(len(fleet_route), max_look_ahead)
        for index in range(turns):
            length, direction = fleet_route[index]
            if direction == Direction.NORTH:
                dy += length
            if direction == Direction.SOUTH:
                dy -= length
            if direction == Direction.WEST:
                dx -= length
            if direction == Direction.EAST:
                dx += length
        return position.translate(Point(dx, dy), board_size)

    @staticmethod
    def to_pos(from_point: Point, to_point: Point, board_size: int, fleet_route_type: FleetRouteType):
        if fleet_route_type == FleetRouteType.RECTANGLE:
            return FleetRoute.to_point_rect(from_point, to_point, board_size)
        elif fleet_route_type == FleetRouteType.CROWBAR:
            return FleetRoute.to_point_crowbar(from_point, to_point, board_size)
        else:
            raise error("Fleet route type does not exist!")

    @staticmethod
    def to_point_crowbar(from_point: Point, to_point: Point, board_size: int):
        abs_delta, dirs = FleetRoute.get_initial_path_info(from_point, to_point, board_size)
        return FleetRoute.crowbar(abs_delta.x, dirs[0], abs_delta.y, dirs[1])

    @staticmethod
    def to_point_rect(from_point: Point, to_point: Point, board_size: int):
        abs_delta, dirs = FleetRoute.get_initial_path_info(from_point, to_point, board_size)
        return FleetRoute.rectangle(abs_delta.x, dirs[0], abs_delta.y, dirs[1])

    @staticmethod
    def get_initial_path_info(from_point: Point, to_point: Point, board_size: int):
        delta = to_point - from_point
        abs_delta = delta.map(abs)
        mag_delta = Point(1 if to_point.x > from_point.x else -1, 1 if to_point.y > from_point.y else -1)

        mag_ck_x = abs_delta.x < board_size * .5
        mag_ck_y = abs_delta.y < board_size * .5

        dir_delta = Point(mag_delta.x if mag_ck_x else -mag_delta.x,
                          mag_delta.y if mag_ck_y else -mag_delta.y)
        dirs = (Direction.EAST if dir_delta.x == 1 else Direction.WEST,
                Direction.NORTH if dir_delta.y == 1 else Direction.SOUTH)

        abs_delta = Point(abs_delta.x if mag_ck_x else board_size - abs_delta.x,
                          abs_delta.y if mag_ck_y else board_size - abs_delta.y)
        return abs_delta, dirs

    @staticmethod
    def get_distance_to_pos(from_point: Point, to_point: Point, board_size: int) -> int:
        abs_delta, _ = FleetRoute.get_initial_path_info(from_point, to_point, board_size)
        return abs_delta.x + abs_delta.y

    # These return to the shipyard
    @staticmethod
    def line(length: int, direction: Direction):
        return FleetRoute([(length, direction)])

    @staticmethod
    def yo_yo(length: int, direction: Direction):
        return FleetRoute.crowbar(length, direction, 1, direction.get_opp_dir())

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
    def crowbar(length_one: int, direction_one: Direction, length_two: int, direction_two: Direction):
        return FleetRoute([(length_one, direction_one), (length_two, direction_two)])
