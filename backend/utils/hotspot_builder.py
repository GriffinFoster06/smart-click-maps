"""Build serialisable hotspot objects from cluster data."""
from __future__ import annotations

import numpy as np
from typing import List, Optional
from shapely.geometry import Polygon, mapping

from backend.geometry.alpha_shapes import generate_alpha_shape, smooth_polygon


MAX_HOTSPOTS = 5


def build_hotspots(points: np.ndarray, labels: np.ndarray) -> List[dict]:
    """
    Convert HDBSCAN labels into up to MAX_HOTSPOTS serialisable hotspot dicts.
    Normalises intensity so all displayed hotspots sum to 100.
    """
    unique = [l for l in set(labels) if l >= 0]
    if not unique:
        return []

    clusters = {l: points[labels == l] for l in unique}
    # Sort by size descending, take top N
    ranked = sorted(clusters.items(), key=lambda kv: -len(kv[1]))[:MAX_HOTSPOTS]

    total_pts = sum(len(v) for _, v in ranked)
    hotspots = []
    for label, pts in ranked:
        centroid = pts.mean(axis=0).tolist()
        polygon = generate_alpha_shape(pts)
        if polygon is not None:
            polygon = smooth_polygon(polygon)
        intensity = round(100 * len(pts) / total_pts, 1)
        hotspots.append({
            "id": int(label),
            "centroid": {"x": centroid[0], "y": centroid[1]},
            "intensity": intensity,
            "pointCount": int(len(pts)),
            "polygon": mapping(polygon) if polygon and not polygon.is_empty else None,
        })
    return hotspots
