export interface ICameraFrameProvider {
  getLatestFrame(): Promise<Frame>;
}

export interface Frame {
  path: string;
  timestamp: number;
}
