import math

import numpy as np
from kaggle_environments.envs.kore_fleets.helpers import Board, ShipyardAction
from kaggle_environments.helpers import Point
import FleetRoute
import logging

logging.basicConfig(filename='log/log.log', filemode='w', level=logging.DEBUG)
SHIPYARD_ACTIONS = [None, 'SPAWN', 'LAUNCH', 'EXPAND']


def point_to_index(point, size):
    return point.x + point.y * size


def transform_actions(actions, obs, config):
    next_actions = {}
    board = Board(obs, config)
    player = board.current_player

    for shipyard in player.shipyards:
        index = shipyard.position.to_index(config.size) * 5
        shipyard_action = actions[index]
        fleet_route_type = FleetRoute.FleetRouteType(actions[index + 1] + 1)
        x_pos = actions[index + 2]
        y_pos = actions[index + 3]
        ships_per = actions[index + 4]

        if SHIPYARD_ACTIONS[shipyard_action] == 'SPAWN':
            max_ships = min(player.kore / config.spawnCost, shipyard.max_spawn)
            num_ships = math.floor(max_ships * (ships_per / 100))
            if num_ships > 1:
                next_actions[shipyard.id] = ShipyardAction.spawn_ships(num_ships).name
        elif SHIPYARD_ACTIONS[shipyard_action] == 'LAUNCH' or 'EXPAND':
            flight_plan = FleetRoute.FleetRoute.to_pos(shipyard.position, Point(x_pos, y_pos), config.size,
                                                       fleet_route_type).to_flight_plan()[
                0]
            flight_plan = flight_plan + 'C' if SHIPYARD_ACTIONS[shipyard_action] == 'EXPAND' else ''
            num_ships = math.floor(shipyard.ship_count * (ships_per / 100))
            if num_ships > 1 and len(flight_plan) > 0 and flight_plan[0].isalpha() and flight_plan[0] in "NESW":
                next_actions[shipyard.id] = ShipyardAction.launch_fleet_with_flight_plan(num_ships, flight_plan).name
        else:
            next_actions[shipyard.id] = None
    return next_actions


MAX_SHIP_SPAWN = 10
MAX_KORE = 26340000
MAX_CARGO = 26340000
MAX_SHIPS = 2634000
MAX_FLEETS = 439
MAX_SHIPYARDS = 439
MAX_DIRECTIONS = 4


def transform_observation(done, obs, config, num_features):
    board = Board(obs, config)
    player = board.current_player

    board_cells = board.cells

    step = []
    done_step = []
    player_kore = []
    player_cargo = []
    opp_kore = []
    opp_cargo = []
    player_shipyards = []
    player_shipyards_max_spawn = []
    player_fleets = []
    player_fleets_cargo = []
    player_fleets_directions = []
    opp_shipyards = []
    opp_shipyards_max_spawn = []
    opp_fleets = []
    opp_fleets_cargo = []
    opp_fleets_directions = []

    player_kore_val = player.kore
    opp_kore_val = max(p.kore for p in board.opponents)

    player_cargo_val = sum(s.kore for s in player.fleets)
    opp_cargo_val = max(sum(s.kore for s in p.fleets) for p in board.opponents)

    for point, cell in board_cells.items():
        step.append(obs['step'] / config.episodeSteps)
        done_step.append(int(done))

        player_kore.append(player_kore_val / MAX_KORE)
        player_cargo.append(player_cargo_val / MAX_KORE)
        opp_kore.append(opp_kore_val / MAX_KORE)
        opp_cargo.append(opp_cargo_val / MAX_KORE)

        if cell.fleet is None:
            player_fleets.append(0)
            player_fleets_cargo.append(0)
            player_fleets_directions.append(0)
            opp_fleets.append(0)
            opp_fleets_cargo.append(0)
            opp_fleets_directions.append(0)

        elif cell.fleet in player.fleets:
            player_fleets.append(cell.fleet.ship_count / MAX_SHIPS)
            player_fleets_cargo.append(cell.fleet.kore / MAX_KORE)
            player_fleets_directions.append((cell.fleet.direction.to_index() + 1) / MAX_DIRECTIONS)
            opp_fleets.append(0)
            opp_fleets_cargo.append(0)
            opp_fleets_directions.append(0)

        else:
            player_fleets.append(0)
            player_fleets_cargo.append(0)
            player_fleets_directions.append(0)
            opp_fleets.append(cell.fleet.ship_count)
            opp_fleets_cargo.append(cell.fleet.kore)
            opp_fleets_directions.append((cell.fleet.direction.to_index() + 1) / MAX_DIRECTIONS)

        if cell.shipyard is None:
            player_shipyards.append(0)
            opp_shipyards.append(0)
            player_shipyards_max_spawn.append(0)
            opp_shipyards_max_spawn.append(0)

        elif cell.shipyard in player.shipyards:
            player_shipyards.append(cell.shipyard.ship_count / MAX_SHIPS)
            player_shipyards_max_spawn.append(cell.shipyard.max_spawn / MAX_SHIP_SPAWN)
            opp_shipyards.append(0)
            opp_shipyards_max_spawn.append(0)


        else:
            player_shipyards.append(0)
            player_shipyards_max_spawn.append(0)
            opp_shipyards.append(cell.shipyard.ship_count / MAX_SHIPS)
            opp_shipyards_max_spawn.append(cell.shipyard.max_spawn / MAX_SHIP_SPAWN)

    x_obs = np.vstack((step,
                       done_step,
                       player_kore,
                       player_cargo,
                       opp_cargo,
                       player_shipyards,
                       player_shipyards_max_spawn,
                       player_fleets,
                       player_fleets_cargo,
                       player_fleets_directions,
                       opp_shipyards,
                       opp_shipyards_max_spawn,
                       opp_fleets,
                       opp_fleets_cargo,
                       opp_fleets_directions))

    x_obs = np.nan_to_num(x_obs.reshape((config.size, config.size, num_features))).astype(np.float32)
    return x_obs


REWARD_WON = 100
REWARD_LOST = -REWARD_WON

MAX_REWARD_DELTA = 10


def transform_reward(done, last_obs, obs, config):
    board = Board(obs, config)
    player = board.current_player
    opp = board.opponents[0]

    num_fleets = len(player.fleets)
    num_shipyards = len(player.shipyards)
    num_ships = sum(f.ship_count for f in player.shipyards)
    num_kore = player.kore
    num_cargo = sum(f.kore for f in player.fleets)

    opp_num_fleets = len(opp.fleets)
    opp_num_shipyards = len(opp.shipyards)
    opp_num_ships = sum(f.ship_count for f in opp.shipyards)
    opp_num_kore = opp.kore
    opp_num_cargo = sum(f.kore for f in opp.fleets)

    step_reward = config.episodeSteps - board.step

    if num_fleets <= 0:
        if num_shipyards <= 0:
            logging.debug("num_shipyards <= 0: turn %s", board.step)
            return REWARD_LOST - step_reward
        if num_kore < config.spawnCost:
            logging.debug("num_kore <= spawnCost: turn %s", board.step)
            return REWARD_LOST - step_reward

    if done:
        scores = [p.kore for p in board.players.values() if
                  len(p.fleets) > 0 or
                  (len(p.shipyards) > 0)]

        if num_kore == max(scores):
            logging.debug("num_kore == winning_kore: turn %s", board.step)
            return REWARD_WON + step_reward
        logging.debug("num_kore != winning_kore: turn %s", board.step)
        return REWARD_LOST - step_reward

    delta = 0

    if last_obs is not None:
        last_board = Board(last_obs, config)
        last_player = last_board.current_player
        last_opp = last_board.opponents[0]

        last_num_fleets = len(last_player.fleets)
        last_num_ships = sum(f.ship_count for f in last_player.shipyards)
        last_num_shipyards = len(last_player.shipyards)
        last_num_kore = last_player.kore
        last_num_cargo = sum(f.kore for f in last_player.fleets)

        last_opp_num_fleets = len(last_opp.fleets)
        last_opp_num_shipyards = len(last_opp.shipyards)
        last_opp_num_ships = sum(f.ship_count for f in last_opp.shipyards)
        last_opp_num_kore = last_opp.kore
        last_opp_num_cargo = sum(f.kore for f in last_opp.fleets)

        delta_fleets = (num_fleets - last_num_fleets) / MAX_FLEETS
        delta_ships = (num_ships - last_num_ships) / MAX_SHIPS
        delta_shipyards = (num_shipyards - last_num_shipyards) / MAX_SHIPYARDS
        delta_kore = (num_kore - last_num_kore) / MAX_KORE
        delta_cargo = (num_cargo - last_num_cargo) / MAX_CARGO

        delta_opp_fleets = (opp_num_fleets - last_opp_num_fleets) / MAX_FLEETS
        delta_opp_ships = (opp_num_ships - last_opp_num_ships) / MAX_SHIPS
        delta_opp_shipyards = (opp_num_shipyards - last_opp_num_shipyards) / MAX_SHIPYARDS
        delta_opp_kore = (opp_num_kore - last_opp_num_kore) / MAX_KORE
        delta_opp_cargo = (opp_num_cargo - last_opp_num_cargo) / MAX_CARGO

        assert -1 <= delta_fleets <= 1, f"Delta fleet is outside of range: ({num_fleets} - {last_num_fleets}) / {MAX_FLEETS} = {delta_fleets}"
        assert -1 <= delta_ships <= 1, f"Delta ships is outside of range: ({num_ships} - {last_num_ships}) / {MAX_SHIPS} = {delta_ships}"
        assert -1 <= delta_shipyards <= 1, f"Delta shipyards is outside of range: ({num_shipyards} - {last_num_shipyards}) / {MAX_SHIPYARDS} = {delta_shipyards}"
        assert -1 <= delta_kore <= 1, f"Delta kore is outside of range: ({num_kore} - {last_num_kore}) / {MAX_KORE} = {delta_kore}"
        assert -1 <= delta_cargo <= 1, f"Delta cargo is outside of range: ({num_cargo} - {last_num_cargo}) / {MAX_CARGO} = {delta_cargo}"
        assert -1 <= delta_opp_fleets <= 1, f"Delta opp fleet is outside of range: ({opp_num_fleets} - {last_opp_num_fleets}) / {MAX_FLEETS} = {delta_opp_fleets}"
        assert -1 <= delta_opp_ships <= 1, f"Delta opp ships is outside of range: ({opp_num_ships} - {last_opp_num_ships}) / {MAX_SHIPS} = {delta_opp_ships}"
        assert -1 <= delta_opp_shipyards <= 1, f"Delta opp shipyards is outside of range: ({opp_num_shipyards} - {last_opp_num_shipyards}) / {MAX_SHIPYARDS} = {delta_opp_shipyards}"
        assert -1 <= delta_opp_kore <= 1, f"Delta opp kore is outside of range: ({opp_num_kore} - {last_opp_num_kore}) / {MAX_KORE} = {delta_opp_kore}"
        assert -1 <= delta_opp_cargo <= 1, f"Delta opp cargo is outside of range: ({opp_num_cargo} - {last_opp_num_cargo}) / {MAX_CARGO} = {delta_opp_cargo}"

        delta = delta_fleets - delta_opp_fleets + delta_ships - delta_opp_ships + delta_shipyards - delta_opp_shipyards + delta_kore - delta_opp_kore + delta_cargo - delta_opp_cargo
    reward = delta / MAX_REWARD_DELTA
    assert -1 <= reward <= 1, f"Reward is outside of range: ({delta} / {MAX_REWARD_DELTA} = {reward}"
    return reward
