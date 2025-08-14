import { readFile } from "fs/promises";
import sharp from "sharp";

export async function frameToLLMInput(framePath: string) {
  // Read the original image
  const originalBuffer = await readFile(framePath);

  // Get original image metadata to calculate 50% dimensions
  const metadata = await sharp(originalBuffer).metadata();
  const newWidth = Math.round((metadata.width || 0) * 0.33);
  const newHeight = Math.round((metadata.height || 0) * 0.33);

  // Resize image to 50% and convert to buffer
  const resizedBuffer = await sharp(originalBuffer)
    .resize(newWidth, newHeight)
    .jpeg({ quality: 85 }) // Maintain good quality
    .toBuffer();

  return {
    media: {
      url: `data:image/jpeg;base64,${resizedBuffer.toString("base64")}`,
    },
  };
}
