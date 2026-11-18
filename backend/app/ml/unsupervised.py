"""Unsupervised learning helpers."""

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def _split_features(df):
    X = df.copy()
    numeric = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical = X.select_dtypes(exclude=[np.number]).columns.tolist()
    return X, numeric, categorical


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


def run_clustering(df, algorithm, params=None, random_state=42):
    params = dict(params or {})
    X, numeric, categorical = _split_features(df)
    pre = _preprocessor(numeric, categorical)
    X_t = pre.fit_transform(X)

    if algorithm == "kmeans":
        n_clusters = int(params.pop("n_clusters", 3))
        model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10, **params)
    elif algorithm == "dbscan":
        model = DBSCAN(**params)
    else:
        raise ValueError(f"Unknown clustering algorithm: {algorithm}")

    labels = model.fit_predict(X_t)

    metrics = {"n_samples": int(len(X))}
    unique = set(labels.tolist()) if hasattr(labels, "tolist") else set(labels)
    unique.discard(-1)
    metrics["n_clusters"] = int(len(unique))
    if len(unique) > 1:
        try:
            metrics["silhouette"] = float(silhouette_score(X_t, labels))
        except Exception:
            metrics["silhouette"] = None
    else:
        metrics["silhouette"] = None

    model.preprocessor_ = pre
    model.feature_names_in_ = list(X.columns)
    return model, labels, metrics


def run_pca(df, params=None, random_state=42):
    params = dict(params or {})
    X, numeric, categorical = _split_features(df)
    pre = _preprocessor(numeric, categorical)
    X_t = pre.fit_transform(X)

    n_components = params.pop("n_components", None)
    if n_components is None:
        n_components = min(X_t.shape[1], X_t.shape[0])
    model = PCA(n_components=n_components, random_state=random_state, **params)
    transformed = model.fit_transform(X_t)

    metrics = {
        "n_components": int(model.n_components_),
        "explained_variance_ratio": [float(v) for v in model.explained_variance_ratio_],
        "total_explained_variance": float(model.explained_variance_ratio_.sum()),
        "n_samples": int(len(X)),
    }
    model.preprocessor_ = pre
    return model, transformed, metrics
