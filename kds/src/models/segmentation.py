from __future__ import annotations

import numpy as np
import pandas as pd


def build_product_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    feature_df = (
        df.groupby("product_type")
        .agg(
            total_revenue=("sales_amount", "sum"),
            total_quantity=("transaction_qty", "sum"),
            average_price=("unit_price", "mean"),
            average_hour=("hour", "mean"),
        )
        .reset_index()
    )

    weekend_share = (
        df.groupby("product_type")["is_weekend"]
        .mean()
        .reset_index(name="weekend_share")
    )
    feature_df = feature_df.merge(weekend_share, on="product_type", how="left")
    return feature_df


def _standardize_features(feature_df: pd.DataFrame, feature_columns: list[str]) -> np.ndarray:
    matrix = feature_df[feature_columns].astype(float).to_numpy()
    means = matrix.mean(axis=0)
    stds = matrix.std(axis=0)
    stds[stds == 0] = 1.0
    return (matrix - means) / stds


def _simple_kmeans(matrix: np.ndarray, n_clusters: int = 4, max_iter: int = 100) -> np.ndarray:
    rng = np.random.default_rng(42)
    initial_indices = np.linspace(0, len(matrix) - 1, num=n_clusters, dtype=int)
    centroids = matrix[initial_indices].copy()

    for _ in range(max_iter):
        distances = np.linalg.norm(matrix[:, None, :] - centroids[None, :, :], axis=2)
        labels = distances.argmin(axis=1)
        new_centroids = []
        for cluster_id in range(n_clusters):
            cluster_points = matrix[labels == cluster_id]
            if len(cluster_points) == 0:
                new_centroids.append(matrix[rng.integers(0, len(matrix))])
            else:
                new_centroids.append(cluster_points.mean(axis=0))
        new_centroids = np.array(new_centroids)
        if np.allclose(centroids, new_centroids):
            break
        centroids = new_centroids

    return labels


def _map_segment_name(row: pd.Series, revenue_median: float, quantity_median: float) -> str:
    if row["total_revenue"] >= revenue_median and row["total_quantity"] >= quantity_median:
        return "Yuksek gelir / yuksek talep"
    if row["total_revenue"] < revenue_median and row["total_quantity"] < quantity_median:
        return "Dusuk gelir / dusuk talep"
    if row["total_revenue"] >= revenue_median and row["total_quantity"] < quantity_median:
        return "Stok riski tasiyan urun"
    return "Kampanya adayi urun"


def run_product_segmentation(df: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
    feature_df = build_product_feature_frame(df)
    if feature_df.empty:
        return pd.DataFrame()

    feature_columns = ["total_revenue", "total_quantity", "average_price", "average_hour", "weekend_share"]
    matrix = _standardize_features(feature_df, feature_columns)
    safe_clusters = min(n_clusters, len(feature_df))
    labels = _simple_kmeans(matrix, n_clusters=safe_clusters)
    feature_df["cluster_id"] = labels

    revenue_median = feature_df["total_revenue"].median()
    quantity_median = feature_df["total_quantity"].median()
    feature_df["segment_name"] = feature_df.apply(
        lambda row: _map_segment_name(row, revenue_median, quantity_median),
        axis=1,
    )
    return feature_df.sort_values(["cluster_id", "total_revenue"], ascending=[True, False]).reset_index(drop=True)


def summarize_segments(segment_df: pd.DataFrame) -> pd.DataFrame:
    if segment_df.empty:
        return pd.DataFrame(columns=["segment_name", "product_count", "avg_revenue", "avg_quantity"])

    summary_df = (
        segment_df.groupby("segment_name")
        .agg(
            product_count=("product_type", "count"),
            avg_revenue=("total_revenue", "mean"),
            avg_quantity=("total_quantity", "mean"),
        )
        .reset_index()
        .sort_values("avg_revenue", ascending=False)
    )
    return summary_df
