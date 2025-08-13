import { Frame, ICameraFrameProvider } from "./ICameraFrameProvider";

export class RealCameraFrameProvider implements ICameraFrameProvider {
  async getLatestFrame(): Promise<Frame> {
    return { path: "", timestamp: Date.now() };
  }
}
export class TestCameraFrameProvider implements ICameraFrameProvider {
  async getLatestFrame(): Promise<Frame> {
    return { path: "test.jpg", timestamp: Date.now() };
  }
}
