import math

import numpy as np
from kaggle_environments.envs.kore_fleets.helpers import Board, ShipyardAction
from kaggle_environments.helpers import Point
import FleetRoute

SHIPYARD_ACTIONS = [None, 'SPAWN', 'LAUNCH', 'EXPAND']


def point_to_index(point, size):
    return point.x + point.y * size


def transform_actions(actions, obs, config):
    next_actions = {}
    board = Board(obs, config)
    player = board.current_player

    for shipyard in player.shipyards:
        index = 0#shipyard.position.to_index(config.size) * 6
        shipyard_action = actions[index]
        fleet_route_type = FleetRoute.FleetRouteType(actions[index + 1] + 1)
        x_pos = actions[index + 2]
        y_pos = actions[index + 3]
        ships_per = actions[index + 4]

        if SHIPYARD_ACTIONS[shipyard_action] == 'SPAWN':
            max_ships = min(player.kore / config.spawnCost, shipyard.max_spawn)
            num_ships = math.floor(max_ships * (ships_per / 100))
            if num_ships > 0:
                next_actions[shipyard.id] = ShipyardAction.spawn_ships(num_ships).name
        elif SHIPYARD_ACTIONS[shipyard_action] == 'LAUNCH' or 'EXPAND':
            flight_plan = FleetRoute.FleetRoute.to_pos(shipyard.position, Point(x_pos, y_pos), config.size,
                                                       fleet_route_type).to_flight_plan()[
                              0]
            flight_plan = flight_plan + 'C' if SHIPYARD_ACTIONS[shipyard_action] == 'EXPAND' else ''
            num_ships = math.floor(shipyard.ship_count * (ships_per / 100))
            if num_ships > 0 and len(flight_plan) > 0 and flight_plan[0].isalpha() and flight_plan[0] in "NESW":
                next_actions[shipyard.id] = ShipyardAction.launch_fleet_with_flight_plan(num_ships, flight_plan).name
        else:
            next_actions[shipyard.id] = None
    return next_actions

MAX_KORE = 9149200
MAX_SHIPS = 1764000
MAX_SHIP_SPAWN = 10
MAX_DIRECTION = 4

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
    opp_shipyards = []
    opp_shipyards_max_spawn = []
    opp_fleets = []
    opp_fleets_cargo = []

    directions = []

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
            opp_fleets.append(0)
            opp_fleets_cargo.append(0)
            directions.append(0)

        elif cell.fleet in player.shipyards:
            player_fleets.append(cell.fleet.ship_count / MAX_SHIPS)
            player_fleets_cargo.append(cell.fleet.kore / MAX_KORE)
            opp_fleets.append(0)
            opp_fleets_cargo.append(0)
            directions.append((cell.fleet.direction.to_index() + 1) / MAX_DIRECTION)

        else:
            player_fleets.append(0)
            player_fleets_cargo.append(0)
            opp_fleets.append(cell.fleet.ship_count / MAX_SHIPS)
            opp_fleets_cargo.append(cell.fleet.kore / MAX_KORE)
            directions.append((cell.fleet.direction.to_index() + 1) / MAX_DIRECTION)

        if cell.shipyard is None:
            player_shipyards.append(0)
            opp_shipyards.append(0)
            player_shipyards_max_spawn.append(0)
            opp_shipyards_max_spawn.append(0)

        elif cell.shipyard in player.shipyards:
            player_shipyards.append(cell.shipyard.ship_count / MAX_KORE)
            player_shipyards_max_spawn.append(cell.shipyard.max_spawn / MAX_SHIP_SPAWN)
            opp_shipyards.append(0)
            opp_shipyards_max_spawn.append(0)


        else:
            player_shipyards.append(0)
            player_shipyards_max_spawn.append(0)
            opp_shipyards.append(cell.shipyard.ship_count / MAX_KORE)
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
                       opp_shipyards,
                       opp_shipyards_max_spawn,
                       opp_fleets,
                       opp_fleets_cargo,
                       directions))

    x_obs = np.nan_to_num(x_obs.reshape((config.size, config.size, num_features))).astype(np.float32)
    return x_obs


REWARD_WON = 400
REWARD_LOST = -REWARD_WON

MAX_DELTA = 500


def transform_reward(done, last_obs, obs, config):
    board = Board(obs, config)
    player = board.current_player

    num_fleets = len(player.fleets)
    num_shipyards = len(player.shipyards)
    num_kore = player.kore
    num_cargo = sum(s.kore for s in player.fleets)

    if num_fleets == 0:
        if num_shipyards == 0:
            return REWARD_LOST
        if num_kore < config.spawnCost:
            return REWARD_LOST

    if done:
        scores = [p.kore for p in board.players.values() if
                  len(p.fleets) > 0 or
                  (len(p.shipyards) > 0 and p.kore >= config.spawnCost)]

        if num_kore == max(scores):
            if scores.count(num_kore) == 1:
                return REWARD_WON
        return REWARD_LOST

    delta = 0

    if last_obs is not None:
        last_board = Board(last_obs, config)
        last_player = last_board.current_player

        last_num_fleets = len(last_player.fleets)
        last_num_shipyards = len(last_player.shipyards)
        last_num_kore = last_player.kore
        last_num_cargo = sum(s.kore for s in last_player.fleets)

        delta_fleets = (num_fleets - last_num_fleets) * config.spawnCost
        delta_shipyards = (num_shipyards - last_num_shipyards) * (config.convertCost + config.spawnCost)
        delta_kore = num_kore - last_num_kore
        delta_cargo = num_cargo - last_num_cargo

        delta = delta_fleets + delta_shipyards + delta_kore + delta_cargo

        if delta_kore > 0:
            delta += MAX_DELTA

        if delta_cargo > 0:
            delta += MAX_DELTA // 2

        if num_shipyards == 0:
            delta -= MAX_DELTA

        if num_fleets == 0:
            delta -= MAX_DELTA

        delta = float(np.clip(delta / MAX_DELTA, -1, 1))

    reward = delta + 1 / MAX_DELTA
    return reward
