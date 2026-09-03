import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

from preprocessing import TrafficPreprocessor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'models')


class TrafficCongestionModel:
    def __init__(self, model_path=None, preprocessor_path=None):
        self.model_path = model_path or os.path.join(MODEL_DIR, 'traffic_model.joblib')
        self.preprocessor_path = preprocessor_path or os.path.join(MODEL_DIR, 'preprocessing.joblib')
        self.model = None
        self.preprocessor = None
        self.metrics = {}
        self.feature_names = []
        self.class_names = []

    def _ensure_model_dir(self):
        os.makedirs(MODEL_DIR, exist_ok=True)

    def train(self, df, target_column=None, numerical_features=None, categorical_features=None):
        if df.empty:
            raise ValueError('Training data is empty.')

        self.preprocessor = TrafficPreprocessor(
            numerical_features=numerical_features,
            categorical_features=categorical_features,
            target_column=target_column
        )

        X_train, X_test, y_train, y_test, artifact = self.preprocessor.fit(
            df,
            target_column=target_column,
            numerical_features=numerical_features,
            categorical_features=categorical_features
        )

        self.model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        self.model.fit(X_train, y_train)
        self.feature_names = list(artifact['feature_columns'])
        self.class_names = sorted(y_train.unique().tolist())

        predictions = self.model.predict(X_test)
        metrics = self.evaluate(y_test, predictions)
        self.metrics = metrics
        self.preprocessor.save(self.preprocessor_path)
        self.save()
        return metrics

    def evaluate(self, y_true, y_pred):
        if self.model is None:
            raise ValueError('Model is not trained yet.')

        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, average='macro', zero_division=0)
        recall = recall_score(y_true, y_pred, average='macro', zero_division=0)
        f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
        weighted_f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        cm = confusion_matrix(y_true, y_pred, labels=self.model.classes_)
        report = classification_report(y_true, y_pred, labels=self.model.classes_, output_dict=True, zero_division=0)

        metrics = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'macro_f1': float(f1),
            'weighted_f1': float(weighted_f1),
            'confusion_matrix': cm.tolist(),
            'classification_report': report,
            'classes': self.model.classes_.tolist(),
            'feature_importance': {feature: float(value) for feature, value in zip(self.feature_names, self.model.feature_importances_)}
        }
        self.metrics = metrics
        return metrics

    def predict(self, input_data):
        if self.model is None or self.preprocessor is None:
            raise ValueError('Model is not trained yet. Please train the model first.')

        if isinstance(input_data, dict):
            input_df = pd.DataFrame([input_data])
        elif isinstance(input_data, pd.DataFrame):
            input_df = input_data.copy()
        else:
            raise TypeError('Input data must be a dictionary or pandas DataFrame.')

        transformed = self.preprocessor.transform(input_df)
        prediction = self.model.predict(transformed)
        return prediction[0]

    def predict_proba(self, input_data):
        if self.model is None or self.preprocessor is None:
            raise ValueError('Model is not trained yet. Please train the model first.')

        if isinstance(input_data, dict):
            input_df = pd.DataFrame([input_data])
        elif isinstance(input_data, pd.DataFrame):
            input_df = input_data.copy()
        else:
            raise TypeError('Input data must be a dictionary or pandas DataFrame.')

        transformed = self.preprocessor.transform(input_df)
        return self.model.predict_proba(transformed)[0]

    def save(self):
        self._ensure_model_dir()
        payload = {
            'model': self.model,
            'preprocessor': self.preprocessor,
            'metrics': self.metrics,
            'feature_names': self.feature_names,
            'class_names': self.class_names,
        }
        joblib.dump(payload, self.model_path)
        return self.model_path

    def load(self, path=None):
        load_path = path or self.model_path
        if not os.path.exists(load_path):
            raise FileNotFoundError(f'Model file not found: {load_path}')

        payload = joblib.load(load_path)
        self.model = payload.get('model')
        self.preprocessor = payload.get('preprocessor')
        self.metrics = payload.get('metrics', {})
        self.feature_names = payload.get('feature_names', [])
        self.class_names = payload.get('class_names', [])
        return self

    def get_feature_importance(self):
        if self.model is None:
            raise ValueError('Model is not trained yet.')
        return {feature: float(value) for feature, value in zip(self.feature_names, self.model.feature_importances_)}


if __name__ == '__main__':
    import pandas as pd
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'traffic_data.csv')
    df = pd.read_csv(csv_path)
    model = TrafficCongestionModel()
    model.train(df)
    print(model.metrics)
