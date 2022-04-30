import math
from numpy import log as ln

# from typing import Tuple, Optional, Union

from kaggle_environments.envs.kore_fleets.helpers import Player, Board, Cell, Shipyard, Fleet
from kaggle_environments.helpers import Point

from Directions import Direction
from FleetRoute import FleetRoute


def get_player_ship_count(player: Player) -> int:
    ship_count = 0
    shipyards = player.shipyards
    fleets = player.fleets
    for shipyard in shipyards:
        ship_count += shipyard.ship_count
    for fleet in fleets:
        ship_count += fleet.ship_count
    return ship_count


def get_total_opp_ship_count(opponents: [Player]) -> int:
    total_ship_count = 0
    for opp in opponents:
        total_ship_count += get_player_ship_count(opp)
    return total_ship_count


def get_best_kore_deposit_to_mine(position: Point, search_range: int, board: Board) -> Cell:
    return get_best_kore_deposit_to_mine_pos_list(position, search_range, board)[0]


def get_best_kore_deposit_to_mine_pos_list(position: Point, search_range: int, board: Board) -> [Cell]:
    cells_in_range = []
    for y in range(-search_range, search_range + 1):
        for x in range(-search_range, search_range + 1):
            offset = Point(x, y)
            if offset == Point(0, 0):
                continue
            search_point = position.translate(offset, board.configuration.size)
            search_cell = board.get_cell_at_point(search_point)
            cells_in_range.append(search_cell)
    cells_in_range.sort(reverse=True, key=lambda cell: cell.kore * get_fleet_size_to_per_mined(
        get_min_fleet_size_from_flight_plan(
            FleetRoute.to_point_rect(position, cell.position, board.configuration.size).to_flight_plan())))
    return cells_in_range


def get_fleet_size_to_per_mined(size: int) -> float:
    return ln(size) / 20


def get_best_cell_to_build_shipyard(position: Point, search_range: int, dist_from_friendly: int, dist_from_enemy: int,
                                    board: Board) -> Cell:
    best_shipyard_cell = None
    max_kore = -math.inf
    for y in range(-search_range, search_range + 1):
        for x in range(-search_range, search_range + 1):
            offset = Point(x, y)
            if offset == Point(0, 0):
                continue
            search_point = position.translate(offset, board.configuration.size)
            search_cell = board.get_cell_at_point(search_point)

            if search_cell.shipyard:
                continue

            nearest_shipyard = get_nearest_shipyard(search_point, board)
            if nearest_shipyard:
                dist = search_point.distance_to(nearest_shipyard.position, board.configuration.size)
                if nearest_shipyard.player_id == board.current_player.id:
                    if dist <= dist_from_friendly:
                        continue
                elif dist <= dist_from_enemy:
                    continue

            kore = get_kore_in_range(search_point, 1, board)
            if kore > max_kore:
                max_kore = kore
                best_shipyard_cell = search_cell
    return best_shipyard_cell


def get_kore_in_range(position: Point, search_range: int, board: Board) -> float:
    total_kore_count = 0
    for y in range(-search_range, search_range + 1):
        for x in range(-search_range, search_range + 1):
            offset = Point(x, y)
            if offset == Point(0, 0):
                continue
            search_point = position.translate(offset, board.configuration.size)
            search_cell = board.get_cell_at_point(search_point)
            total_kore_count += search_cell.kore
    return total_kore_count


def predict_fleet_position(fleet: Fleet, player: Player, board: Board, turn_to_checks: int):
    obs = board
    for index in range(turn_to_checks):
        obs = obs.next()
    return obs.fleets[fleet.id].position if fleet.id in obs.fleets.keys() else None


def will_fleet_cross_position(position: Point, player: Player,
                              board: Board, check_expanding: bool = False, turn_to_checks: int = 3) -> bool:
    obs = board
    for index in range(turn_to_checks):
        for fleet in obs.fleets.values():
            if fleet.player_id == player.id:
                dx = 0
                dy = 0
                direction = fleet.direction.to_char() if len(fleet.flight_plan) == 0 or fleet.flight_plan[
                    0].isnumeric() else fleet.flight_plan[0]
                if direction == Direction.NORTH.to_char():
                    dy += 1
                if direction == Direction.SOUTH.to_char():
                    dy -= 1
                if direction == Direction.WEST.to_char():
                    dx -= 1
                if direction == Direction.EAST.to_char():
                    dx += 1
                next_pos = fleet.position.translate(Point(dx, dy), board.configuration.size)

                if next_pos == position:
                    if not check_expanding:
                        return True
                    else:
                        if len(fleet.flight_plan) > 0 and fleet.flight_plan[-1] == "C":
                            return True
                        else:
                            continue
        obs = obs.next()
    return False


def get_min_fleet_size_from_flight_plan(flight_plan: str) -> int:
    return math.ceil(math.e ** ((len(flight_plan) - 1) * .5))


def get_shipyards_in_range(position: Point, board: Board, search_range: int = math.inf) -> [Shipyard]:
    return list(
        filter(lambda x: position != x.position and position.distance_to(x.position,
                                                                         board.configuration.size) < search_range,
               board.shipyards.values()))


def get_enemy_shipyards_in_range(position: Point, board: Board, player: Player, search_range: int = math.inf) -> [
    Shipyard]:
    return list(
        filter(lambda x: position != x.position and position.distance_to(x.position,
                                                                         board.configuration.size) < search_range and player.id != x.player_id,
               board.shipyards.values()))


def get_friendly_shipyards_in_range(position: Point, board: Board, player: Player, search_range: int = math.inf) -> [
    Shipyard]:
    return list(
        filter(lambda x: position != x.position and position.distance_to(x.position,
                                                                         board.configuration.size) < search_range and player.id == x.player_id,
               board.shipyards.values()))


def get_nearest_shipyard(position: Point, board: Board, search_range: int = math.inf) -> Shipyard:
    shipyards = sorted(get_shipyards_in_range(position, board, search_range),
                       key=lambda x: position.distance_to(x.position, board.configuration.size))
    return shipyards[0] if len(shipyards) > 0 else None


def get_nearest_enemy_shipyard(position: Point, board: Board, player: Player, search_range: int = math.inf) -> Shipyard:
    shipyards = sorted(get_enemy_shipyards_in_range(position, board, player, search_range),
                       key=lambda x: position.distance_to(x.position, board.configuration.size))
    return shipyards[0] if len(shipyards) > 0 else None


def get_nearest_friendly_shipyard(position: Point, board: Board, player: Player,
                                  search_range: int = math.inf) -> Shipyard:
    shipyards = sorted(get_friendly_shipyards_in_range(position, board, player, search_range),
                       key=lambda x: position.distance_to(x.position, board.configuration.size))
    return shipyards[0] if len(shipyards) > 0 else None


def get_fleets_in_range(position: Point, board: Board, search_range: int = math.inf) -> [Fleet]:
    return list(
        filter(lambda x: position.distance_to(x.position, board.configuration.size) < search_range,
               board.fleets.values()))


def get_enemy_fleets_in_range(position: Point, board: Board, player: Player, search_range: int = math.inf) -> [Fleet]:
    return list(filter(lambda x: position.distance_to(x.position,
                                                      board.configuration.size) < search_range and player.id != x.player_id,
                       board.fleets.values()))


def get_friendly_fleets_in_range(position: Point, board: Board, player: Player, search_range: int = math.inf) -> [
    Fleet]:
    return list(filter(lambda x: position.distance_to(x.position,
                                                      board.configuration.size) < search_range and player.id == x.player_id,
                       board.fleets.values()))
