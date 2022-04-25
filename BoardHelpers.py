def get_player_ship_count(player):
    ship_count = 0
    shipyards = player.shipyards
    fleets = player.fleets
    for shipyard in shipyards:
        ship_count += shipyard.ship_count
    for fleet in fleets:
        ship_count += fleet.ship_count
    return ship_count


def get_total_opp_ship_count(opponents):
    total_ship_count = 0
    for opp in opponents:
        total_ship_count += get_player_ship_count(opp)
    return total_ship_count
