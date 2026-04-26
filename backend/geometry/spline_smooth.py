"""Cubic spline smoothing for alpha shape polygon boundaries."""
from __future__ import annotations

from typing import Optional

import numpy as np
from scipy.interpolate import splev, splprep
from shapely.geometry import LinearRing, Polygon


def smooth_polygon(
    polygon_vertices: np.ndarray,
    smoothing_factor: float = 0.3,
    resolution: int = 3,
) -> np.ndarray:
    """Apply parametric cubic spline smoothing to polygon boundary vertices.

    Args:
        polygon_vertices: Nx2 array of boundary vertices (open ring, no duplicate closing point).
        smoothing_factor: Controls smoothness; higher = smoother (0 = interpolation). Default 0.3.
        resolution: Output vertex multiplier. Default 3 (M = N * resolution).

    Returns:
        Mx2 smoothed vertex array, or the original array if smoothing cannot be applied.
    """
    n = len(polygon_vertices)
    if n < 4:
        return polygon_vertices

    x = polygon_vertices[:, 0]
    y = polygon_vertices[:, 1]

    try:
        # Normalise to [0,1] so s=smoothing_factor has the same meaning at any
        # coordinate scale (screen pixels or unit-normalised floats alike).
        mins = polygon_vertices.min(axis=0)
        maxs = polygon_vertices.max(axis=0)
        scale = maxs - mins
        scale = np.where(scale > 1e-10, scale, 1.0)
        xn = (x - mins[0]) / scale[0]
        yn = (y - mins[1]) / scale[1]

        tck, _ = splprep([xn, yn], s=smoothing_factor, per=True, k=3)
        u_new = np.linspace(0, 1, n * resolution)
        smooth_xn, smooth_yn = splev(u_new, tck)

        # De-normalise back to original coordinate space
        smooth_x = smooth_xn * scale[0] + mins[0]
        smooth_y = smooth_yn * scale[1] + mins[1]
        return np.column_stack([smooth_x, smooth_y])
    except Exception:
        return polygon_vertices


def validate_smoothed_polygon(
    original: np.ndarray, smoothed: np.ndarray
) -> tuple[bool, dict]:
    """Validate that the smoothed polygon meets quality constraints.

    Args:
        original: Nx2 vertex array of the original polygon.
        smoothed: Mx2 vertex array of the smoothed polygon.

    Returns:
        (ok, report) where report contains per-check details and an optional reason string.
    """
    report: dict = {"valid": False, "simple": False, "area_delta": float("nan"), "reason": None}

    try:
        orig_poly = Polygon(original)
        smooth_poly = Polygon(smoothed)
        ring = LinearRing(smoothed)
    except Exception as exc:
        report["reason"] = f"geometry construction failed: {exc}"
        return False, report

    report["valid"] = smooth_poly.is_valid
    report["simple"] = ring.is_simple

    if orig_poly.area > 0:
        report["area_delta"] = abs(smooth_poly.area - orig_poly.area) / orig_poly.area
    else:
        report["area_delta"] = 0.0

    if not report["valid"]:
        report["reason"] = "smoothed polygon is not valid (self-intersection or ring error)"
        return False, report
    if not report["simple"]:
        report["reason"] = "smoothed boundary self-intersects"
        return False, report
    if report["area_delta"] >= 0.10:
        report["reason"] = f"area changed by {report['area_delta']:.1%}, exceeds 10% limit"
        return False, report

    return True, report


def adaptive_smoothing(
    polygon: Optional[Polygon], cluster_size: int
) -> Optional[Polygon]:
    """Smooth a shapely Polygon using a cluster-size-adaptive smoothing factor.

    Args:
        polygon: Input shapely Polygon (may be None or empty).
        cluster_size: Number of points in the originating cluster.

    Returns:
        Smoothed shapely Polygon, or the original on validation failure / degenerate input.
    """
    if polygon is None or polygon.is_empty:
        return polygon

    if cluster_size > 100:
        smoothing_factor = 0.3
    elif cluster_size >= 50:
        smoothing_factor = 0.4
    else:
        smoothing_factor = 0.5

    # shapely exterior closes the ring; drop the duplicate last point
    coords = np.array(polygon.exterior.coords)[:-1]

    if len(coords) < 4:
        return polygon

    smoothed_coords = smooth_polygon(coords, smoothing_factor=smoothing_factor, resolution=3)

    ok, _ = validate_smoothed_polygon(coords, smoothed_coords)
    if not ok:
        return polygon

    return Polygon(smoothed_coords)
