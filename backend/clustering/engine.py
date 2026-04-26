"""HDBSCAN clustering engine with incremental updates."""
from __future__ import annotations

import numpy as np
from typing import List, Optional
import hdbscan

from backend.clustering.cluster_engine import (
    MIN_POINTS_FOR_CLUSTERING,
    calculate_adaptive_params,
)


class ClusteringEngine:
    """Maintains rolling click window and produces cluster assignments."""

    MAX_CLUSTERS = 5
    WINDOW_SECONDS = 10

    def __init__(self, min_cluster_size: int = 15, min_samples: int = 5) -> None:
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self._clicks: np.ndarray = np.empty((0, 2), dtype=np.float32)
        self._timestamps: np.ndarray = np.empty(0, dtype=np.float64)

    def add_clicks(self, clicks: List[dict], timestamp: float) -> None:
        """Ingest new normalised [0,1] click coordinates."""
        if clicks:
            new_pts = np.array([[c["x"], c["y"]] for c in clicks], dtype=np.float32)
            new_ts = np.full(len(clicks), timestamp, dtype=np.float64)
            self._clicks = np.vstack([self._clicks, new_pts])
            self._timestamps = np.concatenate([self._timestamps, new_ts])
        self._evict_old(timestamp)

    def _evict_old(self, now: float) -> None:
        mask = (now - self._timestamps) <= self.WINDOW_SECONDS
        self._clicks = self._clicks[mask]
        self._timestamps = self._timestamps[mask]

    def cluster(self) -> Optional[np.ndarray]:
        """Return label array or None if too few points."""
        n_points = len(self._clicks)
        if n_points < MIN_POINTS_FOR_CLUSTERING:
            return None

        click_variance = float(np.std(self._clicks, axis=0).mean())
        min_cluster_size, min_samples = calculate_adaptive_params(n_points, click_variance)
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric="euclidean",
            cluster_selection_method="eom",
            prediction_data=False,
            core_dist_n_jobs=-1,
            algorithm="boruvka_kdtree",
        )
        labels = clusterer.fit_predict(self._clicks)
        return labels

    @property
    def points(self) -> np.ndarray:
        return self._clicks
