MAX_RANGE_MILES = 500
MPG = 10
TANK_CAPACITY_GALLONS = 50


def build_graph(candidates, total_distance):
    """
    candidates: output of filter_candidate_stations()
    total_distance: total route distance in miles (from ORS)

    Returns: dict adjacency list:
        { node_id: [ (neighbor_id, weight_dollars, real_leg_distance), ... ] }

    Nodes: 'START' (marker=0), 'FINISH' (marker=total_distance), and
    each station indexed by position in the sorted candidate list.
    """
    # sort stations by mile_marker so we can do a forward-only sliding window
    sorted_candidates = sorted(candidates, key=lambda c: c['mile_marker'])

    nodes = [{'id': 'START', 'mile_marker': 0, 'price': None}]
    for i, c in enumerate(sorted_candidates):
        nodes.append({
            'id': i,
            'mile_marker': c['mile_marker'],
            'detour_distance': c['detour_distance'],
            'price': float(c['station'].price),
            'station': c['station'],
        })
    nodes.append({'id': 'FINISH', 'mile_marker': total_distance, 'price': None})

    graph = {n['id']: [] for n in nodes}

    for i, origin in enumerate(nodes):
        for dest in nodes[i + 1:]:
            gap = dest['mile_marker'] - origin['mile_marker']

            # real_leg_distance = straight route gap + detour cost of
            # leaving the route to reach origin's station and dest's station
            origin_detour = origin.get('detour_distance', 0) or 0
            dest_detour = dest.get('detour_distance', 0) or 0
            real_leg_distance = gap + origin_detour + dest_detour

            if real_leg_distance > MAX_RANGE_MILES:
                # sliding window: once unreachable, everything farther
                # is also unreachable (nodes are sorted by mile_marker)
                break

            # START's outgoing edges are free — fuel already in tank
            if origin['id'] == 'START':
                weight = 0
            else:
                gallons_needed = real_leg_distance / MPG
                weight = gallons_needed * origin['price']

            graph[origin['id']].append((dest['id'], weight, real_leg_distance))

    return graph, nodes


def solve_cheapest_path(graph, nodes):
    """
    DP forward pass in mile_marker order (graph is a DAG, so this is
    equivalent to Dijkstra but needs less machinery).

    Returns: (path, total_cost) where path is an ordered list of node ids
    from START to FINISH. Raises ValueError if FINISH is unreachable.
    """
    # nodes are already in mile_marker order (START ... FINISH)
    ordered_ids = [n['id'] for n in nodes]

    best_cost = {node_id: float('inf') for node_id in ordered_ids}
    best_cost['START'] = 0
    came_from = {}

    for node_id in ordered_ids:
        if best_cost[node_id] == float('inf'):
            continue  # unreachable so far, skip
        for neighbor_id, weight, _ in graph[node_id]:
            new_cost = best_cost[node_id] + weight
            if new_cost < best_cost[neighbor_id]:
                best_cost[neighbor_id] = new_cost
                came_from[neighbor_id] = node_id

    if best_cost['FINISH'] == float('inf'):
        raise ValueError("No feasible route: a gap between reachable stations exceeds 500 miles.")

    # walk back from FINISH to START
    path = ['FINISH']
    while path[-1] != 'START':
        path.append(came_from[path[-1]])
    path.reverse()

    return path, best_cost['FINISH']