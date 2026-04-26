require("dotenv").config();
const express = require("express");
const { createServer } = require("http");
const cors = require("cors");
const { initSocket } = require("./websocket/socket");

const app = express();
app.use(cors({ origin: process.env.FRONTEND_ORIGIN || "*" }));
app.use(express.json());

app.get("/health", (_req, res) => res.json({ status: "ok" }));

const httpServer = createServer(app);
initSocket(httpServer);

const PORT = process.env.PORT || 3001;
httpServer.listen(PORT, () => {
  console.log(`[server] listening on :${PORT}`);
});
