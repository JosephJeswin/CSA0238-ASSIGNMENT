import os
import sys
import unittest

import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from aco import optimize_route
from app import get_dataset_summary, predict_congestion, solve_route, compare_routes, MODEL
from database import initialize_database
from preprocessing import TrafficPreprocessor


class TrafficProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset_path = os.path.join(BASE_DIR, 'data', 'traffic_data.csv')
        initialize_database()

    def test_valid_congestion_prediction(self):
        df = pd.read_csv(self.dataset_path)
        detector = TrafficPreprocessor.detect_dataset_columns(df)
        self.assertIsNotNone(detector['target_column'])
        payload = {
            'speed_kph': 58,
            'vehicle_count': 220,
            'traffic_density': 0.41,
            'road_occupancy': 0.28,
            'average_delay_sec': 18,
            'traffic_flow': 980,
            'queue_length': 12,
            'acceleration': 0.8,
            'weather_condition': 'Clear',
            'time_period': 'Morning',
            'road_type': 'Highway',
            'incident_status': 'None',
            'signal_timing': 'Adaptive',
            'environment_type': 'Urban',
        }
        result = predict_congestion(payload)
        self.assertIn('predicted_class', result)
        self.assertIn('confidence', result)
        self.assertIn('probabilities', result)

    def test_missing_prediction_input(self):
        with self.assertRaises(ValueError):
            predict_congestion({'speed_kph': 50})

    def test_valid_aco_route(self):
        result = optimize_route('A', 'I', 'Normal')
        self.assertIn('route', result)
        self.assertTrue(result['route'][0] == 'A')
        self.assertTrue(result['route'][-1] == 'I')
        self.assertGreater(result['cost'], 0)

    def test_same_source_and_destination(self):
        with self.assertRaises(ValueError):
            solve_route('A', 'A', 'Normal')

    def test_unreachable_destination(self):
        with self.assertRaises(ValueError):
            solve_route('A', 'Z', 'Normal')

    def test_congested_route_vs_alternative_route(self):
        comparison = compare_routes('A', 'I', 'Accident Incident')
        self.assertIn('distance_only', comparison)
        self.assertIn('traffic_aware', comparison)
        self.assertIn('time_saving', comparison)

    def test_missing_dataset(self):
        if os.path.exists(self.dataset_path):
            self.assertTrue(os.path.exists(self.dataset_path))

    def test_model_unavailable_before_training(self):
        self.assertIsNotNone(MODEL)

    def test_aco_pheromone_update(self):
        result = optimize_route('A', 'I', 'Normal', params={'number_of_ants': 10, 'number_of_iterations': 5})
        self.assertIn('trace', result)
        self.assertTrue(len(result['trace']) > 0)

    def test_aco_convergence_trace(self):
        result = optimize_route('A', 'I', 'Accident Incident', params={'number_of_ants': 12, 'number_of_iterations': 10})
        trace = result['trace']
        self.assertTrue(len(trace) > 0)
        self.assertIn('best_route', trace[0])
        self.assertIn('best_route_cost', trace[0])


if __name__ == '__main__':
    unittest.main()
