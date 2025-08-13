import { promises as fs } from "fs";
import path from "path";
import { Frame, ICameraFrameProvider } from "./ICameraFrameProvider";

export class RealCameraFrameProvider implements ICameraFrameProvider {
  async getLatestFrame(): Promise<Frame> {
    return { path: "", timestamp: Date.now() };
  }
}
export class TestCameraFrameProvider implements ICameraFrameProvider {
  private frameRelativePaths: string[] = [];
  private currentIndex: number = 0;
  private initialized: boolean = false;
  private initPromise?: Promise<void>;

  private async initialize(): Promise<void> {
    if (this.initialized) return;
    if (this.initPromise) return this.initPromise;

    this.initPromise = (async () => {
      const framesDirAbsolute = path.resolve(process.cwd(), "frames");
      const entries = await fs.readdir(framesDirAbsolute, {
        withFileTypes: true,
      });
      const imageExtensions = new Set([
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".gif",
        ".webp",
      ]);
      const files = entries
        .filter((e) => e.isFile())
        .map((e) => e.name)
        .filter((name) => imageExtensions.has(path.extname(name).toLowerCase()))
        .sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));

      if (files.length === 0) {
        throw new Error(
          `No image frames found in directory: ${framesDirAbsolute}`
        );
      }

      // Store as relative paths like "frames/filename.jpg" so downstream can resolve them
      this.frameRelativePaths = files.map((name) => path.join("frames", name));
      this.currentIndex = 0;
      this.initialized = true;
    })();

    return this.initPromise;
  }

  async getLatestFrame(): Promise<Frame> {
    await this.initialize();
    const framePath = this.frameRelativePaths[this.currentIndex];
    this.currentIndex =
      (this.currentIndex + 1) % this.frameRelativePaths.length;
    console.log("TCFP serving:  ", framePath);
    return { path: framePath, timestamp: Date.now() };
  }
}
