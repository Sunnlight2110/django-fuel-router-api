import time
from .geo import haversine, project_station_onto_route


def filter_candidate_stations(stations, route_points, bounding_box_margin=50):
    """
    stations: queryset/list of FuelStation objects (with .latitude, .longitude, .price, etc.)
    route_points: output of dissect_route()
    bounding_box_margin: miles of slack around the route's lat/lng box

    Returns: list of dicts, one per surviving station:
        {'station': <FuelStation>, 'mile_marker':, 'detour_distance':}

    This is a PERFORMANCE prefilter only (cheap bounding box), not a
    feasibility filter — no station is excluded here just for being
    "too far" in the cost sense. Feasibility (500mi range) is decided
    later, at graph-build time.
    """
    lats = [p['lat'] for p in route_points]
    lngs = [p['lng'] for p in route_points]

    margin_deg = bounding_box_margin / 69.0

    min_lat, max_lat = min(lats) - margin_deg, max(lats) + margin_deg
    min_lng, max_lng = min(lngs) - margin_deg, max(lngs) + margin_deg

    candidates = []
    projection_time = 0.0

    for station in stations:
        if not (min_lat <= station.latitude <= max_lat):
            continue
        if not (min_lng <= station.longitude <= max_lng):
            continue

        t_proj = time.perf_counter()
        mile_marker, detour_distance = project_station_onto_route(
            (station.latitude, station.longitude), route_points
        )
        projection_time += time.perf_counter() - t_proj

        candidates.append({
            'station': station,
            'mile_marker': mile_marker,
            'detour_distance': detour_distance,
        })

    # print total projection time (keeps changes minimal and removable)
    print(f"[PERF] Station projection: {projection_time:.3f}s")
    return candidates