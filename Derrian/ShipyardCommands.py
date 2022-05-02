from kaggle_environments.envs.kore_fleets.helpers import ShipyardAction, Player, Board

from FleetRoute import FleetRoute
from BoardHelpers import *

DEBUG = False

def spawn(board: Board, player: Player):
    min_total_ship_count = 100
    min_shipyard_ship_count = 50

    shipyards = player.shipyards
    kore_count = player.kore
    spawn_cost = board.configuration.spawn_cost
    turn = board.step

    if len(shipyards) <= 0:
        return

    total_target_ship_count = max(
        int((get_total_opp_ship_count(board.opponents) / (max(len(board.opponents), 1))) * 1.5), min_total_ship_count)
    target_shipyard_ship_count = max(int(total_target_ship_count / len(shipyards)), min_shipyard_ship_count)
    for shipyard in shipyards:
        if shipyard.next_action is not None:
            continue
        curr_ship_count = shipyard.ship_count
        if curr_ship_count <= target_shipyard_ship_count:
            spawn_amount = min(int(kore_count / spawn_cost), shipyard.max_spawn)
            if DEBUG:
                print(
                f"Spawning Ships - Position: {shipyard.position} Ship Count: {spawn_amount} Turn: {turn}")
            shipyard.next_action = ShipyardAction.spawn_ships(spawn_amount)


def mining(board: Board, player: Player):
    mining_period = 4
    # mining_turn_gate = 50
    search_range = 5
    min_mining_ships = 8
    shipyards = player.shipyards
    turn = board.step

    if turn % mining_period != 0:
        return

    for shipyard in shipyards:
        if shipyard.next_action is not None:
            continue

        largest_kore_deposit_list = get_largest_kore_deposit_pos_list(shipyard.position, search_range, board)
        flight_plan = None
        for deposit in largest_kore_deposit_list:
            flight_plan = FleetRoute.to_point_rect(shipyard.position, deposit.position, board.configuration.size)
            if not is_fleet_enroute(player, flight_plan):
                break
        if flight_plan:
            flight_plan_str = flight_plan.to_flight_plan()
            fleet_size = max(get_min_fleet_size_from_flight_plan(flight_plan_str), min_mining_ships)
            if flight_plan.is_valid(fleet_size):
                if shipyard.ship_count > fleet_size:
                    if DEBUG:
                        print(f"Moving to mine largest kore deposit - Position: {deposit.position} Kore: {deposit.kore} Flight Plan: {flight_plan.to_flight_plan()} Turn: {turn}")
                    shipyard.next_action = ShipyardAction.launch_fleet_with_flight_plan(fleet_size, flight_plan_str)


def expansion(board: Board, player: Player):
    search_range = 5
    min_dist_from_friendly = 3
    min_dist_from_enemy = 4
    min_expansion_ships = 71
    shipyards = player.shipyards
    turn = board.step

    for shipyard in shipyards:
        if shipyard.next_action is not None:
            continue
        best_shipyard_cell = get_best_shipyard_cell(shipyard.position, search_range, min_dist_from_friendly,
                                                    min_dist_from_enemy, board)
        if best_shipyard_cell:
            best_shipyard_pos = best_shipyard_cell.position
            flight_plan = FleetRoute.to_point(shipyard.position, best_shipyard_pos, board.configuration.size)
            flight_plan_str = flight_plan.to_flight_plan() + "C"
            if is_fleet_enroute(player, flight_plan):
                continue

            fleet_size = min_expansion_ships
            if shipyard.ship_count > fleet_size * 1.1 and flight_plan.is_valid(fleet_size):
                if DEBUG:
                    print(f"Moving to create shipyard - Position: {best_shipyard_pos} Flight Plan: {flight_plan_str}  Turn: {turn}")
                shipyard.next_action = ShipyardAction.launch_fleet_with_flight_plan(fleet_size, flight_plan_str)


def fleet_attack(board: Board, player: Player):
    pass


def shipyard_attack(board: Board, player: Player):
    search_range = 10
    shipyards = player.shipyards

    should_attack_all = get_total_opp_ship_count(board.opponents) * 2 < get_player_ship_count(player)

    turn = board.step

    for shipyard in shipyards:
        if shipyard.next_action is not None:
            continue
        nearest_enemy_shipyard, dist = get_nearest_enemy_shipyard(shipyard.position, board, player, search_range)
        if nearest_enemy_shipyard:

            if should_attack_all:
                attack_fleet_size = shipyard.ship_count;
            else:
                attack_fleet_size = nearest_enemy_shipyard.ship_count + 10;

            if 0 < attack_fleet_size <= shipyard.ship_count:
                nearest_enemy_shipyard_pos = nearest_enemy_shipyard.position
                flight_plan = FleetRoute.to_point(shipyard.position, nearest_enemy_shipyard_pos,
                                                  board.configuration.size)
                flight_plan_str = flight_plan.to_flight_plan()
                if is_fleet_enroute(player, flight_plan):
                    continue
                if flight_plan.is_valid(attack_fleet_size):
                    if DEBUG:
                        print(f"Moving to attack shipyard - Position: {nearest_enemy_shipyard_pos} Flight Plan: {flight_plan_str}  Turn: {turn}")
                    shipyard.next_action = ShipyardAction.launch_fleet_with_flight_plan(attack_fleet_size,
                                                                                        flight_plan_str)
    pass


def shipyard_defense(board: Board, player: Player):
    pass
