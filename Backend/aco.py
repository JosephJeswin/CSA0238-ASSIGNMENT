import math
import random
from collections import defaultdict

from road_network import build_scenario_edges, build_adjacency, route_cost


class AntColonyOptimizer:
    def __init__(
        self,
        number_of_ants=20,
        number_of_iterations=50,
        alpha=1.0,
        beta=2.0,
        evaporation_rate=0.5,
        pheromone_constant=100,
        random_state=42,
    ):
        self.number_of_ants = number_of_ants
        self.number_of_iterations = number_of_iterations
        self.alpha = alpha
        self.beta = beta
        self.evaporation_rate = evaporation_rate
        self.pheromone_constant = pheromone_constant
        self.random = random.Random(random_state)
        self.trace = []
        self.best_route = []
        self.best_cost = float('inf')

    def _initialize_pheromones(self, adjacency):
        pheromones = defaultdict(float)
        for node in adjacency:
            for neighbor in adjacency[node]:
                key = (node, neighbor)
                pheromones[key] = 1.0
        return pheromones

    def _heuristic_value(self, edge_cost):
        return 1.0 / max(float(edge_cost), 1e-6)

    def _transition_probability(self, current_node, neighbors, pheromones, edge_costs):
        if not neighbors:
            return []

        weights = []
        for neighbor in neighbors:
            tau = pheromones.get((current_node, neighbor), 1.0)
            eta = self._heuristic_value(edge_costs.get((current_node, neighbor), {}).get('effective_cost', 1.0))
            weights.append((tau ** self.alpha) * (eta ** self.beta))

        total = sum(weights)
        if total == 0:
            return [1.0 / len(neighbors)] * len(neighbors)
        return [weight / total for weight in weights]

    def _route_cost(self, route, edge_lookup):
        if len(route) < 2:
            return float('inf')
        total_cost, total_time = route_cost(route, edge_lookup)
        return total_cost

    def _construct_route(self, source, destination, adjacency, pheromones, edge_lookup):
        route = [source]
        current = source
        visited = {source}

        while current != destination:
            neighbors = adjacency.get(current, [])
            if not neighbors:
                return []

            valid_neighbors = [n for n in neighbors if n not in visited]
            if not valid_neighbors:
                return []

            probabilities = self._transition_probability(current, valid_neighbors, pheromones, edge_lookup)
            next_node = self.random.choices(valid_neighbors, probabilities, k=1)[0]
            route.append(next_node)
            current = next_node
            visited.add(current)

            if len(route) > len(adjacency) + 2:
                return []

        return route

    def _update_pheromones(self, pheromones, ant_routes, edge_lookup):
        for key in list(pheromones.keys()):
            pheromones[key] *= (1.0 - self.evaporation_rate)

        for route in ant_routes:
            cost = self._route_cost(route, edge_lookup)
            if not route or cost == float('inf'):
                continue
            delta = self.pheromone_constant / cost
            for i in range(len(route) - 1):
                start = route[i]
                end = route[i + 1]
                pheromones[(start, end)] += delta

        return pheromones

    def optimize(self, source, destination, scenario='Normal'):
        edges = build_scenario_edges(scenario)
        adjacency, edge_lookup = build_adjacency(edges)
        if source not in adjacency or destination not in adjacency:
            raise ValueError(f'Invalid source or destination. Available nodes: {sorted(adjacency.keys())}')

        pheromones = self._initialize_pheromones(adjacency)
        self.trace = []
        self.best_route = []
        self.best_cost = float('inf')

        for iteration in range(1, self.number_of_iterations + 1):
            candidate_routes = []
            candidate_costs = []
            for _ in range(self.number_of_ants):
                route = self._construct_route(source, destination, adjacency, pheromones, edge_lookup)
                if not route or route[-1] != destination:
                    continue
                cost = self._route_cost(route, edge_lookup)
                if cost == float('inf'):
                    continue
                candidate_routes.append(route)
                candidate_costs.append(cost)

            if not candidate_routes:
                continue

            best_route_in_iteration = min(candidate_routes, key=lambda route: self._route_cost(route, edge_lookup))
            best_cost_in_iteration = self._route_cost(best_route_in_iteration, edge_lookup)
            average_cost = sum(candidate_costs) / len(candidate_costs)

            if best_cost_in_iteration < self.best_cost:
                self.best_cost = best_cost_in_iteration
                self.best_route = best_route_in_iteration

            pheromone_values = list(pheromones.values())
            pheromone_summary = {
                'max': float(max(pheromone_values)) if pheromone_values else 0.0,
                'min': float(min(pheromone_values)) if pheromone_values else 0.0,
                'avg': float(sum(pheromone_values) / len(pheromone_values)) if pheromone_values else 0.0,
            }

            self.trace.append({
                'iteration': iteration,
                'best_route': best_route_in_iteration,
                'best_route_cost': float(best_cost_in_iteration),
                'average_route_cost': float(average_cost),
                'pheromone': pheromone_summary,
            })

            pheromones = self._update_pheromones(pheromones, candidate_routes, edge_lookup)

        if not self.best_route:
            raise ValueError(f'No valid route found from {source} to {destination} for scenario {scenario}.')

        return {
            'route': self.best_route,
            'cost': float(self.best_cost),
            'iteration_count': len(self.trace),
            'trace': self.trace,
        }


def optimize_route(source, destination, scenario='Normal', params=None):
    params = params or {}
    optimizer = AntColonyOptimizer(
        number_of_ants=params.get('number_of_ants', 20),
        number_of_iterations=params.get('number_of_iterations', 50),
        alpha=params.get('alpha', 1.0),
        beta=params.get('beta', 2.0),
        evaporation_rate=params.get('evaporation_rate', 0.5),
        pheromone_constant=params.get('pheromone_constant', 100),
        random_state=42,
    )
    result = optimizer.optimize(source, destination, scenario=scenario)
    return result


if __name__ == '__main__':
    result = optimize_route('A', 'I', 'Accident Incident')
    print(result)
