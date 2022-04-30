from random import sample

from kaggle_environments.envs.kore_fleets.helpers import ShipyardAction, Player, Board, Fleet

from FleetRoute import FleetRoute
from BoardHelpers import *

DEBUG = True


def spawn(board: Board, player: Player):
    min_total_ship_count = 200
    min_shipyard_ship_count = 200

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
    mining_period = 1
    # mining_turn_gate = 50
    search_range = 6
    min_mining_ships = 8
    shipyards = player.shipyards
    turn = board.step

    if turn % mining_period != 0:
        return

    for shipyard in shipyards:
        if shipyard.next_action is not None:
            continue

        largest_kore_deposit_list = get_best_kore_deposit_to_mine_pos_list(shipyard.position, search_range, board)
        flight_plan = None
        for deposit in largest_kore_deposit_list:
            if not will_fleet_cross_position(deposit.position, player,board):
                flight_plan = FleetRoute.to_point_rect(shipyard.position, deposit.position, board.configuration.size)
                break
        if flight_plan and flight_plan.is_valid(board.step, 400):
            flight_plan_str, _ = flight_plan.to_flight_plan()
            fleet_size = max(get_min_fleet_size_from_flight_plan(flight_plan_str), min_mining_ships)
            if shipyard.ship_count > fleet_size:
                if DEBUG:
                    print(
                        f"Moving to mine largest kore deposit - Position: {deposit.position} Kore: {deposit.kore} Flight Plan: {flight_plan.to_flight_plan()} Turn: {turn}")
                shipyard.next_action = ShipyardAction.launch_fleet_with_flight_plan(fleet_size, flight_plan_str)


def expansion(board: Board, player: Player):
    search_range = 5
    min_dist_from_friendly = 1
    min_dist_from_enemy = 0
    min_expansion_ships = 58
    shipyards = player.shipyards
    turn = board.step

    for shipyard in shipyards:
        if shipyard.next_action is not None:
            continue
        best_shipyard_cell = get_best_cell_to_build_shipyard(shipyard.position, search_range, min_dist_from_friendly,
                                                             min_dist_from_enemy, board)
        if best_shipyard_cell:
            best_shipyard_pos = best_shipyard_cell.position
            if will_fleet_cross_position(best_shipyard_pos, player, board, True):
                continue

            flight_plan = FleetRoute.to_point(shipyard.position, best_shipyard_pos, board.configuration.size)
            flight_plan_str, _ = flight_plan.to_flight_plan()
            flight_plan_str += "C"

            expansion_fleet_size = min_expansion_ships
            if shipyard.ship_count > expansion_fleet_size and flight_plan.is_valid(board.step, 400):
                if DEBUG:
                    print(
                        f"Moving to create shipyard - Position: {best_shipyard_pos} Flight Plan: {flight_plan_str}  Turn: {turn}")
                shipyard.next_action = ShipyardAction.launch_fleet_with_flight_plan(expansion_fleet_size, flight_plan_str)


def fleet_attack(board: Board, player: Player):
    search_range = 6
    min_attack_size = 21
    shipyards = player.shipyards
    turn = board.step

    for shipyard in shipyards:

        if shipyard.next_action is not None:
            continue

        enemy_fleets_in_range = get_enemy_fleets_in_range(shipyard.position, board, player, search_range)
        enemy_fleets_in_range = sample(enemy_fleets_in_range, len(enemy_fleets_in_range))
        for enemy_fleet in enemy_fleets_in_range:
            attack_fleet_size = max(enemy_fleet.ship_count + 1, min_attack_size)
            future_pos = predict_fleet_position(enemy_fleet, player, board, FleetRoute.get_distance_to_pos(shipyard.position, enemy_fleet.position, board.configuration.size))
            if future_pos is not None and attack_fleet_size <= shipyard.ship_count:
                flight_plan = FleetRoute.to_point_rect(shipyard.position, future_pos,
                                                       board.configuration.size)
                flight_plan_str, _ = flight_plan.to_flight_plan()
                if flight_plan.is_valid(board.step, 400):
                    if DEBUG:
                        print(
                            f"Moving to intercept fleet - My Position: {shipyard.position} Enemy current Position: {enemy_fleet.position} Enemy predicted Position: {future_pos} Flight Plan: {flight_plan_str}  Turn: {turn}")
                    shipyard.next_action = ShipyardAction.launch_fleet_with_flight_plan(attack_fleet_size,
                                                                                        flight_plan_str)
                    break


def shipyard_attack(board: Board, player: Player):
    search_range = 10
    min_attack_size = 21

    shipyards = player.shipyards

    should_attack_all = get_total_opp_ship_count(board.opponents) * 2 < get_player_ship_count(player)

    turn = board.step

    for shipyard in shipyards:
        if shipyard.next_action is not None:
            continue
        nearest_enemy_shipyard_info = get_nearest_enemy_shipyard(shipyard.position, board, player, search_range)
        nearest_enemy_shipyard, dist = nearest_enemy_shipyard_info if nearest_enemy_shipyard_info is not None else None, 0
        if nearest_enemy_shipyard:
            nearest_enemy_shipyard_pos = nearest_enemy_shipyard.position
            if will_fleet_cross_position(nearest_enemy_shipyard_pos, player, board):
                continue

            if should_attack_all:
                attack_fleet_size = shipyard.ship_count;
            else:
                attack_fleet_size = max(min_attack_size, nearest_enemy_shipyard.ship_count + 10)

            if 0 < attack_fleet_size <= shipyard.ship_count:

                flight_plan = FleetRoute.to_point(shipyard.position, nearest_enemy_shipyard_pos,
                                                  board.configuration.size)
                flight_plan_str, _ = flight_plan.to_flight_plan()

                if flight_plan.is_valid(board.step, 400):
                    if DEBUG:
                        print(
                            f"Moving to attack shipyard - Position: {nearest_enemy_shipyard_pos} Flight Plan: {flight_plan_str}  Turn: {turn}")
                    shipyard.next_action = ShipyardAction.launch_fleet_with_flight_plan(attack_fleet_size,
                                                                                        flight_plan_str)
    pass


def shipyard_defense(board: Board, player: Player):
    search_range = 5
    shipyards = player.shipyards
    turn = board.step

    for shipyard in shipyards:

        if shipyard.next_action is not None:
            continue

        enemy_fleets_in_range = get_enemy_fleets_in_range(shipyard.position, board, player, search_range)

        for enemy_fleet in enemy_fleets_in_range:
            attack_fleet_size = enemy_fleet.ship_count + 1
            if will_fleet_cross_position(shipyard.position, board.opponents[0], board):
                if attack_fleet_size <= shipyard.ship_count:
                    flight_plan = FleetRoute.to_point_rect(shipyard.position, enemy_fleet.position,
                                                      board.configuration.size)
                    flight_plan_str, _ = flight_plan.to_flight_plan()
                    if flight_plan.is_valid(board.step, 400):
                        if DEBUG:
                            print(
                                f"Moving to defend shipyard - My Position: {shipyard.position} Enemy Position: {enemy_fleet.position} Flight Plan: {flight_plan_str}  Turn: {turn}")
                        shipyard.next_action = ShipyardAction.launch_fleet_with_flight_plan(attack_fleet_size,
                                                                                       flight_plan_str)
                else:
                    friendly_shipyards_in_range = get_friendly_shipyards_in_range(shipyard.position, board, player, 3)
                    for friendly_shipyard in friendly_shipyards_in_range:
                        if attack_fleet_size <= friendly_shipyard.ship_count:
                            flight_plan = FleetRoute.to_point_rect(friendly_shipyard.position, enemy_fleet.position,
                                                                   board.configuration.size)
                            flight_plan_str, _ = flight_plan.to_flight_plan()
                            if flight_plan.is_valid(board.step, 400):
                                if DEBUG:
                                    print(
                                         f"Moving to help defend shipyard - My Position: {friendly_shipyard.position} Enemy Position: {enemy_fleet.position} Flight Plan: {flight_plan_str}  Turn: {turn}")
                                shipyard.next_action = ShipyardAction.launch_fleet_with_flight_plan(attack_fleet_size,
                                                                                                    flight_plan_str)
                                break
                break

