export interface Point {
  x: number;
  y: number;
}

export interface GeoJSONPolygon {
  type: "Polygon";
  coordinates: number[][][];
}

export interface Hotspot {
  id: number;
  centroid: Point;
  intensity: number;   // 0–100, sum across displayed hotspots == 100
  pointCount: number;
  polygon: GeoJSONPolygon | null;
}

export interface HotspotsPayload {
  hotspots: Hotspot[];
  ts: number;
}
