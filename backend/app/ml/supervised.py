"""Supervised learning helpers."""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def _split(df, target):
    X = df.drop(columns=[target])
    y = df[target]
    numeric = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical = X.select_dtypes(exclude=[np.number]).columns.tolist()
    return X, y, numeric, categorical


def _preprocessor(numeric, categorical):
    num_pipe = Pipeline(
        [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
    )
    cat_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    transformers = []
    if numeric:
        transformers.append(("num", num_pipe, numeric))
    if categorical:
        transformers.append(("cat", cat_pipe, categorical))
    return ColumnTransformer(transformers=transformers, remainder="drop")


def train_classification(df, target, algorithm, test_size=0.2, params=None, random_state=42):
    params = dict(params or {})
    X, y, numeric, categorical = _split(df, target)
    pre = _preprocessor(numeric, categorical)

    if algorithm == "logistic":
        model = LogisticRegression(max_iter=1000, **params)
    elif algorithm == "random_forest":
        n_estimators = params.pop("n_estimators", 100)
        model = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state, **params)
    elif algorithm == "xgboost":
        try:
            from xgboost import XGBClassifier
        except Exception as e:
            raise ValueError("xgboost is not installed") from e
        model = XGBClassifier(random_state=random_state, **params, eval_metric="logloss")
    else:
        raise ValueError(f"Unknown classification algorithm: {algorithm}")

    pipe = Pipeline([("pre", pre), ("clf", model)])

    stratify = y if y.nunique() > 1 and y.value_counts().min() >= 2 else None
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=stratify
        )
    except ValueError:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    avg = "binary" if y.nunique() == 2 else "weighted"
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, average=avg, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, average=avg, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, average=avg, zero_division=0)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }
    return pipe, metrics


def train_regression(df, target, algorithm, test_size=0.2, params=None, random_state=42):
    params = dict(params or {})
    X, y, numeric, categorical = _split(df, target)
    pre = _preprocessor(numeric, categorical)

    if algorithm == "linear":
        model = LinearRegression(**params)
    elif algorithm == "random_forest":
        n_estimators = params.pop("n_estimators", 100)
        model = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state, **params)
    elif algorithm == "xgboost":
        try:
            from xgboost import XGBRegressor
        except Exception as e:
            raise ValueError("xgboost is not installed") from e
        model = XGBRegressor(random_state=random_state, **params)
    else:
        raise ValueError(f"Unknown regression algorithm: {algorithm}")

    pipe = Pipeline([("pre", pre), ("reg", model)])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)

    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    metrics = {
        "rmse": rmse,
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "r2": float(r2_score(y_test, y_pred)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }
    return pipe, metrics
