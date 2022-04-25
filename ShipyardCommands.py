from kaggle_environments.envs.kore_fleets.helpers import ShipyardAction
from BoardHelpers import *


def spawn(board, player):

    min_ship_count = 200

    shipyards = player.shipyards
    kore_count = player.kore
    spawn_cost = board.configuration.spawn_cost

    target_ship_count = max(int(get_total_opp_ship_count(board.opponents) * 1.5), min_ship_count)
    for shipyard in shipyards:
        curr_ship_count = get_player_ship_count(player)
        if curr_ship_count < target_ship_count:
            shipyard.next_action = ShipyardAction.spawn_ships(min(shipyard.max_spawn, int(kore_count/spawn_cost)))


def mining(board, player):
    pass


def expansion(board, player):
    pass


def fleet_attack(board, player):
    pass


def shipyard_attack(board, player):
    pass


def shipyard_defense(board, player):
    pass
