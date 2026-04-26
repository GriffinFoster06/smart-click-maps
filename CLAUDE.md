# Smart Click Maps — Professional Clone for DougDoug

Production-grade real-time click clustering system for Twitch streams.
Matches Ex Machina's Smart Click Maps quality with HDBSCAN + Alpha Shapes + WebGL.

**Target:** 10,000–20,000 concurrent viewers with <500ms latency.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.11 | Clustering pipeline |
| | HDBSCAN | Hierarchical density-based clustering |
| | SciPy | Delaunay triangulation, spline interpolation |
| | Shapely | Polygon operations and validation |
| | NumPy | Numerical computations |
| | Pytest | Unit testing |
| **Server** | Node.js 20 | Real-time communication |
| | Express | HTTP server |
| | Socket.io | WebSocket real-time communication |
| | TypeScript | Type safety |
| **Frontend** | React 18 + WebGL | Visualization |
| | Three.js | WebGL rendering engine |
| | Socket.io-client | Real-time data reception |
| | TypeScript | Type safety |
| **Infrastructure** | Railway.app | Hosting and deployment |
| | Redis | Click buffer storage *(optional, future)* |

---

## Project Architecture

```
/backend
  /clustering
    cluster_engine.py     - HDBSCAN clustering with adaptive parameters
    spatial_index.py      - Quadtree for fast neighbor queries
  /geometry
    alpha_shapes.py       - Alpha shape generation
    spline_smooth.py      - Cubic spline boundary smoothing
    centroid.py           - Geometric calculations
  /utils
    validators.py         - Input validation
    performance.py        - Timing and profiling
  /tests
    test_clustering.py
    test_alpha_shapes.py
    test_integration.py

/server
  /src
    server.ts             - Main server entry point
    /websocket
      handler.ts          - WebSocket connection management
      rate_limit.ts       - Per-user rate limiting (10 clicks/sec)
    /aggregation
      click_buffer.ts     - Time-windowed click storage
      aggregator.ts       - Trigger clustering every 200ms
    /broadcast
      broadcaster.ts      - Send hotspots to all clients
  /tests
    integration.test.ts

/frontend
  /src
    /components
      ClickMap.tsx        - Main component
      Overlay.tsx         - OBS browser source overlay
    /renderers
      WebGLRenderer.ts    - Three.js setup
      HotspotRenderer.ts  - Polygon + gradient rendering
      TextRenderer.ts     - Percentage labels
    /hooks
      useWebSocket.ts     - Socket.io connection
      useHotspots.ts      - Hotspot state management
    /utils
      coordinates.ts      - Screen coordinate transforms

/shared
  /types
    hotspot.ts            - Hotspot data structure
    click.ts              - Click event structure

/docs
  algorithm.md            - Technical algorithm documentation
  deployment.md           - Deployment guide
  tuning.md               - Parameter tuning guide
```

---

## Data Flow

```
Viewer clicks → Rate limit → WebSocket → Server
     ↓
Server aggregates clicks in 4-second sliding window
     ↓
Every 200ms: Trigger clustering pipeline
     ↓
Python clustering → Alpha shapes → Smoothing → Return polygons
     ↓
Server broadcasts hotspots (NOT raw clicks) to all viewers
     ↓
Frontend WebGL renders polygons with gradients
```

---

## Critical Requirements

### Algorithm Quality
- HDBSCAN clustering (NOT basic DBSCAN)
- Adaptive parameters based on viewer count and variance
- Alpha shapes with automatic alpha calculation
- Cubic spline smoothing (`smoothing_factor=0.3`)
- Competitive assignment (each click belongs to ONE hotspot)

### Performance Targets
| Operation | Target |
|-----------|--------|
| Clustering | < 200ms for 10k points |
| Alpha shapes | < 50ms per cluster |
| Total pipeline | < 300ms |
| Update frequency | 200ms (5 Hz) |
| Concurrent viewers | 10k–20k |

### Visual Quality
- Adaptive polygon shapes (like screenshot teal shape)
- Smooth curved edges (no jagged lines)
- Radial gradient fills (bright center, transparent edges)
- White outlines (3px stroke)
- Percentage labels (48px, bold, drop shadow)
- Color scheme: Teal primary `rgb(64,224,208)`, Purple secondary `rgb(147,112,219)`

---

## Development Commands

### Backend
```bash
python3 -m pytest backend/tests/            # Run all tests
python3 backend/clustering/cluster_engine.py # Test clustering
python3 backend/geometry/alpha_shapes.py    # Test alpha shapes
```

### Server
```bash
cd server && npm run dev    # Start dev server (hot reload)
cd server && npm test       # Run integration tests
cd server && npm run build  # Production build
```

### Frontend
```bash
cd frontend && npm start    # Start React dev server
cd frontend && npm test     # Run component tests
cd frontend && npm run build # Production build
```

### Deployment
```bash
railway up    # Deploy to Railway
railway logs  # View production logs
```

---

## Parameter Tuning

### HDBSCAN
- `min_cluster_size`: `max(8, total_clicks * 0.02)`
- `min_samples`: `min_cluster_size * 0.3`
- Increase if high variance

### Alpha Shapes
- `alpha`: `0.8 * (density^0.5) / spread`
- Per-cluster calculation (different alpha for each)

### Spline Smoothing
- `smoothing_factor`: `0.3` (sweet spot)
- `resolution`: 3× original vertices

### WebSocket
- Click buffer: 4 seconds (auto-expire old clicks)
- Update interval: 200ms
- Rate limit: 10 clicks/sec per user
- Max hotspots: 5

---

## Quality Standards

### Code
- All Python code must have type hints
- All functions must have docstrings
- Test coverage: > 80%
- All tests must pass before commit

### Performance
- Profile slow operations (use Python's `cProfile`)
- Optimize critical path (clustering + alpha shapes)
- Monitor memory usage (max 2GB for backend)

### Visual
- Match reference screenshot quality
- Smooth 60 FPS rendering
- No visual artifacts or flickering

---

## NEVER Do This

### Algorithm
- ❌ Don't use regular DBSCAN (use HDBSCAN)
- ❌ Don't use fixed clustering parameters
- ❌ Don't use convex hull (use alpha shapes)
- ❌ Don't skip spline smoothing
- ❌ Don't use circular visualizations

### Performance
- ❌ Don't send raw clicks to frontend (send aggregated hotspots)
- ❌ Don't re-cluster all clicks every update (use incremental)
- ❌ Don't use Canvas 2D (use WebGL)
- ❌ Don't create new geometries every frame (cache)

### Architecture
- ❌ Don't put clustering in Node.js (use Python subprocess)
- ❌ Don't store clicks in database (use in-memory buffer)
- ❌ Don't broadcast every 16ms (use 200ms)

---

## Success Criteria

1. Clustering detects 2–5 hotspots automatically
2. Polygons are smooth and adaptive (not circles)
3. Percentages sum to 100% ± 1%
4. Handles 10k viewers without lag
5. Visually matches reference screenshot
6. <500ms end-to-end latency
7. Works in OBS browser source

---

## Reference Material

See uploaded screenshot (teal polygon shape) for target visual quality.
This is the quality bar we're matching.

---

**Build this right. No shortcuts. Professional quality for DougDoug.**
