"""Visualise spline smoothing: alpha shape boundary before vs. after."""
from __future__ import annotations

import os
import sys

import numpy as np

# Allow running from repo root without install
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.geometry.alpha_shapes import generate_alpha_shape
from backend.geometry.spline_smooth import adaptive_smoothing, smooth_polygon


def _synthetic_cluster(n: int = 300, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    # Two overlapping blobs to produce an irregular alpha shape
    c1 = rng.normal([200, 300], [40, 30], (n // 2, 2))
    c2 = rng.normal([320, 280], [30, 50], (n - n // 2, 2))
    return np.vstack([c1, c2])


def main() -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed — skipping visualisation")
        return

    points = _synthetic_cluster()
    alpha_shape = generate_alpha_shape(points)
    if alpha_shape is None:
        print("Could not generate alpha shape for synthetic cluster")
        return

    smoothed = adaptive_smoothing(alpha_shape, cluster_size=len(points))

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for ax, poly, title in [
        (axes[0], alpha_shape, "Alpha Shape (original)"),
        (axes[1], smoothed or alpha_shape, "After Spline Smoothing"),
    ]:
        ax.scatter(points[:, 0], points[:, 1], s=3, alpha=0.3, color="gray", label="clicks")
        x, y = poly.exterior.xy
        ax.plot(x, y, color="teal", linewidth=2)
        ax.fill(x, y, alpha=0.25, color="teal")
        ax.set_title(title)
        ax.set_aspect("equal")
        ax.axis("off")

    plt.tight_layout()
    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "spline_before_after.png")
    plt.savefig(out_path, dpi=150)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
