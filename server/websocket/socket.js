const { Server } = require("socket.io");
const { ClickAggregator } = require("../aggregation/aggregator");
const { HotspotBroadcaster } = require("../broadcast/broadcaster");

const UPDATE_INTERVAL_MS = 200; // 5 Hz

function initSocket(httpServer) {
  const io = new Server(httpServer, {
    cors: { origin: "*" },
    transports: ["websocket"],
  });

  const aggregator = new ClickAggregator();
  const broadcaster = new HotspotBroadcaster(io);

  io.on("connection", (socket) => {
    console.log(`[socket] connected: ${socket.id} (total: ${io.engine.clientsCount})`);

    socket.on("click", (payload) => {
      if (!isValidClick(payload)) return;
      aggregator.add({ x: payload.x, y: payload.y, socketId: socket.id });
    });

    socket.on("disconnect", () => {
      console.log(`[socket] disconnected: ${socket.id}`);
    });
  });

  // Drain aggregator → python → broadcast on fixed interval
  setInterval(async () => {
    const batch = aggregator.drain();
    if (batch.length === 0) return;
    const hotspots = await broadcaster.computeAndBroadcast(batch);
    if (hotspots) {
      io.emit("hotspots", { hotspots, ts: Date.now() });
    }
  }, UPDATE_INTERVAL_MS);

  return io;
}

function isValidClick(payload) {
  if (!payload || typeof payload !== "object") return false;
  const { x, y } = payload;
  return (
    typeof x === "number" &&
    typeof y === "number" &&
    x >= 0 && x <= 1 &&
    y >= 0 && y <= 1
  );
}

module.exports = { initSocket };
