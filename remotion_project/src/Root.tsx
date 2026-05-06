import React from "react";
import { Composition } from "remotion";
import { CWTAd, CWTAdProps } from "./CWTAd";

const fps = 30;

const defaultProps: CWTAdProps = {
  audioPath: "/audio/voiceover.mp3",     // ✅ FIXED
  imagePaths: [
    "/images/scene_01.png",              // ✅ FIXED
    "/images/scene_02.png",
    "/images/scene_03.png",
    "/images/scene_04.png",
    "/images/scene_05.png",
  ],
  script: "Your ad script here",
  durationSeconds: 60,
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="CWTAd"
      component={CWTAd}
      durationInFrames={defaultProps.durationSeconds * fps}
      fps={fps}
      width={1080}
      height={1920}
      defaultProps={defaultProps}
    />
  );
};