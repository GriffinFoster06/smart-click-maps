/**
 * Accumulates incoming clicks between drain cycles.
 * Rate-limits per socket to prevent griefing.
 */
const RATE_LIMIT_PER_SOCKET = 2; // 10 clicks/sec at 200ms ticks

class ClickAggregator {
  constructor() {
    this._buffer = [];
    this._socketCounts = new Map();
  }

  add({ x, y, socketId }) {
    if (typeof socketId !== "string" || socketId.length === 0) return;
    const count = this._socketCounts.get(socketId) ?? 0;
    if (count >= RATE_LIMIT_PER_SOCKET) return;
    this._socketCounts.set(socketId, count + 1);
    this._buffer.push({ x, y });
  }

  /** Returns buffered clicks and resets for next window. */
  drain() {
    const batch = this._buffer;
    this._buffer = [];
    this._socketCounts.clear();
    return batch;
  }
}

module.exports = { ClickAggregator };
