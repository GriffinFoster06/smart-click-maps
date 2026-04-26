/**
 * Accumulates incoming clicks between drain cycles.
 * Rate-limits per socket to prevent griefing.
 */
const RATE_LIMIT_PER_SOCKET = 5; // max clicks accepted per 200ms window per client

class ClickAggregator {
  constructor() {
    this._buffer = [];
    this._socketCounts = new Map();
  }

  add({ x, y, socketId }) {
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
