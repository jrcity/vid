declare module '@vladmandic/face-api' {
  export interface TinyFaceDetectorOptions {
    inputSize?: number;
    scoreThreshold?: number;
  }

  export interface Box {
    x: number;
    y: number;
    width: number;
    height: number;
  }

  export interface FaceDetection {
    box: Box;
    score: number;
  }

  export const nets: {
    tinyFaceDetector: {
      loadFromUri(uri: string): Promise<void>;
    };
  };

  export class TinyFaceDetectorOptions {
    constructor(options?: TinyFaceDetectorOptions);
  }

  export function detectSingleFace(
    input: HTMLVideoElement,
    options: TinyFaceDetectorOptions,
  ): Promise<FaceDetection | undefined>;
}
