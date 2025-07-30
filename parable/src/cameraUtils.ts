import ffmpeg from "fluent-ffmpeg";
import * as fs from "fs-extra";
import * as path from "path";

/**
 * Creates a valid RTSP URL from its components
 * @param hostname - The hostname or IP address of the camera
 * @param login - The username for authentication
 * @param password - The password for authentication
 * @param port - The port number (default: 554)
 * @param path - The stream path (default: "/stream")
 * @returns The complete RTSP URL
 */
export function createRtspUrl(
  hostname: string,
  login: string,
  password: string,
  port: number = 554,
  path: string = "/stream"
): string {
  return `rtsp://${login}:${password}@${hostname}:${port}${path}`;
}

/**
 * Grabs a frame from an RTSP camera stream and saves it to the frames folder
 * @param rtspUrl - The RTSP URL of the camera stream
 * @returns Promise<string> - The path to the saved frame file
 */
export async function grabFrame(rtspUrl: string): Promise<string> {
  try {
    // Create frames directory if it doesn't exist
    const framesDir = path.join(process.cwd(), "frames");
    await fs.ensureDir(framesDir);

    // Generate timestamp-based filename for alphabetical ordering
    const timestamp = new Date()
      .toISOString()
      .replace(/:/g, "-")
      .replace(/\./g, "-")
      .replace("T", "_")
      .replace("Z", "");

    const filename = `frame_${timestamp}.jpg`;
    const filePath = path.join(framesDir, filename);

    console.log(`Grabbing frame from RTSP stream: ${rtspUrl}`);
    console.log(`Saving to: ${filePath}`);

    return new Promise((resolve, reject) => {
      ffmpeg(rtspUrl)
        .inputOptions([
          "-rtsp_transport",
          "tcp", // Use TCP for more reliable connection
          "-timeout",
          "5000000", // 5 second timeout in microseconds
        ])
        .outputOptions([
          "-vframes",
          "1", // Capture only 1 frame
          "-f",
          "image2", // Output format
          "-q:v",
          "2", // High quality
        ])
        .output(filePath)
        .on("end", () => {
          console.log(`Frame successfully saved: ${filename}`);
          resolve(filePath);
        })
        .on("error", (err) => {
          console.error("Error grabbing frame:", err.message);
          reject(new Error(`Failed to grab frame: ${err.message}`));
        })
        .run();
    });
  } catch (error) {
    console.error("Error in grabFrame function:", error);
    throw new Error(`Frame grabbing failed: ${error}`);
  }
}

/**
 * Alternative function to grab frame with custom settings
 * @param rtspUrl - The RTSP URL of the camera stream
 * @param options - Custom options for frame grabbing
 */
export async function grabFrameWithOptions(
  rtspUrl: string,
  options: {
    filename?: string;
    quality?: number;
    timeout?: number;
    format?: "jpg" | "png";
  } = {}
): Promise<string> {
  const {
    filename = `frame_${Date.now()}.jpg`,
    quality = 2,
    timeout = 5000000,
    format = "jpg",
  } = options;

  const framesDir = path.join(process.cwd(), "frames");
  await fs.ensureDir(framesDir);

  const filePath = path.join(framesDir, filename);

  return new Promise((resolve, reject) => {
    ffmpeg(rtspUrl)
      .inputOptions([
        "-rtsp_transport",
        "tcp",
        "-timeout",
        timeout.toString(),
        "-reconnect",
        "1",
      ])
      .outputOptions([
        "-vframes",
        "1",
        "-f",
        "image2",
        "-q:v",
        quality.toString(),
      ])
      .output(filePath)
      .on("end", () => resolve(filePath))
      .on("error", (err) =>
        reject(new Error(`Failed to grab frame: ${err.message}`))
      )
      .run();
  });
}
