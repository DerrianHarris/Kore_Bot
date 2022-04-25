from Directions import Direction


# These return to the shipyard
def line(length: int, direction: Direction):
    return [(length, direction)]


def yo_yo(length: int, direction: Direction):
    return l_shape(length,direction,direction.get_opp_dir())


def rectangle(length_one: int, direction_one: Direction, length_two: int, direction_two: Direction):
    return [(length_one, direction_one), (length_two, direction_two), (length_one, direction_one.get_opp_dir()),
            (length_two, direction_two.get_opp_dir())]


def square(length: int, direction_one: Direction, direction_two: Direction):
    return rectangle(length, direction_one, length, direction_two)

# These don't return to the shipyard
def l_shape(length: int, direction_one: Direction, direction_two: Direction):
    return [(length,direction_one),(1,direction_two)]

