"""KD-tree spatial index for fast neighbour queries."""
from __future__ import annotations

import numpy as np
from scipy.spatial import KDTree
from typing import List, Tuple


class SpatialIndex:
    def __init__(self) -> None:
        self._tree: KDTree | None = None
        self._points: np.ndarray = np.empty((0, 2))

    def build(self, points: np.ndarray) -> None:
        self._points = points
        self._tree = KDTree(points) if len(points) > 0 else None

    def radius_query(self, center: Tuple[float, float], r: float) -> List[int]:
        if self._tree is None:
            return []
        return self._tree.query_ball_point(center, r)

    def k_nearest(self, center: Tuple[float, float], k: int) -> List[int]:
        if self._tree is None:
            return []
        k = min(k, len(self._points))
        _, idx = self._tree.query(center, k=k)
        return idx.tolist() if k > 1 else [int(idx)]
