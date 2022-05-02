import math
# from typing import Tuple, Optional, Union

from kaggle_environments.envs.kore_fleets.helpers import Player, Board, Cell, Shipyard
from kaggle_environments.helpers import Point


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


def get_largest_kore_deposit_pos(position: Point, search_range: int, board: Board) -> Cell:
    return get_largest_kore_deposit_pos_list(position, search_range, board)[0]


def get_largest_kore_deposit_pos_list(position: Point, search_range: int, board: Board) -> [Cell]:
    cells_in_range = []
    for y in range(-search_range, search_range + 1):
        for x in range(-search_range, search_range + 1):
            offset = Point(x, y)
            if offset == Point(0, 0):
                continue
            search_point = position.translate(offset, board.configuration.size)
            search_cell = board.get_cell_at_point(search_point)
            cells_in_range.append(search_cell)
    cells_in_range.sort(reverse=True, key=lambda cell: cell.kore)
    return cells_in_range


def get_best_shipyard_cell(position: Point, search_range: int, dist_from_friendly: int, dist_from_enemy: int,
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
            nearest_shipyard, dist = get_nearest_shipyard(search_point, board)
            if nearest_shipyard:
                if nearest_shipyard.player_id == board.current_player.id and dist <= dist_from_friendly:
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


def is_fleet_enroute(player: Player, flight_plan: str):
    fleets = player.fleets
    for fleet in fleets:
        return fleet.flight_plan == flight_plan


def get_min_fleet_size_from_flight_plan(flight_plan: str):
    return math.ceil(math.e ** ((len(flight_plan) - 1) * .5))


def get_nearest_shipyard(position: Point, board: Board, search_range: int = math.inf):
    shipyards = board.shipyards.values()
    min_dist = search_range
    nearest = None
    for shipyard in shipyards:
        if position == shipyard.position:
            continue
        dist = position.distance_to(shipyard.position, board.configuration.size)
        if dist < min_dist:
            min_dist = dist
            nearest = shipyard
    return nearest, min_dist


def get_nearest_enemy_shipyard(position: Point, board: Board, player: Player, search_range: int = math.inf):
    shipyards = board.shipyards.values()
    min_dist = search_range
    nearest = None
    for shipyard in shipyards:
        if position == shipyard.position or shipyard.player_id == player.id:
            continue
        dist = position.distance_to(shipyard.position, board.configuration.size)
        if dist < min_dist:
            min_dist = dist
            nearest = shipyard
    return nearest, min_dist


def get_nearest_friendly_shipyard(position: Point, board: Board, player: Player, search_range: int = math.inf):
    shipyards = board.shipyards.values()
    min_dist = search_range
    nearest = None
    for shipyard in shipyards:
        if position == shipyard.position or shipyard.player_id != player.id:
            continue
        dist = position.distance_to(shipyard.position, board.configuration.size)
        if dist < min_dist:
            min_dist = dist
            nearest = shipyard
    return nearest, min_dist
