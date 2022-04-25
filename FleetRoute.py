from Directions import Direction

RouteEntry = tuple[int, Direction]
Route = list[RouteEntry]


class FleetRoute:
    def __init__(self, path: Route):
        self.path = path

    def to_flight_plan(self):
        flight_plan = ""
        for entry in self.path:
            length = entry[0]
            direction = entry[1]
            flight_string = f"{direction}{str(length) if length > 1 else ''}"
            flight_plan += flight_string
        return flight_plan

    # These return to the shipyard
    @staticmethod
    def line(length: int, direction: Direction):
        return FleetRoute([(length, direction)])

    @staticmethod
    def yo_yo(length: int, direction: Direction):
        return FleetRoute.l_shape(length, direction, direction.get_opp_dir())

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
    def l_shape(length: int, direction_one: Direction, direction_two: Direction):
        return FleetRoute([(length, direction_one), (1, direction_two)])
