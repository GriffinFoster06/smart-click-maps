"""Tests for backend/geometry/alpha_shapes.py"""
import time

import numpy as np
import pytest
from shapely.geometry import Polygon

from backend.geometry.alpha_shapes import (
    calculate_optimal_alpha,
    extract_boundary,
    generate_alpha_shape,
)

RNG = np.random.default_rng(42)


def _disk_points(cx: float, cy: float, r: float, n: int) -> np.ndarray:
    """Points uniformly distributed inside a disk (not just on boundary)."""
    angles = RNG.uniform(0, 2 * np.pi, n)
    radii = r * np.sqrt(RNG.uniform(0, 1, n))
    return np.column_stack([cx + radii * np.cos(angles), cy + radii * np.sin(angles)])


def _l_shape_points(n: int) -> np.ndarray:
    """100 points in an L-shape (non-convex)."""
    n_each = n // 2
    bottom = np.column_stack([RNG.uniform(0, 1, n_each), RNG.uniform(0, 0.4, n_each)])
    left = np.column_stack([RNG.uniform(0, 0.4, n - n_each), RNG.uniform(0, 1, n - n_each)])
    return np.vstack([bottom, left])


def test_circle_50_points():
    """Alpha shape on 50 disk points should be a valid polygon near the disk."""
    pts = _disk_points(0.5, 0.5, 0.3, 50)
    result = generate_alpha_shape(pts)
    assert result is not None
    assert isinstance(result, Polygon)
    assert result.is_valid
    assert result.area > 0
    cx, cy = result.centroid.x, result.centroid.y
    assert abs(cx - 0.5) < 0.15, f"centroid x={cx:.3f} too far from 0.5"
    assert abs(cy - 0.5) < 0.15, f"centroid y={cy:.3f} too far from 0.5"


def test_irregular_shape_100_points():
    """Alpha shape on L-shaped points should be tighter than convex hull."""
    pts = _l_shape_points(100)
    result = generate_alpha_shape(pts)
    assert result is not None
    assert isinstance(result, Polygon)
    assert result.is_valid
    assert result.area > 0
    from shapely.geometry import MultiPoint
    convex_area = MultiPoint(pts).convex_hull.area
    assert result.area < convex_area * 0.85, (
        f"alpha shape area {result.area:.4f} not meaningfully smaller than "
        f"convex hull {convex_area:.4f}"
    )


def test_performance_500_points():
    """generate_alpha_shape on 500 random points must complete in < 150ms."""
    pts = RNG.uniform(0, 1, (500, 2))
    times = []
    for _ in range(3):
        t0 = time.perf_counter()
        generate_alpha_shape(pts)
        times.append(time.perf_counter() - t0)
    best_ms = min(times) * 1000
    assert best_ms < 150, f"Best of 3 runs took {best_ms:.1f}ms (limit: 150ms)"


def test_extract_boundary_valid_polygon():
    """extract_boundary on a square ring of edges should produce a valid Polygon."""
    pts = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    edges: set[tuple[int, int]] = {(0, 1), (1, 2), (2, 3), (0, 3)}
    boundary = extract_boundary(edges, pts)
    assert len(boundary) >= 3
    poly = Polygon(boundary)
    assert poly.area > 0
