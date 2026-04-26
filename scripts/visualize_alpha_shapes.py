"""Visualize three alpha-shape examples and save to docs/alpha_shapes_examples.png."""
import sys
import time
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.geometry.alpha_shapes import generate_alpha_shape

RNG = np.random.default_rng(42)


def disk_points(cx, cy, r, n):
    angles = RNG.uniform(0, 2 * np.pi, n)
    radii = r * np.sqrt(RNG.uniform(0, 1, n))
    return np.column_stack([cx + radii * np.cos(angles), cy + radii * np.sin(angles)])


def l_shape_points(n):
    n_each = n // 2
    bottom = np.column_stack([RNG.uniform(0, 1.0, n_each), RNG.uniform(0, 0.4, n_each)])
    left = np.column_stack([RNG.uniform(0, 0.4, n - n_each), RNG.uniform(0, 1.0, n - n_each)])
    return np.vstack([bottom, left])


DATASETS = [
    ("50-point disk", disk_points(0.5, 0.5, 0.35, 50)),
    ("100-point irregular (L-shape)", l_shape_points(100)),
    ("500-point random cluster", RNG.uniform(0, 1, (500, 2))),
]

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle("Alpha Shape Examples — Smart Click Maps", fontsize=14, fontweight="bold")

for ax, (title, pts) in zip(axes, DATASETS):
    t0 = time.perf_counter()
    poly = generate_alpha_shape(pts)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    ax.scatter(pts[:, 0], pts[:, 1], s=8, color="#40E0D0", alpha=0.6, zorder=2)

    if poly is not None and not poly.is_empty:
        x, y = poly.exterior.xy
        ax.fill(x, y, alpha=0.35, color="#40E0D0")
        ax.plot(x, y, color="white", linewidth=2, zorder=3)

    ax.set_title(f"{title}\n{elapsed_ms:.1f}ms | {len(pts)} pts", fontsize=10)
    ax.set_facecolor("#1a1a2e")
    ax.set_aspect("equal")
    ax.tick_params(colors="#aaa")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

    print(f"{title}: {elapsed_ms:.1f}ms  |  valid={poly is not None and poly.is_valid}")

fig.patch.set_facecolor("#0d0d1a")
plt.tight_layout()

out = Path(__file__).resolve().parents[1] / "docs" / "alpha_shapes_examples.png"
out.parent.mkdir(exist_ok=True)
plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"\nSaved → {out}")
