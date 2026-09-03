import json
import os
import sys
from datetime import datetime

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from aco import optimize_route
from database import log_prediction, log_route_query
from ml_model import TrafficCongestionModel
from preprocessing import TrafficPreprocessor
from road_network import JUNCTIONS, build_adjacency, build_scenario_edges, shortest_distance_route, route_distance, route_cost

DATASET_PATH = os.path.join(BASE_DIR, 'data', 'traffic_data.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'traffic_model.joblib')
MODEL = TrafficCongestionModel(model_path=MODEL_PATH)

app = Flask(__name__)
CORS(app)


def is_model_available():
    return os.path.exists(MODEL_PATH)


def ensure_dataset_exists():
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f'Dataset file is missing: {DATASET_PATH}')


def get_dataset_summary():
    ensure_dataset_exists()
    df = pd.read_csv(DATASET_PATH)
    auto = TrafficPreprocessor.detect_dataset_columns(df)
    summary = {
        'rows': int(df.shape[0]),
        'columns': int(df.shape[1]),
        'missing_values': df.isnull().sum().to_dict(),
        'duplicate_count': int(df.duplicated().sum()),
        'target_column': auto.get('target_column'),
        'target_classes': [],
        'class_distribution': {}
    }
    if auto.get('target_column'):
        target_series = df[auto['target_column']].astype(str)
        summary['target_classes'] = sorted(target_series.unique().tolist())
        summary['class_distribution'] = target_series.value_counts().to_dict()
    return summary


def train_model():
    ensure_dataset_exists()
    df = pd.read_csv(DATASET_PATH)
    model = TrafficCongestionModel(model_path=MODEL_PATH)
    metrics = model.train(df)
    global MODEL
    MODEL = model
    return metrics


def auto_train_model_if_needed():
    if not os.path.exists(DATASET_PATH):
        return MODEL
    if os.path.exists(MODEL_PATH):
        try:
            MODEL.load(MODEL_PATH)
            return MODEL
        except FileNotFoundError:
            pass
    try:
        train_model()
    except Exception:
        pass
    return MODEL


MODEL = auto_train_model_if_needed()


def predict_congestion(payload):
    if MODEL.model is None or MODEL.preprocessor is None:
        raise ValueError('Model is not trained yet. Train the model before making predictions.')

    if not isinstance(payload, dict):
        raise ValueError('Prediction payload must be a JSON object.')

    required_fields = list(MODEL.preprocessor.numerical_features) + list(MODEL.preprocessor.categorical_features)
    missing = [field for field in required_fields if field not in payload or payload[field] in [None, '']]
    if missing:
        raise ValueError(f'Missing required prediction fields: {missing}')

    try:
        input_df = pd.DataFrame([payload])
        for col in MODEL.preprocessor.numerical_features:
            if col in input_df.columns:
                input_df[col] = pd.to_numeric(input_df[col], errors='raise')
        prediction = MODEL.predict(input_df)
        probabilities = MODEL.predict_proba(input_df)
        class_names = MODEL.model.classes_
        confidence = float(max(probabilities))
        probability_dict = {str(label): float(prob) for label, prob in zip(class_names, probabilities)}
        result = {
            'predicted_class': str(prediction),
            'confidence': confidence,
            'probabilities': probability_dict,
        }
        log_prediction(payload, result['predicted_class'], result['confidence'])
        return result
    except Exception as exc:
        raise ValueError(f'Unable to predict congestion: {str(exc)}')


def validate_route_inputs(source, destination, scenario, params):
    if not source or not destination:
        raise ValueError('Source and destination are required.')
    if source == destination:
        raise ValueError('Source and destination must be different.')
    if scenario not in {'Normal', 'Morning Rush Hour', 'Accident Incident', 'Bad Weather Storm'}:
        raise ValueError('Scenario must be one of: Normal, Morning Rush Hour, Accident Incident, Bad Weather Storm.')
    if params is None:
        params = {}
    if 'number_of_ants' in params and (not isinstance(params['number_of_ants'], int) or params['number_of_ants'] <= 0):
        raise ValueError('number_of_ants must be a positive integer.')
    if 'number_of_iterations' in params and (not isinstance(params['number_of_iterations'], int) or params['number_of_iterations'] <= 0):
        raise ValueError('number_of_iterations must be a positive integer.')
    return params


def solve_route(source, destination, scenario='Normal', params=None):
    params = validate_route_inputs(source, destination, scenario, params)
    graph_edges = build_scenario_edges(scenario)
    adjacency, edge_lookup = build_adjacency(graph_edges)
    if source not in adjacency or destination not in adjacency:
        raise ValueError(f'Invalid route: {source} to {destination} is unreachable in the graph.')

    aco_result = optimize_route(source, destination, scenario=scenario, params=params)
    route = aco_result['route']
    if not route or route[-1] != destination:
        raise ValueError(f'No valid route found from {source} to {destination}.')

    distance = route_distance(route, edge_lookup)
    total_cost, total_time = route_cost(route, edge_lookup)
    route_response = {
        'route': route,
        'total_distance': float(distance),
        'total_cost': float(total_cost),
        'estimated_time': float(total_time),
        'iterations': aco_result['iteration_count'],
        'convergence': aco_result['trace'][-1] if aco_result.get('trace') else {},
        'trace': aco_result['trace'],
    }
    log_route_query(source, destination, scenario, route, distance, total_cost)
    return route_response


def compare_routes(source, destination, scenario='Normal', params=None):
    params = params or {}
    first = shortest_distance_route(source, destination, build_scenario_edges(scenario))
    if not first[0]:
        raise ValueError(f'No valid shortest-distance route from {source} to {destination}.')

    distance_route, distance_distance = first
    distance_cost, distance_time = route_cost(distance_route, build_adjacency(build_scenario_edges(scenario))[1])
    aco_route_response = solve_route(source, destination, scenario=scenario, params=params)
    aco_route = aco_route_response['route']
    aco_distance = route_distance(aco_route, build_adjacency(build_scenario_edges(scenario))[1])
    aco_cost, aco_time = route_cost(aco_route, build_adjacency(build_scenario_edges(scenario))[1])

    return {
        'distance_only': {
            'route': distance_route,
            'distance': float(distance_distance),
            'cost': float(distance_cost),
            'time': float(distance_time),
        },
        'traffic_aware': {
            'route': aco_route,
            'distance': float(aco_distance),
            'cost': float(aco_cost),
            'time': float(aco_time),
        },
        'time_saving': float(max(0.0, distance_time - aco_time)),
        'extra_distance': float(max(0.0, aco_distance - distance_distance)),
        'avoided_congested_road': 'Yes' if aco_route != distance_route else 'No',
    }


@app.route('/api/health', methods=['GET'])
def health_check():
    status = {
        'backend_status': 'running',
        'model_available': is_model_available(),
        'dataset_available': os.path.exists(DATASET_PATH),
        'timestamp': datetime.utcnow().isoformat(),
    }
    return jsonify(status)


@app.route('/api/dataset/summary', methods=['GET'])
def dataset_summary():
    try:
        return jsonify(get_dataset_summary())
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400


@app.route('/api/dataset/records', methods=['GET'])
def dataset_records():
    try:
        ensure_dataset_exists()
        df = pd.read_csv(DATASET_PATH)
        return jsonify(df.head(20).to_dict(orient='records'))
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400


@app.route('/api/model/train', methods=['POST'])
def train_endpoint():
    try:
        metrics = train_model()
        return jsonify({'status': 'trained', 'metrics': metrics})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400


@app.route('/api/model/metrics', methods=['GET'])
def model_metrics():
    if not is_model_available():
        return jsonify({'error': 'Model is not trained yet. Please call /api/model/train first.'}), 400
    return jsonify(MODEL.metrics)


@app.route('/api/predict', methods=['POST'])
def predict_endpoint():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({'error': 'JSON request body is required.'}), 400
    try:
        result = predict_congestion(payload)
        return jsonify(result)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400


@app.route('/api/route', methods=['POST'])
def route_endpoint():
    payload = request.get_json(silent=True) or {}
    source = payload.get('source')
    destination = payload.get('destination')
    scenario = payload.get('scenario', 'Normal')
    params = payload.get('aco_parameters', {})
    try:
        result = solve_route(source, destination, scenario=scenario, params=params)
        return jsonify(result)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400


@app.route('/api/route/compare', methods=['POST'])
def route_compare_endpoint():
    payload = request.get_json(silent=True) or {}
    source = payload.get('source')
    destination = payload.get('destination')
    scenario = payload.get('scenario', 'Normal')
    params = payload.get('aco_parameters', {})
    try:
        result = compare_routes(source, destination, scenario=scenario, params=params)
        return jsonify(result)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400


@app.route('/api/graph', methods=['GET'])
def graph_data():
    scenario = request.args.get('scenario', 'Normal')
    edges = build_scenario_edges(scenario)
    adjacency, edge_lookup = build_adjacency(edges)
    return jsonify({
        'nodes': JUNCTIONS,
        'edges': edges,
        'adjacency': {k: list(v) for k, v in adjacency.items()},
        'scenario': scenario,
    })


@app.route('/api/aco/trace', methods=['GET'])

def aco_trace():
    try:
        scenario = request.args.get('scenario', 'Normal')
        source = request.args.get('source', 'A')
        destination = request.args.get('destination', 'I')
        params = {
            'number_of_ants': int(request.args.get('number_of_ants', 20)),
            'number_of_iterations': int(request.args.get('number_of_iterations', 50)),
            'alpha': float(request.args.get('alpha', 1.0)),
            'beta': float(request.args.get('beta', 2.0)),
            'evaporation_rate': float(request.args.get('evaporation_rate', 0.5)),
            'pheromone_constant': float(request.args.get('pheromone_constant', 100)),
        }
        result = solve_route(source, destination, scenario=scenario, params=params)
        return jsonify({'trace': result.get('trace', [])})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400


@app.route('/api/export/report', methods=['GET'])
def export_report():
    try:
        summary = get_dataset_summary()
        metrics = MODEL.metrics if is_model_available() else {}
        report = {
            'dataset_summary': summary,
            'model_metrics': metrics,
            'generated_at': datetime.utcnow().isoformat(),
            'backend_status': 'running',
        }
        return jsonify(report)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
