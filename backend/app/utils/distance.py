import math
from typing import Tuple


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return round(distance, 2)


def calculate_delivery_fee(distance_km: float) -> float:
    if distance_km <= 3:
        return 3.0
    elif distance_km > 10:
        return -1
    else:
        extra = math.ceil(distance_km - 3)
        return min(3.0 + extra * 1.0, 10.0)


def calculate_distance_and_fee(lat1: float, lon1: float, lat2: float, lon2: float) -> Tuple[float, float]:
    distance = haversine_distance(lat1, lon1, lat2, lon2)
    fee = calculate_delivery_fee(distance)
    return distance, fee
