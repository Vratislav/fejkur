import { promises as fs } from "fs";
import path from "path";
import { Frame, ICameraFrameProvider } from "./ICameraFrameProvider";
import { grabFrame, grabFrameWithOptions } from "../cameraUtils";

export class RealCameraFrameProvider implements ICameraFrameProvider {
  private rtspUrl: string;
  private timeoutId?: NodeJS.Timeout;
  private latestFrame?: Frame;
  private isRunning: boolean = false;
  private frameGrabInterval: number;

  constructor(rtspUrl: string, frameGrabInterval: number = 1000) {
    this.rtspUrl = rtspUrl;
    this.frameGrabInterval = frameGrabInterval;
  }

  /**
   * Starts the continuous frame grabbing loop
   */
  start(): void {
    if (this.isRunning) {
      console.log("RealCameraFrameProvider is already running");
      return;
    }

    this.isRunning = true;
    console.log(
      `Starting RealCameraFrameProvider with interval: ${this.frameGrabInterval}ms`
    );

    // Start the frame grabbing loop
    this.scheduleNextFrameGrab();
  }

  /**
   * Stops the continuous frame grabbing loop
   */
  stop(): void {
    if (!this.isRunning) {
      console.log("RealCameraFrameProvider is not running");
      return;
    }

    this.isRunning = false;
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = undefined;
    }
    console.log("RealCameraFrameProvider stopped");
  }

  /**
   * Private method to schedule the next frame grab
   */
  private scheduleNextFrameGrab(): void {
    if (!this.isRunning) return;

    this.timeoutId = setTimeout(async () => {
      await this.grabAndStoreFrame();
      // Schedule the next frame grab after this one completes
      this.scheduleNextFrameGrab();
    }, this.frameGrabInterval);
  }

  /**
   * Private method to grab a frame and store it
   */
  private async grabAndStoreFrame(): Promise<void> {
    try {
      const framePath = await grabFrame(this.rtspUrl);

      this.latestFrame = {
        path: framePath,
        timestamp: Date.now(),
      };

      //console.log(`Frame grabbed and stored: ${framePath}`);
    } catch (error) {
      console.error("Error grabbing frame:", error);
      // Keep the previous frame if available, don't crash the loop
    }
  }

  async getLatestFrame(): Promise<Frame> {
    if (!this.latestFrame) {
      // If no frame has been grabbed yet, try to grab one immediately
      if (!this.isRunning) {
        throw new Error(
          "RealCameraFrameProvider not started. Call start() first."
        );
      }

      // Wait a bit for the first frame to be grabbed
      let attempts = 0;
      const maxAttempts = 300;
      while (!this.latestFrame && attempts < maxAttempts) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        attempts++;
      }

      if (!this.latestFrame) {
        throw new Error("No frames available. Check camera connection.");
      }
    }

    return this.latestFrame;
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
