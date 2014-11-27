import math


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000.0  # Earth radius in metres
    d_lat = math.radians(lat2-lat1)
    d_lon = math.radians(lon2-lon1)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    # Haversine formula
    a = math.pow(math.sin(d_lat/2.0), 2) + math.pow(math.sin(d_lon/2.0), 2) * math.cos(lat1) * math.cos(lat2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0-a))
    dist = R * c

    return dist
