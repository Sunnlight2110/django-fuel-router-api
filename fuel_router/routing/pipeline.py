from . import utils as ors_client
from .geo import dissect_route
from .candidates import filter_candidate_stations
from .graph import build_graph, solve_cheapest_path, MPG


def compute_route_and_fuel_stops(start_coords, finish_coords, stations):
    """
    start_coords, finish_coords: (longitude, latitude) tuples, as ORS expects
    stations: queryset/list of FuelStation objects to consider


    """
    # 1. get the route from ORS
    route = ors_client.get_route(start_coords, finish_coords)

    total_distance = route['distance_miles']

    # 2. dissect into mile-marker-tagged points
    route_points = dissect_route(route['geometry'])

    # 3. filter + project candidate stations
    candidates = filter_candidate_stations(stations, route_points)

    # 4. build graph + solve cheapest path
    graph, nodes = build_graph(candidates, total_distance)

    path, total_cost = solve_cheapest_path(graph, nodes)

    # 5. walk the path, computing gallons/cost per leg
    nodes_by_id = {n['id']: n for n in nodes}
    fuel_stops = []

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

    

    return {
        'total_distance_miles': round(total_distance, 2),
        'total_fuel_cost': round(total_cost, 2),
        'route_geometry': route['geometry'],
        'fuel_stops': fuel_stops,
    }