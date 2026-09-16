import math
import polyline


def decode_polyline(encoded_geometry):
    """
    Decodes ORS's encoded polyline string into a list of (lat, lng) tuples.
    Note: `polyline` lib returns (lat, lng) — matches ORS's default precision (5).
    """
    return polyline.decode(encoded_geometry)


def haversine(coord1, coord2):
    """
    coord1, coord2: (lat, lng) tuples
    Returns distance in miles.
    """
    lat1, lng1 = coord1
    lat2, lng2 = coord2

    R = 3958.8  # Earth radius in miles

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = (math.sin(d_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def dissect_route(encoded_geometry):
    """
    Decodes the route geometry and walks it, computing cumulative
    mile_marker distance at each point.

    Returns: list of dicts: [{'lat':, 'lng':, 'mile_marker':}, ...]
    """
    points = decode_polyline(encoded_geometry)

    route_points = []
    cumulative = 0.0

    for i, (lat, lng) in enumerate(points):
        if i > 0:
            prev_lat, prev_lng = points[i - 1]
            cumulative += haversine((prev_lat, prev_lng), (lat, lng))

        route_points.append({
            'lat': lat,
            'lng': lng,
            'mile_marker': cumulative,
        })

    return route_points


def project_station_onto_route(station_coord, route_points):
    """
    station_coord: (lat, lng)
    route_points: output of dissect_route()

    Practical version (per our design decision): finds the NEAREST
    discrete route point, not the true nearest point on the interpolated
    line segment. Returns (mile_marker, detour_distance).
    """
    nearest_point = min(
        route_points,
        key=lambda p: haversine(station_coord, (p['lat'], p['lng']))
    )

    detour_distance = haversine(station_coord, (nearest_point['lat'], nearest_point['lng']))

    return nearest_point['mile_marker'], detour_distance