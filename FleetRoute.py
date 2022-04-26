from Directions import Direction
from kaggle_environments.helpers import Point

RouteEntry = tuple[int, Direction]
Route = list[RouteEntry]


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
    def to_point(from_point: Point, to_point: Point):
        diff = to_point - from_point
        y_dir = Direction.NORTH if diff.y > 0 else Direction.SOUTH
        x_dir = Direction.EAST if diff.x > 0 else Direction.WEST
        diff = diff.map(abs)
        return FleetRoute.crowbar(diff.x, x_dir, diff.y, y_dir)

    @staticmethod
    def to_point_rect(from_point: Point, to_point: Point):
        diff = to_point - from_point
        y_dir = Direction.NORTH if diff.y > 0 else Direction.SOUTH
        x_dir = Direction.EAST if diff.x > 0 else Direction.WEST
        diff = diff.map(abs)
        return FleetRoute.rectangle(diff.x, x_dir, diff.y, y_dir)

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
