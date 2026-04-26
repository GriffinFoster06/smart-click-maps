# Architecture

## Data Flow

```
Twitch viewer browser
  │  click {x, y} (normalised 0–1)
  ▼
Node.js / Socket.io server
  │  ClickAggregator  (rate-limit, buffer)
  │  every 200 ms → drain batch
  ▼
Python cluster_worker.py  (stdin JSON → stdout JSON)
  │  ClusteringEngine  — rolling 10 s window, HDBSCAN
  │  alpha_shape + spline smoothing per cluster
  │  build_hotspots → top-5, normalise to 100 %
  ▼
Node.js broadcasts  hotspots[] via Socket.io
  ▼
React frontend
  │  useHotspots hook
  ▼
HotspotRenderer (Three.js WebGL)
  │  ShapeGeometry per polygon
  └─ renders on canvas overlay
```

## Key Design Decisions

| Decision | Rationale |
|---|---|
| HDBSCAN over DBSCAN | Handles clusters of varying density |
| Adaptive alpha | α = 0.8·√density/spread avoids over/under-fitting |
| Incremental window eviction | Avoids full re-cluster every tick |
| Python worker via stdin/stdout | Keeps Node server simple; easy to swap to microservice |
| WebGL (Three.js) | Handles 60 fps polygon updates for thousands of DOM frames |
| Competitive assignment | Each click belongs to exactly one hotspot |

## Scaling

- Socket.io horizontal scaling: add Redis adapter when > 1 Node process
- Python worker: upgrade to persistent process (ZeroMQ or gRPC) when latency matters at 20k+ CCU
- CDN / Railway auto-scale handles egress
