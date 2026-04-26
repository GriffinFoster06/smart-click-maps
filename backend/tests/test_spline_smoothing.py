"""Tests for backend/geometry/spline_smooth.py."""
from __future__ import annotations

import time
from unittest.mock import patch

import numpy as np
import pytest
from shapely.geometry import Polygon

from backend.geometry.spline_smooth import (
    adaptive_smoothing,
    smooth_polygon,
    validate_smoothed_polygon,
)


def _square_vertices() -> np.ndarray:
    return np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])


def _noisy_circle(n: int = 50, radius: float = 1.0, noise: float = 0.05) -> np.ndarray:
    rng = np.random.default_rng(42)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    r = radius + rng.uniform(-noise, noise, n)
    return np.column_stack([r * np.cos(angles), r * np.sin(angles)])


def test_too_few_vertices_returns_input():
    verts = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, 1.0]])
    result = smooth_polygon(verts)
    np.testing.assert_array_equal(result, verts)


def test_output_vertex_count():
    verts = _square_vertices()
    result = smooth_polygon(verts, resolution=3)
    assert result.shape == (len(verts) * 3, 2)


def test_square_smooths_to_round():
    verts = _square_vertices()
    smoothed = smooth_polygon(verts, smoothing_factor=0.3, resolution=3)
    # A smoothed square should have corners rounded.  Measure the maximum
    # signed 2-D cross-product magnitude at each vertex; a sharp corner
    # (90°) has a larger value than a smooth curve.
    def max_corner_sharpness(pts: np.ndarray) -> float:
        n = len(pts)
        cross_mags = []
        for i in range(n):
            a = pts[(i - 1) % n] - pts[i]
            b = pts[(i + 1) % n] - pts[i]
            cross_mags.append(abs(float(a[0] * b[1] - a[1] * b[0])))
        return float(np.max(cross_mags))

    assert max_corner_sharpness(smoothed) < max_corner_sharpness(verts)


def test_complex_polygon_preserves_topology():
    # adaptive_smoothing guarantees a valid result (falls back to original on failure)
    polygon = Polygon(_noisy_circle(50))
    result = adaptive_smoothing(polygon, cluster_size=50)
    assert result is not None
    assert result.is_valid
    assert result.exterior.is_simple


def test_area_preservation_square():
    # adaptive_smoothing falls back when area change exceeds 10%,
    # so the returned polygon always satisfies the area constraint.
    polygon = Polygon(_square_vertices())
    result = adaptive_smoothing(polygon, cluster_size=30)
    orig_area = polygon.area
    result_area = result.area
    assert abs(result_area - orig_area) / orig_area < 0.10


def test_area_preservation_noisy_circle():
    # adaptive_smoothing falls back when area change exceeds 10%,
    # guaranteeing area preservation regardless of smoothing aggressiveness.
    polygon = Polygon(_noisy_circle(50))
    result = adaptive_smoothing(polygon, cluster_size=50)
    orig_area = polygon.area
    result_area = result.area
    assert abs(result_area - orig_area) / orig_area < 0.10


def test_performance_under_5ms():
    verts = _noisy_circle(100)
    timings = []
    for _ in range(10):
        t0 = time.perf_counter()
        smooth_polygon(verts)
        timings.append(time.perf_counter() - t0)
    median_ms = np.median(timings) * 1000
    assert median_ms < 5.0, f"median smoothing took {median_ms:.2f} ms, expected < 5 ms"


def test_validation_passes_for_valid_smoothing():
    # Use exact interpolation (smoothing_factor=0) so the spline passes through
    # every vertex and does not introduce area change or self-intersections.
    verts = _noisy_circle(50)
    smoothed = smooth_polygon(verts, smoothing_factor=0.0)
    ok, report = validate_smoothed_polygon(verts, smoothed)
    assert ok, report["reason"]


def test_validation_detects_area_blowup():
    original = _noisy_circle(50, radius=1.0)
    # Scale up dramatically to simulate an area-blowing result
    bloated = _noisy_circle(150, radius=2.0)
    ok, report = validate_smoothed_polygon(original, bloated)
    assert not ok
    assert report["area_delta"] >= 0.10


@pytest.mark.parametrize(
    "cluster_size, expected_factor",
    [(30, 0.5), (75, 0.4), (150, 0.3)],
)
def test_adaptive_smoothing_picks_factor(cluster_size: int, expected_factor: float):
    polygon = Polygon(_noisy_circle(60))
    captured: dict = {}

    original_smooth = smooth_polygon

    def mock_smooth(verts: np.ndarray, smoothing_factor: float = 0.3, resolution: int = 3):
        captured["smoothing_factor"] = smoothing_factor
        return original_smooth(verts, smoothing_factor=smoothing_factor, resolution=resolution)

    with patch("backend.geometry.spline_smooth.smooth_polygon", side_effect=mock_smooth):
        adaptive_smoothing(polygon, cluster_size=cluster_size)

    assert captured.get("smoothing_factor") == expected_factor


def test_adaptive_smoothing_none_input():
    assert adaptive_smoothing(None, cluster_size=50) is None


def test_adaptive_smoothing_empty_polygon():
    result = adaptive_smoothing(Polygon(), cluster_size=50)
    assert result is not None and result.is_empty


def test_adaptive_smoothing_returns_polygon():
    polygon = Polygon(_noisy_circle(80))
    result = adaptive_smoothing(polygon, cluster_size=80)
    assert result is not None
    assert not result.is_empty
    assert result.is_valid
