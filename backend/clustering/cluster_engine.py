"""Adaptive HDBSCAN clustering engine for Smart Click Maps.

Stateless module — every call to cluster_clicks() is independent.
The rolling-window state lives in engine.py (ClusteringEngine).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np
import hdbscan
from scipy.spatial import ConvexHull, QhullError


# Points-per-axis std-dev (in normalised [0,1] screen coords) above which
# we apply the 1.5× tightening multiplier to avoid over-merging sparse clouds.
VARIANCE_THRESHOLD: float = 0.05

MAX_CLUSTERS: int = 5  # return at most this many hotspots, ranked by size
MIN_POINTS_FOR_CLUSTERING: int = 8

_EMPTY_F64 = np.empty(0, dtype=np.float64)
_EMPTY_I32 = np.empty(0, dtype=np.int32)


@dataclass(frozen=True)
class ClusterInfo:
    """Metadata for a single detected hotspot cluster."""

    label: int
    centroid: Tuple[float, float]
    density: float          # points / convex-hull area; 0.0 when undefined
    point_count: int
    point_indices: np.ndarray = field(compare=False)


@dataclass(frozen=True)
class ClusterResult:
    """Full output of one cluster_clicks() call."""

    labels: np.ndarray          # shape (N,), -1 = noise
    probabilities: np.ndarray   # shape (N,), HDBSCAN membership confidence
    clusters: List[ClusterInfo] # ranked desc by point_count, len <= MAX_CLUSTERS
    n_points: int
    params: Tuple[int, int]     # (min_cluster_size, min_samples) actually used


def calculate_adaptive_params(
    total_clicks: int, click_variance: float
) -> Tuple[int, int]:
    """Return optimal (min_cluster_size, min_samples) for the current batch.

    Args:
        total_clicks: Number of points in the current window.
        click_variance: Mean per-axis std-dev of the points in [0,1] screen
            coords — use ``np.std(points, axis=0).mean()``.

    Returns:
        Tuple of (min_cluster_size, min_samples).
    """
    base = max(8, int(total_clicks * 0.02))

    if click_variance > VARIANCE_THRESHOLD:
        # Clicks are spread across the screen — tighten to avoid one giant blob
        min_cluster_size = int(base * 1.5)
    else:
        min_cluster_size = base

    min_samples = max(5, int(min_cluster_size * 0.3))
    return min_cluster_size, min_samples


def _compute_density(pts: np.ndarray) -> float:
    """Points-per-unit-area via convex hull; 0.0 on degenerate input."""
    if len(pts) < 3:
        return 0.0
    try:
        hull = ConvexHull(pts)
        area = hull.volume  # scipy uses .volume for 2-D area
        return float(len(pts) / area) if area > 0 else 0.0
    except QhullError:
        return 0.0


def cluster_clicks(points: np.ndarray) -> ClusterResult:
    """Run adaptive HDBSCAN on a batch of 2-D click coordinates.

    Args:
        points: (N, 2) float array of normalised [0, 1] screen coordinates.
            Accepts None or empty arrays gracefully.

    Returns:
        ClusterResult with labels, probabilities, and up to MAX_CLUSTERS
        ClusterInfo objects ranked by descending point count.
    """
    # ── Edge cases ──────────────────────────────────────────────────────────
    if points is None or len(points) == 0:
        return ClusterResult(
            labels=_EMPTY_I32.copy(),
            probabilities=_EMPTY_F64.copy(),
            clusters=[],
            n_points=0,
            params=(MIN_POINTS_FOR_CLUSTERING, 5),
        )

    pts = np.asarray(points, dtype=np.float32)
    n = len(pts)

    if n < MIN_POINTS_FOR_CLUSTERING:
        # Below the minimum possible min_cluster_size — no cluster can form
        return ClusterResult(
            labels=np.full(n, -1, dtype=np.int32),
            probabilities=np.zeros(n, dtype=np.float64),
            clusters=[],
            n_points=n,
            params=(MIN_POINTS_FOR_CLUSTERING, 5),
        )

    variance = float(np.std(pts, axis=0).mean())
    if variance == 0.0:
        # All points identical — degenerate Delaunay would crash HDBSCAN
        return ClusterResult(
            labels=np.full(n, -1, dtype=np.int32),
            probabilities=np.zeros(n, dtype=np.float64),
            clusters=[],
            n_points=n,
            params=calculate_adaptive_params(n, 0.0),
        )

    # ── Adaptive parameters ──────────────────────────────────────────────────
    min_cluster_size, min_samples = calculate_adaptive_params(n, variance)

    # ── HDBSCAN ──────────────────────────────────────────────────────────────
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=False,
        core_dist_n_jobs=-1,
        algorithm="boruvka_kdtree",
    )
    clusterer.fit(pts)
    labels: np.ndarray = clusterer.labels_.astype(np.int32)
    probs: np.ndarray = clusterer.probabilities_.astype(np.float64)

    # ── Post-processing ───────────────────────────────────────────────────────
    unique_labels = [int(l) for l in set(labels) if l >= 0]
    infos: List[ClusterInfo] = []

    for lbl in unique_labels:
        idx = np.where(labels == lbl)[0]
        cluster_pts = pts[idx]
        centroid = (float(cluster_pts[:, 0].mean()), float(cluster_pts[:, 1].mean()))
        density = _compute_density(cluster_pts)
        infos.append(
            ClusterInfo(
                label=lbl,
                centroid=centroid,
                density=density,
                point_count=len(idx),
                point_indices=idx,
            )
        )

    # Sort by size desc, cap at MAX_CLUSTERS
    infos.sort(key=lambda c: c.point_count, reverse=True)
    infos = infos[:MAX_CLUSTERS]

    return ClusterResult(
        labels=labels,
        probabilities=probs,
        clusters=infos,
        n_points=n,
        params=(min_cluster_size, min_samples),
    )
