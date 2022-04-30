from kaggle_environments.envs.kore_fleets.helpers import *
from ShipyardCommands import spawn, mining, expansion, fleet_attack, shipyard_attack, shipyard_defense


def agent(obs, config):
    board = Board(obs, config)
    player = board.current_player

    # Shipyard Defense -
    shipyard_defense(board, player)
    # Shipyard Attack -
    shipyard_attack(board, player)
    # Fleet Attack -
    fleet_attack(board, player)
    # Shipyard Expansion -
    expansion(board, player)
    # Mining -
    mining(board, player)
    # Spawn -
    spawn(board, player)
    return player.next_actions
