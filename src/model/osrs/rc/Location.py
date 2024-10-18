from enum import Enum
from utilities.api.morg_http_client import MorgHTTPSocket


def get_location():
    api_m = MorgHTTPSocket()
    if api_m.get_player_region_data()[2] == 14484:
        if api_m.get_player_position()[0] <= 3591:
            return Location.LEFT_AREA
        if api_m.get_player_position()[0] >= 3637:
            return Location.RIGHT_AREA
        return Location.MAIN_AREA
    else:
        return Location.ALTAR


class Location(Enum):
    MAIN_AREA = 1
    LEFT_AREA = 2
    RIGHT_AREA = 3
    ALTAR = 4

