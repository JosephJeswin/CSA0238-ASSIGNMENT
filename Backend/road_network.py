import copy
from collections import defaultdict

CONGESTION_FACTORS = {
    'Free-flow': 1.0,
    'Moderate': 1.4,
    'Heavy': 2.2,
    'Gridlock': 4.5,
}

JUNCTIONS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']

DEFAULT_SEGMENTS = [
    {'source': 'A', 'destination': 'B', 'distance_km': 8, 'base_time': 10},
    {'source': 'A', 'destination': 'D', 'distance_km': 10, 'base_time': 12},
    {'source': 'B', 'destination': 'C', 'distance_km': 7, 'base_time': 9},
    {'source': 'B', 'destination': 'E', 'distance_km': 11, 'base_time': 14},
    {'source': 'C', 'destination': 'F', 'distance_km': 9, 'base_time': 12},
    {'source': 'D', 'destination': 'E', 'distance_km': 7, 'base_time': 9},
    {'source': 'D', 'destination': 'G', 'distance_km': 8, 'base_time': 10},
    {'source': 'E', 'destination': 'F', 'distance_km': 6, 'base_time': 8},
    {'source': 'E', 'destination': 'H', 'distance_km': 9, 'base_time': 12},
    {'source': 'F', 'destination': 'I', 'distance_km': 10, 'base_time': 13},
    {'source': 'H', 'destination': 'I', 'distance_km': 7, 'base_time': 9},
    {'source': 'G', 'destination': 'I', 'distance_km': 12, 'base_time': 15},
]

SCENARIO_MODIFIERS = {
    'Normal': {},
    'Morning Rush Hour': {
        ('A', 'B'): 'Moderate',
        ('B', 'E'): 'Heavy',
        ('D', 'E'): 'Moderate',
        ('F', 'I'): 'Moderate',
    },
    'Accident Incident': {
        ('E', 'H'): 'Gridlock',
        ('H', 'E'): 'Gridlock',
        ('A', 'B'): 'Moderate',
    },
    'Bad Weather Storm': {
        ('B', 'E'): 'Heavy',
        ('D', 'E'): 'Heavy',
        ('E', 'F'): 'Moderate',
        ('H', 'I'): 'Heavy',
    },
}


def build_scenario_edges(scenario_name='Normal'):
    scenario = (scenario_name or 'Normal').strip()
    edges = []
    for segment in DEFAULT_SEGMENTS:
        source = segment['source']
        destination = segment['destination']
        pair = (source, destination)
        reverse_pair = (destination, source)
        congestion = 'Free-flow'
        if pair in SCENARIO_MODIFIERS.get(scenario, {}):
            congestion = SCENARIO_MODIFIERS[scenario][pair]
        elif reverse_pair in SCENARIO_MODIFIERS.get(scenario, {}):
            congestion = SCENARIO_MODIFIERS[scenario][reverse_pair]

        factor = CONGESTION_FACTORS.get(congestion, 1.0)
        effective_cost = segment['base_time'] * factor
        edges.append({
            'source': source,
            'destination': destination,
            'distance_km': segment['distance_km'],
            'base_time': segment['base_time'],
            'congestion_level': congestion,
            'effective_cost': float(effective_cost),
        })

    bidirectional_edges = []
    for edge in edges:
        bidirectional_edges.append(edge)
        reverse_edge = {
            'source': edge['destination'],
            'destination': edge['source'],
            'distance_km': edge['distance_km'],
            'base_time': edge['base_time'],
            'congestion_level': edge['congestion_level'],
            'effective_cost': float(edge['effective_cost']),
        }
        bidirectional_edges.append(reverse_edge)
    return bidirectional_edges


def build_adjacency(edges):
    adjacency = defaultdict(list)
    edge_lookup = {}
    for edge in edges:
        adjacency[edge['source']].append(edge['destination'])
        edge_lookup[(edge['source'], edge['destination'])] = edge
    return adjacency, edge_lookup


def route_distance(route, edge_lookup):
    total_distance = 0.0
    for i in range(len(route) - 1):
        current = route[i]
        nxt = route[i + 1]
        edge = edge_lookup.get((current, nxt))
        if edge is None:
            reverse_edge = edge_lookup.get((nxt, current))
            if reverse_edge is None:
                raise ValueError(f'Missing edge for {current} -> {nxt}')
            total_distance += reverse_edge['distance_km']
        else:
            total_distance += edge['distance_km']
    return float(total_distance)


def route_cost(route, edge_lookup):
    total_cost = 0.0
    total_time = 0.0
    for i in range(len(route) - 1):
        current = route[i]
        nxt = route[i + 1]
        edge = edge_lookup.get((current, nxt))
        if edge is None:
            reverse_edge = edge_lookup.get((nxt, current))
            if reverse_edge is None:
                raise ValueError(f'Missing edge for {current} -> {nxt}')
            total_cost += reverse_edge['effective_cost']
            total_time += reverse_edge['base_time'] * CONGESTION_FACTORS.get(reverse_edge['congestion_level'], 1.0)
        else:
            total_cost += edge['effective_cost']
            total_time += edge['base_time'] * CONGESTION_FACTORS.get(edge['congestion_level'], 1.0)
    return float(total_cost), float(total_time)


def shortest_distance_route(source, destination, edges):
    graph = defaultdict(list)
    for edge in edges:
        graph[edge['source']].append((edge['destination'], edge['distance_km']))

    distances = {node: float('inf') for node in JUNCTIONS}
    previous = {node: None for node in JUNCTIONS}
    distances[source] = 0
    visited = set()

    while True:
        current = None
        current_distance = float('inf')
        for node, distance in distances.items():
            if node not in visited and distance < current_distance:
                current = node
                current_distance = distance
        if current is None:
            break
        visited.add(current)
        if current == destination:
            break

        for neighbor, weight in graph.get(current, []):
            candidate = distances[current] + weight
            if candidate < distances[neighbor]:
                distances[neighbor] = candidate
                previous[neighbor] = current

    if distances.get(destination, float('inf')) == float('inf'):
        return [], float('inf')

    route = []
    cursor = destination
    while cursor is not None:
        route.append(cursor)
        cursor = previous.get(cursor)
    route.reverse()
    return route, distances[destination]


if __name__ == '__main__':
    edges = build_scenario_edges('Normal')
    print(edges[:5])
