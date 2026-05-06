import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
} from "remotion";

// ── Types ─────────────────────────────────────────────────────────────────────

interface CWTAdProps {
  audioPath: string;       // Relative path e.g. "/audio/voiceover.mp3"
  imagePaths: string[];    // Relative paths e.g. ["/images/scene_01.png"]
  script: string;
  durationSeconds: number;
}

// ── Subtitle generator ────────────────────────────────────────────────────────

function splitIntoSubtitleChunks(script: string): string[] {
  const words = script.split(/\s+/).filter(Boolean);
  const chunks: string[] = [];
  for (let i = 0; i < words.length; i += 5) {
    chunks.push(words.slice(i, i + 5).join(" "));
  }
  return chunks;
}

// ── Scene component ───────────────────────────────────────────────────────────

interface SceneProps {
  // relativePath must start with "/" e.g. "/images/scene_01.png"
  relativePath: string;
  startFrame: number;
  endFrame: number;
}

const Scene: React.FC<SceneProps> = ({ relativePath, startFrame, endFrame }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Ken Burns zoom effect
  const scale = interpolate(frame, [startFrame, endFrame], [1.0, 1.08], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Fade in/out
  const opacity = interpolate(
    frame,
    [startFrame, startFrame + fps * 0.4, endFrame - fps * 0.4, endFrame],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ opacity }}>
      <Img
        // FIX: staticFile() resolves paths relative to /public folder
        // Never pass absolute OS paths here — they will crash the renderer
        src={staticFile(relativePath)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale})`,
          transformOrigin: "center center",
        }}
      />
      {/* Dark gradient overlay for text readability */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to bottom, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.55) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

// ── Subtitle component ────────────────────────────────────────────────────────

interface SubtitleProps {
  chunks: string[];
  totalFrames: number;
}

const Subtitles: React.FC<SubtitleProps> = ({ chunks, totalFrames }) => {
  const frame = useCurrentFrame();
  const framesPerChunk = Math.floor(totalFrames / Math.max(chunks.length, 1));
  const currentChunkIndex = Math.min(
    Math.floor(frame / framesPerChunk),
    chunks.length - 1
  );
  const currentChunk = chunks[currentChunkIndex] || "";

  const chunkStart = currentChunkIndex * framesPerChunk;
  const wordOpacity = interpolate(
    frame,
    [chunkStart, chunkStart + 4],
    [0, 1],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: 160,
      }}
    >
      <div style={{ opacity: wordOpacity, textAlign: "center", padding: "16px 32px", maxWidth: "90%" }}>
        <div style={{ background: "rgba(0,0,0,0.65)", borderRadius: 12, padding: "12px 24px" }}>
          <span
            style={{
              fontFamily: "'Arial Black', Arial, sans-serif",
              fontSize: 56,
              fontWeight: 900,
              color: "#FFFFFF",
              textTransform: "uppercase",
              letterSpacing: 1,
              lineHeight: 1.2,
              textShadow: "2px 2px 8px rgba(0,0,0,0.9)",
            }}
          >
            {currentChunk}
          </span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── CTA Overlay ───────────────────────────────────────────────────────────────

const CTAOverlay: React.FC<{ frame: number; totalFrames: number }> = ({ frame, totalFrames }) => {
  const ctaStart = Math.floor(totalFrames * 0.83);
  const opacity = interpolate(frame, [ctaStart, ctaStart + 15], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  if (frame < ctaStart) return null;

  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 60, opacity }}>
      <div style={{ background: "linear-gradient(135deg, #F7B731, #F0932B)", borderRadius: 50, padding: "24px 60px", boxShadow: "0 8px 32px rgba(247,183,49,0.5)" }}>
        <span style={{ fontFamily: "'Arial Black', Arial, sans-serif", fontSize: 48, fontWeight: 900, color: "#1a1a1a", textTransform: "uppercase", letterSpacing: 2 }}>
          Start Free Trial →
        </span>
      </div>
    </AbsoluteFill>
  );
};

// ── Branding Bug ──────────────────────────────────────────────────────────────

const BrandingBug: React.FC = () => (
  <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: 40 }}>
    <div style={{ background: "rgba(0,0,0,0.7)", borderRadius: 12, padding: "10px 20px", border: "2px solid #F7B731" }}>
      <span style={{ fontFamily: "Arial, sans-serif", fontSize: 28, fontWeight: 700, color: "#F7B731", letterSpacing: 1 }}>
        CrowdWisdomTrading
      </span>
    </div>
  </AbsoluteFill>
);

// ── Main Composition ──────────────────────────────────────────────────────────

export const CWTAd: React.FC<CWTAdProps> = ({
  audioPath,
  imagePaths,
  script,
  durationSeconds,
}) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const totalFrames = durationSeconds * fps;

  const sceneCount = Math.max(imagePaths.length, 1);
  const framesPerScene = Math.floor(totalFrames / sceneCount);
  const subtitleChunks = splitIntoSubtitleChunks(script);

  return (
    <AbsoluteFill style={{ background: "#000000" }}>

      {/* ── Audio track — uses staticFile() with relative path ─────────── */}
      {audioPath && (
        <Audio
          src={staticFile(audioPath)}
          startFrom={0}
          volume={1}
        />
      )}

      {/* ── Scene images with Ken Burns ────────────────────────────────── */}
      {imagePaths.map((relativePath, i) => {
        const start = i * framesPerScene;
        const end = i === sceneCount - 1 ? totalFrames : (i + 1) * framesPerScene;
        return (
          <Sequence key={i} from={start} durationInFrames={end - start}>
            <Scene relativePath={relativePath} startFrame={start} endFrame={end} />
          </Sequence>
        );
      })}

      {/* ── Branding bug ───────────────────────────────────────────────── */}
      <BrandingBug />

      {/* ── Karaoke subtitles ──────────────────────────────────────────── */}
      <Subtitles chunks={subtitleChunks} totalFrames={totalFrames} />

      {/* ── CTA button (last ~10s) ─────────────────────────────────────── */}
      <CTAOverlay frame={frame} totalFrames={totalFrames} />

    </AbsoluteFill>
  );
};