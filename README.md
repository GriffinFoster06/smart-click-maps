# Smart Click Maps

Real-time viewer click clustering for Twitch streams — a recreation of Ex Machina's Smart Click Maps extension, built for DougDoug's 10k–20k CCU streams.

## How It Works

Viewers click on a game overlay. Clicks are aggregated server-side every 200 ms, clustered with HDBSCAN, shaped with adaptive alpha shapes, and broadcast back as up to 5 hotspot polygons rendered via WebGL.

## Quick Start

```bash
# Install everything
./scripts/setup.sh

# Start dev servers (Node + Vite)
npm run dev

# Run Python tests
pytest backend/tests/ -v

# Run Node tests
npm test --workspace=server
```

## Stack

| Layer | Tech |
|---|---|
| Clustering | Python 3.11, HDBSCAN, SciPy, Shapely |
| Server | Node.js, Socket.io, Express |
| Frontend | React 18, Three.js (WebGL), TypeScript |
| Hosting | Railway.app |

## Project Structure

```
backend/
  clustering/   HDBSCAN engine with rolling window
  geometry/     Alpha shapes + spline smoothing
  utils/        Spatial index, hotspot builder
  tests/
server/
  websocket/    Socket.io setup
  aggregation/  Rate-limited click buffer
  broadcast/    Python worker bridge
  tests/
frontend/
  src/
    components/ React UI
    renderers/  Three.js WebGL renderer
    hooks/      useHotspots (Socket.io)
    utils/
  public/
shared/
  types/        TypeScript interfaces
  constants/    Shared config values
docs/           Architecture notes
scripts/        Setup & deploy helpers
```

## Configuration

Copy `.env.example` to `.env` in `server/` and set:

```
PORT=3001
FRONTEND_ORIGIN=http://localhost:5173
```

Set `VITE_SERVER_URL` in `frontend/.env` for production.

## Deploy

```bash
railway up
```

See `docs/architecture.md` for scaling notes.
