/**
 * WebGL renderer for hotspot polygons using Three.js.
 * Each hotspot is a filled ShapeGeometry with opacity keyed to intensity.
 */
import * as THREE from "three";
import type { Hotspot } from "../../../shared/types/hotspot";

const COLORS = [0xff4500, 0xff8c00, 0xffd700, 0x00ced1, 0x7b68ee];

export class HotspotRenderer {
  private scene: THREE.Scene;
  private camera: THREE.OrthographicCamera;
  private renderer: THREE.WebGLRenderer;
  private meshes: Map<number, THREE.Mesh> = new Map();

  constructor(canvas: HTMLCanvasElement) {
    this.renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
    this.scene = new THREE.Scene();
    this.camera = new THREE.OrthographicCamera(0, 1, 1, 0, -1, 1);
    this.renderer.setPixelRatio(window.devicePixelRatio);
  }

  resize(w: number, h: number): void {
    this.renderer.setSize(w, h);
  }

  update(hotspots: Hotspot[]): void {
    const seen = new Set<number>();

    for (const hs of hotspots) {
      seen.add(hs.id);
      if (hs.polygon == null) continue;

      const shape = this._polygonToShape(hs.polygon.coordinates[0]);
      const geo = new THREE.ShapeGeometry(shape);
      const mat = new THREE.MeshBasicMaterial({
        color: COLORS[hs.id % COLORS.length],
        transparent: true,
        opacity: 0.35 + 0.45 * (hs.intensity / 100),
      });

      if (this.meshes.has(hs.id)) {
        const old = this.meshes.get(hs.id)!;
        old.geometry.dispose();
        (old.material as THREE.Material).dispose();
        this.scene.remove(old);
      }

      const mesh = new THREE.Mesh(geo, mat);
      this.scene.add(mesh);
      this.meshes.set(hs.id, mesh);
    }

    // Remove stale meshes
    for (const [id, mesh] of this.meshes) {
      if (!seen.has(id)) {
        mesh.geometry.dispose();
        (mesh.material as THREE.Material).dispose();
        this.scene.remove(mesh);
        this.meshes.delete(id);
      }
    }

    this.renderer.render(this.scene, this.camera);
  }

  private _polygonToShape(ring: number[][]): THREE.Shape {
    const shape = new THREE.Shape();
    shape.moveTo(ring[0][0], ring[0][1]);
    for (let i = 1; i < ring.length; i++) {
      shape.lineTo(ring[i][0], ring[i][1]);
    }
    shape.closePath();
    return shape;
  }

  dispose(): void {
    this.renderer.dispose();
  }
}
