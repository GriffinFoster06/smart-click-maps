import { useEffect, useRef } from "react";
import { HotspotRenderer } from "../renderers/HotspotRenderer";
import { useHotspots } from "../hooks/useHotspots";

export function ClickOverlay() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rendererRef = useRef<HotspotRenderer | null>(null);
  const { hotspots, sendClick } = useHotspots();

  useEffect(() => {
    if (!canvasRef.current) return;
    rendererRef.current = new HotspotRenderer(canvasRef.current);
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      rendererRef.current?.resize(width, height);
    });
    ro.observe(canvasRef.current);
    return () => {
      ro.disconnect();
      rendererRef.current?.dispose();
    };
  }, []);

  useEffect(() => {
    rendererRef.current?.update(hotspots);
  }, [hotspots]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = (e.target as HTMLCanvasElement).getBoundingClientRect();
    sendClick(
      (e.clientX - rect.left) / rect.width,
      (e.clientY - rect.top) / rect.height
    );
  };

  return (
    <canvas
      ref={canvasRef}
      onClick={handleClick}
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
    />
  );
}
