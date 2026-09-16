import time
from . import utils as ors_client
from .geo import dissect_route
from .candidates import filter_candidate_stations
from .graph import build_graph, solve_cheapest_path, MPG


def compute_route_and_fuel_stops(start_coords, finish_coords, stations):
    """
    start_coords, finish_coords: (longitude, latitude) tuples, as ORS expects
    stations: queryset/list of FuelStation objects to consider

    Returns a dict ready to hand to a serializer:
        {
            'total_distance_miles': float,
            'total_fuel_cost': float,
            'route_geometry': <encoded polyline string>,
            'fuel_stops': [
                {
                    'station_name':,
                    'address':,
                    'mile_marker':,
                    'gallons_purchased':,
                    'price_per_gallon':,
                    'leg_cost':,
                },
                ...
            ],
        }
    """
    t_start = time.perf_counter()

    # 1. get the route from ORS
    t_stage = time.perf_counter()
    route = ors_client.get_route(start_coords, finish_coords)
    t_after_ors = time.perf_counter()
    print(f"[PERF] ORS request: {t_after_ors - t_stage:.3f}s")

    total_distance = route['distance_miles']

    # 2. dissect into mile-marker-tagged points
    t_stage = time.perf_counter()
    route_points = dissect_route(route['geometry'])
    t_after_route = time.perf_counter()
    print(f"[PERF] Route processing: {t_after_route - t_stage:.3f}s")

    # 3. filter + project candidate stations
    t_stage = time.perf_counter()
    candidates = filter_candidate_stations(stations, route_points)
    t_after_filter = time.perf_counter()
    print(f"[PERF] Station filtering: {t_after_filter - t_stage:.3f}s")

    # 4. build graph + solve cheapest path
    t_stage = time.perf_counter()
    graph, nodes = build_graph(candidates, total_distance)
    t_after_graph = time.perf_counter()
    print(f"[PERF] Graph construction: {t_after_graph - t_stage:.3f}s")

    t_stage = time.perf_counter()
    path, total_cost = solve_cheapest_path(graph, nodes)
    t_after_optimization = time.perf_counter()
    print(f"[PERF] Optimization: {t_after_optimization - t_stage:.3f}s")

    # 5. walk the path, computing gallons/cost per leg
    nodes_by_id = {n['id']: n for n in nodes}
    fuel_stops = []

    t_stage = time.perf_counter()
    for i in range(len(path) - 1):
        origin_id = path[i]
        dest_id = path[i + 1]
        origin = nodes_by_id[origin_id]

        # find the real_leg_distance for this specific edge from the graph
        leg_distance = next(
            dist for (nid, _w, dist) in graph[origin_id] if nid == dest_id
        )

        # only record a "fuel stop" for actual stations, not START
        if origin_id != 'START':
            gallons = leg_distance / MPG
            price = origin['price']
            fuel_stops.append({
                'station_name': origin['station'].name,
                'address': origin['station'].address,
                'mile_marker': origin['mile_marker'],
                'gallons_purchased': round(gallons, 2),
                'price_per_gallon': price,
                'leg_cost': round(gallons * price, 2),
            })

    t_after_pathcalc = time.perf_counter()
    print(f"[PERF] Path calculation: {t_after_pathcalc - t_stage:.3f}s")

    t_end = time.perf_counter()
    print(f"[PERF] TOTAL (pipeline): {t_end - t_start:.3f}s")

    return {
        'total_distance_miles': round(total_distance, 2),
        'total_fuel_cost': round(total_cost, 2),
        'route_geometry': route['geometry'],
        'fuel_stops': fuel_stops,
    }