import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODEL_DIR = os.path.join(BASE_DIR, 'models')


class TrafficPreprocessor:
    def __init__(self, numerical_features=None, categorical_features=None, target_column=None):
        self.numerical_features = numerical_features or []
        self.categorical_features = categorical_features or []
        self.target_column = target_column
        self.feature_columns = []
        self.scaler = StandardScaler()
        self.is_fitted = False

    @staticmethod
    def get_dataset_path(filename='traffic_data.csv'):
        path = os.path.join(DATA_DIR, filename)
        return path

    @staticmethod
    def detect_dataset_columns(df):
        lower_cols = [str(col).lower() for col in df.columns]

        numerical_keywords = (
            'speed', 'vehicle', 'density', 'occupancy', 'delay', 'flow', 'queue',
            'acceleration', 'traffic'
        )
        categorical_keywords = (
            'weather', 'time', 'road', 'incident', 'signal', 'environment'
        )
        target_keywords = ('congestion_level', 'congestion', 'label', 'target')

        numerical_features = []
        categorical_features = []
        target_column = None

        for column in df.columns:
            name = str(column).lower()
            if any(keyword in name for keyword in target_keywords):
                target_column = column
                continue
            if any(keyword in name for keyword in numerical_keywords):
                numerical_features.append(column)
                continue
            if any(keyword in name for keyword in categorical_keywords):
                categorical_features.append(column)

        if target_column is None:
            for column in df.columns:
                name = str(column).lower()
                if 'class' in name or 'level' in name:
                    target_column = column
                    break

        return {
            'numerical_features': numerical_features,
            'categorical_features': categorical_features,
            'target_column': target_column,
        }

    @staticmethod
    def inspect_dataset(csv_path):
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Dataset not found: {csv_path}")

        df = pd.read_csv(csv_path)
        duplicate_count = int(df.duplicated().sum())
        missing_values = df.isnull().sum().to_dict()
        summary = {
            'filename': os.path.basename(csv_path),
            'rows': int(df.shape[0]),
            'columns': int(df.shape[1]),
            'column_names': list(df.columns),
            'missing_values': missing_values,
            'duplicate_records': duplicate_count,
            'target_column': None,
            'target_classes': [],
            'class_distribution': {}
        }

        auto_detect = TrafficPreprocessor.detect_dataset_columns(df)
        summary['target_column'] = auto_detect['target_column']

        if auto_detect['target_column']:
            y = df[auto_detect['target_column']]
            summary['target_classes'] = sorted(y.dropna().astype(str).unique().tolist())
            summary['class_distribution'] = y.fillna('Missing').astype(str).value_counts().to_dict()

        return df, summary

    def fit(self, df, target_column=None, numerical_features=None, categorical_features=None, test_size=0.2):
        if df.empty:
            raise ValueError('Dataset is empty. Please provide a valid traffic dataset.')

        if target_column is None:
            detected = self.detect_dataset_columns(df)
            target_column = detected['target_column']
            numerical_features = numerical_features or detected['numerical_features']
            categorical_features = categorical_features or detected['categorical_features']

        if target_column is None or target_column not in df.columns:
            raise ValueError(
                'A target column such as congestion_level, Congestion_Level, congestion, label or target is required.'
            )

        self.target_column = target_column
        self.numerical_features = numerical_features or [
            col for col in df.columns if pd.api.types.is_numeric_dtype(df[col]) and col != target_column
        ]
        self.categorical_features = categorical_features or [
            col for col in df.columns if col not in self.numerical_features and col != target_column
        ]

        feature_frame = df.copy()
        median_values = {}
        mode_values = {}
        for col in self.numerical_features:
            if col not in feature_frame.columns:
                continue
            feature_frame[col] = pd.to_numeric(feature_frame[col], errors='coerce')
            median_value = feature_frame[col].median()
            median_values[col] = median_value
            feature_frame[col] = feature_frame[col].fillna(median_value)

        for col in self.categorical_features:
            if col not in feature_frame.columns:
                continue
            mode_value = feature_frame[col].mode().iloc[0] if not feature_frame[col].mode().empty else 'Unknown'
            mode_values[col] = mode_value
            feature_frame[col] = feature_frame[col].fillna(mode_value)
            feature_frame[col] = feature_frame[col].astype(str)

        if not self.numerical_features and not self.categorical_features:
            raise ValueError('No usable features were identified in the dataset.')

        feature_columns = list(self.numerical_features) + list(self.categorical_features)
        X = feature_frame[feature_columns].copy()
        y = feature_frame[target_column].astype(str)

        X_encoded = pd.get_dummies(X, columns=self.categorical_features, dummy_na=False)
        self.feature_columns = list(X_encoded.columns)

        X_train, X_test, y_train, y_test = train_test_split(
            X_encoded,
            y,
            test_size=test_size,
            random_state=42,
            stratify=y
        )

        self.scaler.fit(X_train)
        X_train_scaled = self.scaler.transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        self.is_fitted = True
        self.artifact = {
            'numerical_features': self.numerical_features,
            'categorical_features': self.categorical_features,
            'target_column': self.target_column,
            'feature_columns': self.feature_columns,
            'scaler': self.scaler,
            'median_values': median_values,
            'mode_values': mode_values,
            'classes': sorted(y.unique().tolist())
        }

        return X_train_scaled, X_test_scaled, y_train, y_test, self.artifact

    def transform(self, df):
        if not self.is_fitted:
            raise ValueError('The preprocessor must be fitted before transforming new data.')

        new_df = df.copy()
        for col in self.numerical_features:
            if col in new_df.columns:
                new_df[col] = pd.to_numeric(new_df[col], errors='coerce')
                median_value = self.artifact.get('median_values', {}).get(col)
                if median_value is not None:
                    new_df[col] = new_df[col].fillna(median_value)

        for col in self.categorical_features:
            if col in new_df.columns:
                mode_value = self.artifact.get('mode_values', {}).get(col, 'Unknown')
                new_df[col] = new_df[col].fillna(mode_value)
                new_df[col] = new_df[col].astype(str)

        selected_columns = [col for col in self.feature_columns if col in new_df.columns]
        transformed = new_df[selected_columns].copy() if selected_columns else new_df.copy()
        if self.categorical_features:
            transformed = pd.get_dummies(transformed, columns=[col for col in self.categorical_features if col in transformed.columns], dummy_na=False)
        for column in self.feature_columns:
            if column not in transformed.columns:
                transformed[column] = 0
        transformed = transformed[self.feature_columns]
        return self.scaler.transform(transformed)

    def save(self, path=None):
        if path is None:
            os.makedirs(MODEL_DIR, exist_ok=True)
            path = os.path.join(MODEL_DIR, 'preprocessing.joblib')
        joblib.dump(self.artifact, path)
        return path

    @staticmethod
    def load(path=None):
        if path is None:
            path = os.path.join(MODEL_DIR, 'preprocessing.joblib')
        if not os.path.exists(path):
            raise FileNotFoundError(f'Preprocessing artifact not found: {path}')
        artifact = joblib.load(path)
        preprocessor = TrafficPreprocessor(
            numerical_features=artifact.get('numerical_features', []),
            categorical_features=artifact.get('categorical_features', []),
            target_column=artifact.get('target_column')
        )
        preprocessor.feature_columns = artifact.get('feature_columns', [])
        preprocessor.scaler = artifact.get('scaler', StandardScaler())
        preprocessor.artifact = artifact
        preprocessor.is_fitted = True
        return preprocessor

    def prepare_for_training(self, df, target_column=None):
        if target_column is None:
            target_column = self.target_column
        detected = self.detect_dataset_columns(df) if target_column is None else {'numerical_features': self.numerical_features, 'categorical_features': self.categorical_features, 'target_column': target_column}
        if target_column is None:
            raise ValueError('A valid target column is required before training.')
        numerical_features = self.numerical_features or detected['numerical_features']
        categorical_features = self.categorical_features or detected['categorical_features']
        return self.fit(df, target_column=target_column, numerical_features=numerical_features, categorical_features=categorical_features)


if __name__ == '__main__':
    csv_path = os.path.join(DATA_DIR, 'traffic_data.csv')
    df, summary = TrafficPreprocessor.inspect_dataset(csv_path)
    print('Dataset summary:', summary)
