const { execFile } = require("child_process");
const path = require("path");

const PYTHON_SCRIPT = path.resolve(__dirname, "../../backend/cluster_worker.py");

class HotspotBroadcaster {
  constructor(io) {
    this._io = io;
  }

  /**
   * Sends batch to Python worker, returns parsed hotspot array or null.
   * Python worker reads JSON from stdin, writes JSON to stdout.
   */
  computeAndBroadcast(batch) {
    return new Promise((resolve) => {
      const child = execFile(
        "python3",
        [PYTHON_SCRIPT],
        { timeout: 180 },
        (err, stdout, stderr) => {
          if (err) {
            console.error("[broadcaster] python error:", stderr);
            return resolve(null);
          }
          try {
            resolve(JSON.parse(stdout));
          } catch {
            console.error("[broadcaster] bad JSON from python");
            resolve(null);
          }
        }
      );
      child.stdin.write(JSON.stringify(batch));
      child.stdin.end();
    });
  }
}

module.exports = { HotspotBroadcaster };
