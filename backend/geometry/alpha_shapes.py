"""Alpha shape (concave hull) generation with adaptive alpha and spline smoothing."""
from __future__ import annotations

from collections import defaultdict
from typing import Optional

import numpy as np
from scipy.spatial import ConvexHull, Delaunay
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import polygonize, unary_union


def calculate_optimal_alpha(cluster_points: np.ndarray) -> float:
    """Auto-determine alpha based on point density.

    Formula: α = 0.8 * sqrt(density) where density = N / convex_hull_area.
    Dividing by spread (std) was intentionally omitted — it makes the formula
    scale-dependent and causes no triangles to pass for small-radius clusters.
    """
    if len(cluster_points) < 3:
        return 1.0
    try:
        hull = ConvexHull(cluster_points)
        area = hull.volume  # ConvexHull.volume is area in 2D
    except Exception:
        return 1.0
    if area < 1e-10:
        return 1.0
    density = len(cluster_points) / area
    return 0.8 * (density ** 0.5)


def generate_alpha_shape(
    points: np.ndarray, alpha: Optional[float] = None
) -> Optional[Polygon]:
    """Return alpha-shape polygon for a set of 2-D points.

    Uses Delaunay triangulation with circumradius filtering. Interior edges
    (shared by two kept triangles) are removed via XOR so only the boundary
    remains. Assembles the result with shapely polygonize for robustness.
    Returns the largest polygon if a MultiPolygon results.
    """
    if len(points) < 4:
        return None
    if alpha is None:
        alpha = calculate_optimal_alpha(points)

    tri = Delaunay(points)
    ia = tri.simplices[:, 0]
    ib = tri.simplices[:, 1]
    ic = tri.simplices[:, 2]

    pa, pb, pc = points[ia], points[ib], points[ic]
    a = np.linalg.norm(pb - pc, axis=1)
    b = np.linalg.norm(pa - pc, axis=1)
    c = np.linalg.norm(pa - pb, axis=1)
    s = (a + b + c) / 2.0
    area = np.sqrt(np.maximum(s * (s - a) * (s - b) * (s - c), 1e-20))
    circum_r = (a * b * c) / (4.0 * area)

    keep = circum_r < (1.0 / alpha)

    edges: set[tuple[int, int]] = set()
    for simplex in tri.simplices[keep]:
        for i in range(3):
            e = tuple(sorted((int(simplex[i]), int(simplex[(i + 1) % 3]))))
            if e in edges:
                edges.discard(e)
            else:
                edges.add(e)

    if not edges:
        return None

    edge_pts = [(points[i].tolist(), points[j].tolist()) for i, j in edges]
    from shapely.geometry import MultiLineString
    m = MultiLineString(edge_pts)
    polys = list(polygonize(m))
    if not polys:
        return None
    result = unary_union(polys)
    if isinstance(result, MultiPolygon):
        result = max(result.geoms, key=lambda p: p.area)
    return result if isinstance(result, Polygon) else None


def extract_boundary(
    edges: set[tuple[int, int]], points: np.ndarray
) -> np.ndarray:
    """Convert boundary edge set to ordered polygon vertices via graph walk.

    Builds an adjacency map and traverses from an arbitrary start node.
    Returns an Nx2 array of ordered boundary coordinates.
    """
    graph: dict[int, list[int]] = defaultdict(list)
    for u, v in edges:
        graph[u].append(v)
        graph[v].append(u)

    start = next(iter(edges))[0]
    boundary = [start]
    visited = {start}
    current = graph[start][0]

    while current != start:
        boundary.append(current)
        visited.add(current)
        neighbors = graph[current]
        nxt = next((n for n in neighbors if n not in visited), None)
        if nxt is None:
            break
        current = nxt

    return points[boundary]
