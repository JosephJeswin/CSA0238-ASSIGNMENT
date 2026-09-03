import json
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'traffic_app.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            input_data TEXT NOT NULL,
            predicted_class TEXT NOT NULL,
            confidence REAL NOT NULL
        )
        '''
    )
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS route_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            scenario TEXT NOT NULL,
            route TEXT NOT NULL,
            distance REAL NOT NULL,
            cost REAL NOT NULL
        )
        '''
    )
    conn.commit()
    conn.close()


def log_prediction(input_data, predicted_class, confidence):
    conn = get_connection()
    cursor = conn.cursor()
    payload = json.dumps(input_data, default=str)
    cursor.execute(
        'INSERT INTO predictions (timestamp, input_data, predicted_class, confidence) VALUES (?, ?, ?, ?)',
        (datetime.utcnow().isoformat(), payload, str(predicted_class), float(confidence))
    )
    conn.commit()
    conn.close()


def log_route_query(source, destination, scenario, route, distance, cost):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO route_queries (timestamp, source, destination, scenario, route, distance, cost) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (
            datetime.utcnow().isoformat(),
            str(source),
            str(destination),
            str(scenario),
            json.dumps(route),
            float(distance),
            float(cost),
        )
    )
    conn.commit()
    conn.close()


initialize_database()
