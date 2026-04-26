import time
import os

import numpy as np
import pytest
from backend.clustering.engine import ClusteringEngine
from backend.clustering.cluster_engine import (
    MAX_CLUSTERS,
    ClusterResult,
    calculate_adaptive_params,
    cluster_clicks,
)


def _make_cluster(cx, cy, n=50, spread=0.05):
    rng = np.random.default_rng(42)
    return [
        {"x": float(cx + rng.normal(0, spread)), "y": float(cy + rng.normal(0, spread))}
        for _ in range(n)
    ]


def test_no_crash_on_empty():
    engine = ClusteringEngine()
    assert engine.cluster() is None


def test_finds_two_clusters():
    engine = ClusteringEngine(min_cluster_size=10)
    t = 0.0
    engine.add_clicks(_make_cluster(0.25, 0.25, 60), t)
    engine.add_clicks(_make_cluster(0.75, 0.75, 60), t)
    labels = engine.cluster()
    assert labels is not None
    n_clusters = len(set(labels) - {-1})
    assert n_clusters >= 2


def test_eviction_removes_old_clicks():
    engine = ClusteringEngine()
    engine.add_clicks(_make_cluster(0.5, 0.5, 30), timestamp=0.0)
    assert len(engine.points) == 30
    engine.add_clicks([], timestamp=20.0)  # trigger eviction
    assert len(engine.points) == 0


# ── cluster_engine.py tests ──────────────────────────────────────────────────


def test_adaptive_params_low_variance():
    # 100 clicks, low variance → base=max(8,2)=8, low-variance branch, min_samples floor=5
    mcs, ms = calculate_adaptive_params(100, 0.01)
    assert mcs == 8
    assert ms == 5


def test_adaptive_params_high_variance_scaling():
    # 10k clicks, high variance → base=200, *1.5=300, min_samples=max(5,90)=90
    mcs, ms = calculate_adaptive_params(10_000, 0.1)
    assert mcs == 300
    assert ms == 90


def test_cluster_empty_and_tiny():
    rng = np.random.default_rng(7)
    # Empty array
    res = cluster_clicks(np.empty((0, 2)))
    assert isinstance(res, ClusterResult)
    assert res.clusters == []
    assert res.n_points == 0

    # Single point
    res = cluster_clicks(rng.uniform(size=(1, 2)))
    assert res.clusters == []

    # Degenerate: all identical (zero variance)
    res = cluster_clicks(np.zeros((20, 2)))
    assert res.clusters == []


def test_cluster_10_points():
    rng = np.random.default_rng(13)
    pts = rng.uniform(0, 1, (10, 2))
    res = cluster_clicks(pts)
    n = len(res.clusters)
    assert 0 <= n <= 1, f"Expected 0-1 clusters for 10 random points, got {n}"


def test_cluster_100_points_3_groups():
    rng = np.random.default_rng(42)
    centres = [(0.2, 0.2), (0.5, 0.8), (0.8, 0.3)]
    pts = np.vstack([rng.normal(c, 0.02, (34, 2)) for c in centres])
    # clip to [0,1] to avoid out-of-range values
    pts = np.clip(pts, 0.0, 1.0)

    res = cluster_clicks(pts)
    n = len(res.clusters)
    assert n == 3, f"Expected 3 clusters for 3-blob input, got {n}"

    # Each detected centroid must be close to one of the true centres
    detected = set()
    for info in res.clusters:
        cx, cy = info.centroid
        for i, (tx, ty) in enumerate(centres):
            if abs(cx - tx) <= 0.05 and abs(cy - ty) <= 0.05:
                detected.add(i)
                break
    assert len(detected) == 3, f"Centroids did not match expected blob centres: {[c.centroid for c in res.clusters]}"


def test_cluster_1000_uniform():
    rng = np.random.default_rng(99)
    pts = rng.uniform(0, 1, (1000, 2))
    res = cluster_clicks(pts)
    n = len(res.clusters)
    assert 0 <= n <= 2, f"Expected 0-2 clusters for 1000 uniform points, got {n}"


def test_cluster_10k_performance(capsys):
    rng = np.random.default_rng(0)
    pts = np.vstack([
        rng.normal((0.2, 0.2), 0.03, (2500, 2)),
        rng.normal((0.5, 0.8), 0.03, (2500, 2)),
        rng.normal((0.8, 0.3), 0.03, (2500, 2)),
        rng.uniform(0, 1, (2500, 2)),
    ])
    pts = np.clip(pts, 0.0, 1.0)

    # warm-up run to amortise import/JIT cost
    cluster_clicks(pts[:100])

    runs = []
    for _ in range(5):
        t0 = time.perf_counter()
        res = cluster_clicks(pts)
        runs.append((time.perf_counter() - t0) * 1000)

    median_ms = sorted(runs)[2]
    with capsys.disabled():
        print(
            f"\n[10k perf] N={len(pts)}  clusters={len(res.clusters)}  "
            f"min={min(runs):.1f}ms  median={median_ms:.1f}ms  max={max(runs):.1f}ms"
        )

    perf_budget_ms = float(os.getenv("CLUSTER_10K_BUDGET_MS", "350"))
    assert median_ms < perf_budget_ms, (
        f"Median latency {median_ms:.1f}ms exceeds {perf_budget_ms:.1f}ms budget"
    )


def test_result_invariants():
    rng = np.random.default_rng(42)
    centres = [(0.2, 0.2), (0.5, 0.8), (0.8, 0.3)]
    pts = np.vstack([rng.normal(c, 0.02, (34, 2)) for c in centres])
    pts = np.clip(pts, 0.0, 1.0)
    n = len(pts)

    res = cluster_clicks(pts)

    # Labels array shape matches input
    assert res.labels.shape == (n,)
    assert res.probabilities.shape == (n,)
    assert res.n_points == n

    # Cluster count cap
    assert len(res.clusters) <= MAX_CLUSTERS

    # Sorted by size descending
    counts = [c.point_count for c in res.clusters]
    assert counts == sorted(counts, reverse=True)

    # All centroids in [0, 1]²
    for info in res.clusters:
        cx, cy = info.centroid
        assert 0.0 <= cx <= 1.0, f"centroid x={cx} out of range"
        assert 0.0 <= cy <= 1.0, f"centroid y={cy} out of range"

    # params matches what calculate_adaptive_params would return
    variance = float(np.std(pts, axis=0).mean())
    expected_params = calculate_adaptive_params(n, variance)
    assert res.params == expected_params
