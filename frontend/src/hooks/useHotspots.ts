import { useEffect, useRef, useState } from "react";
import { io, Socket } from "socket.io-client";
import type { Hotspot, HotspotsPayload } from "../../../shared/types/hotspot";

const SERVER_URL = import.meta.env.VITE_SERVER_URL ?? "http://localhost:3001";

export function useHotspots() {
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    const socket = io(SERVER_URL, { transports: ["websocket"] });
    socketRef.current = socket;

    socket.on("hotspots", (payload: HotspotsPayload) => {
      setHotspots(payload.hotspots);
    });

    return () => { socket.disconnect(); };
  }, []);

  const sendClick = (x: number, y: number) => {
    socketRef.current?.emit("click", { x, y });
  };

  return { hotspots, sendClick };
}
