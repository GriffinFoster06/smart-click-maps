#!/usr/bin/env python3
"""
Stdin→stdout JSON worker: reads a click batch, outputs hotspot list.
Called by Node broadcaster once per 200ms window.
"""
import sys
import json
import time
import numpy as np

from backend.clustering.engine import ClusteringEngine
from backend.utils.hotspot_builder import build_hotspots

_engine = ClusteringEngine()


def main() -> None:
    raw = sys.stdin.read()
    try:
        clicks = json.loads(raw)
    except json.JSONDecodeError:
        print("[]")
        return

    _engine.add_clicks(clicks, timestamp=time.time())
    labels = _engine.cluster()
    if labels is None:
        print("[]")
        return

    hotspots = build_hotspots(_engine.points, labels)
    print(json.dumps(hotspots))


if __name__ == "__main__":
    main()
