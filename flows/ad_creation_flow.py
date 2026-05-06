"""
flows/ad_creation_flow.py
CrewAI Flow — orchestrates all 4 agents sequentially,
passing state between steps. Uses @start / @listen decorators
for clean event-driven chaining.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from crewai.flow.flow import Flow, listen, start
from crewai import Crew, Task
from pydantic import BaseModel

from agents import (
    create_ad_researcher,
    create_insight_extractor,
    create_script_writer,
    create_video_creator,
)
from config import settings
from utils.logger import get_logger

logger = get_logger("flow")


# ── Shared state model ────────────────────────────────────────────────────────

class AdCreationState(BaseModel):
    # Agent 1 outputs
    raw_ads_path: str = ""
    ads_summary: str = ""

    # Agent 2 outputs
    insights: str = ""

    # Agent 3 outputs
    script: str = ""
    scene_prompts: str = ""   # JSON array of image prompts

    # Agent 4 outputs
    audio_path: str = ""
    image_paths: list[str] = []

    # Final output
    video_path: str = ""
    success: bool = False


# ── Flow definition ───────────────────────────────────────────────────────────

class AdCreationFlow(Flow[AdCreationState]):
    """
    End-to-end ad creation pipeline.
    Step 1 → Research → Step 2 → Insights → Step 3 → Script → Step 4 → Video
    """

    # ── Step 1: Research top Meta ads ────────────────────────────────────────

    @start()
    def research_ads(self):
        logger.info("=" * 60)
        logger.info("STEP 1 — Researching top Meta ads via Apify")
        logger.info("=" * 60)

        researcher = create_ad_researcher()

        task = Task(
            description=(
                f"Search Meta Ad Library for the top performing ads related to: "
                f"'{settings.CWT_NICHE}' and '{settings.CWT_WEBSITE}'. "
                f"Focus on ads active in the last 30 days with the highest impressions. "
                f"Use keywords: 'trading signals, stock market alerts, financial freedom, "
                f"beat the market, trading community'. "
                f"Save results to JSON and return a summary of the top 10 ads "
                f"including their headlines, ad text, and estimated reach."
            ),
            expected_output=(
                "A structured summary of the top 10 best-performing Meta ads "
                "including: page name, headline, ad body text, CTA, estimated "
                "impressions, and the file path where full results were saved."
            ),
            agent=researcher,
        )

        crew = Crew(agents=[researcher], tasks=[task], verbose=True)
        result = crew.kickoff()

        self.state.ads_summary = str(result.raw)
        logger.info(f"Research complete. Summary length: {len(self.state.ads_summary)} chars")

        # Also load the saved JSON if it exists
        raw_ads_path = settings.JSON_DIR / "raw_ads.json"
        if raw_ads_path.exists():
            self.state.raw_ads_path = str(raw_ads_path)
            logger.info(f"Raw ads JSON: {raw_ads_path}")

        return self.state.ads_summary

    # ── Step 2: Extract marketing insights ───────────────────────────────────

    @listen(research_ads)
    def extract_insights(self, ads_summary: str):
        logger.info("=" * 60)
        logger.info("STEP 2 — Extracting marketing insights")
        logger.info("=" * 60)

        extractor = create_insight_extractor()

        # Load full ads JSON for richer context
        ads_context = ads_summary
        if self.state.raw_ads_path:
            try:
                ads_context = Path(self.state.raw_ads_path).read_text(encoding="utf-8")
            except Exception:
                pass

        task = Task(
            description=(
                f"Analyse these top-performing Meta ads and extract structured insights:\n\n"
                f"{ads_context[:6000]}\n\n"
                f"Extract and structure:\n"
                f"1. TOP 5 PAIN POINTS: The specific fears/frustrations being targeted\n"
                f"2. HOOK PATTERNS: Opening lines/techniques used (pattern interrupts, "
                f"questions, bold claims)\n"
                f"3. EMOTIONAL TRIGGERS: Primary emotions being activated (fear, greed, "
                f"FOMO, hope, trust)\n"
                f"4. PERSUASION FRAMEWORKS: Identify AIDA, PAS, storytelling arcs, etc.\n"
                f"5. CTA PATTERNS: Most common calls-to-action\n"
                f"6. VISUAL CONCEPTS: Types of imagery/videos that appear in winning ads\n"
                f"7. KEY MESSAGES: Core value propositions that repeat across winners"
            ),
            expected_output=(
                "A structured JSON document with 7 sections: pain_points, hook_patterns, "
                "emotional_triggers, persuasion_frameworks, cta_patterns, visual_concepts, "
                "key_messages. Each section should have 3-7 specific, actionable items."
            ),
            agent=extractor,
        )

        crew = Crew(agents=[extractor], tasks=[task], verbose=True)
        result = crew.kickoff()

        self.state.insights = str(result.raw)

        # Save insights to file
        insights_path = settings.JSON_DIR / "insights.json"
        insights_path.parent.mkdir(parents=True, exist_ok=True)
        insights_path.write_text(self.state.insights, encoding="utf-8")
        logger.info(f"Insights saved → {insights_path}")

        return self.state.insights

    # ── Step 3: Write the ad script ───────────────────────────────────────────

    @listen(extract_insights)
    def write_script(self, insights: str):
        logger.info("=" * 60)
        logger.info("STEP 3 — Writing 60-second ad script")
        logger.info("=" * 60)

        writer = create_script_writer()

        task = Task(
            description=(
                f"Write a 60-second video ad script for CrowdWisdomTrading.\n\n"
                f"MARKETING INSIGHTS FROM WINNING ADS:\n{insights[:3000]}\n\n"
                f"INSTRUCTIONS:\n"
                f"1. First, use the GoogleDriveFetcher tool to fetch our product data\n"
                f"2. Write the script using this EXACT structure with timestamps:\n"
                f"   - [0-5s]  HOOK: Scroll-stopping opening line\n"
                f"   - [5-15s] PAIN: Identify the core struggle\n"
                f"   - [15-25s] AGITATE: Make the pain more vivid\n"
                f"   - [25-40s] SOLUTION: Introduce CrowdWisdomTrading\n"
                f"   - [40-50s] PROOF: Social proof & results\n"
                f"   - [50-60s] CTA: Clear call to action\n\n"
                f"3. After the script, output a JSON array called SCENE_PROMPTS with "
                f"5 image generation prompts, one for each major scene.\n"
                f"   Format: SCENE_PROMPTS: [\"prompt1\", \"prompt2\", ...]\n\n"
                f"The script should be conversational, emotionally resonant, and "
                f"use the pain points and hooks from the winning ads research."
            ),
            expected_output=(
                "A complete 60-second video ad script with timestamps for each section, "
                "followed by SCENE_PROMPTS: a JSON array of 5 image generation prompts "
                "describing the visual for each scene."
            ),
            agent=writer,
        )

        crew = Crew(agents=[writer], tasks=[task], verbose=True)
        result = crew.kickoff()

        raw_output = str(result.raw)
        self.state.script, self.state.scene_prompts = self._parse_script_output(raw_output)

        # Save script
        script_path = settings.SCRIPTS_DIR / "ad_script.txt"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(raw_output, encoding="utf-8")
        logger.info(f"Script saved → {script_path}")

        return raw_output

    # ── Step 4: Generate video assets ────────────────────────────────────────

    @listen(write_script)
    def create_video_assets(self, script_output: str):
        logger.info("=" * 60)
        logger.info("STEP 4 — Generating video assets (images + audio)")
        logger.info("=" * 60)

        creator = create_video_creator()

        task = Task(
            description=(
                f"Generate all assets for the 60-second ad video.\n\n"
                f"AD SCRIPT (for voiceover):\n{self.state.script}\n\n"
                f"IMAGE PROMPTS (for scene generation):\n{self.state.scene_prompts}\n\n"
                f"INSTRUCTIONS:\n"
                f"1. Call AdImageGenerator with the scene prompts JSON array\n"
                f"2. Call ElevenLabsVoiceover with the full ad script text\n"
                f"   (voiceover-only text, no timestamps or stage labels)\n"
                f"3. Report all generated file paths clearly\n\n"
                f"For the voiceover, extract ONLY the spoken words from the script "
                f"(remove timestamps like [0-5s], remove section labels like HOOK:)."
            ),
            expected_output=(
                "Confirmation that both tools have been called successfully, "
                "with the exact file paths for: all generated scene images "
                "and the voiceover MP3 file."
            ),
            agent=creator,
        )

        crew = Crew(agents=[creator], tasks=[task], verbose=True)
        result = crew.kickoff()

        output_text = str(result.raw)
        self._extract_asset_paths(output_text)

        logger.info(f"Audio path: {self.state.audio_path}")
        logger.info(f"Image paths: {self.state.image_paths}")

        return output_text

    # ── Step 5: Render with Remotion ─────────────────────────────────────────

    @listen(create_video_assets)
    def render_video(self, assets_output: str):
        logger.info("=" * 60)
        logger.info("STEP 5 — Rendering video with Remotion")
        logger.info("=" * 60)

        video_path = self._run_remotion_render()
        self.state.video_path = str(video_path)
        self.state.success = True

        # Save final pipeline summary
        summary = {
            "status": "success",
            "raw_ads_path": self.state.raw_ads_path,
            "insights_path": str(settings.JSON_DIR / "insights.json"),
            "script_path": str(settings.SCRIPTS_DIR / "ad_script.txt"),
            "audio_path": self.state.audio_path,
            "image_paths": self.state.image_paths,
            "video_path": self.state.video_path,
        }
        summary_path = settings.OUTPUT_DIR / "pipeline_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        logger.info(f"Pipeline complete! Video → {self.state.video_path}")
        logger.info(f"Summary → {summary_path}")
        return self.state.video_path

    # ── Private helpers ───────────────────────────────────────────────────────

    # Default scene prompts used when LLM doesn't output SCENE_PROMPTS tag
    DEFAULT_SCENE_PROMPTS = [
        "stressed young professional losing money on stock market, dark moody lighting, cinematic",
        "person looking frustrated at phone with red market chart, dramatic shadows",
        "crowdwisdomtrading app on phone showing green profits and trading signals, bright hopeful",
        "happy trader celebrating portfolio gains at desk, warm golden lighting, success",
        "phone screen showing crowdwisdomtrading community dashboard, 50000 members, vibrant colors",
    ]

    def _parse_script_output(self, raw: str) -> tuple[str, str]:
        """
        Split raw agent output into clean voiceover script and scene prompts JSON.
        If LLM doesn't output SCENE_PROMPTS tag (common with free models),
        falls back to DEFAULT_SCENE_PROMPTS so image generation always has input.
        """
        import re

        script = raw
        scene_prompts = "[]"

        # Try to extract SCENE_PROMPTS from LLM output
        if "SCENE_PROMPTS:" in raw:
            parts = raw.split("SCENE_PROMPTS:", 1)
            script = parts[0].strip()
            prompts_raw = parts[1].strip()
            start = prompts_raw.find("[")
            end = prompts_raw.rfind("]") + 1
            if start >= 0 and end > start:
                candidate = prompts_raw[start:end]
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, list) and len(parsed) > 0:
                        scene_prompts = candidate
                        logger.info(f"Extracted {len(parsed)} scene prompts from LLM output")
                except json.JSONDecodeError:
                    pass

        # FALLBACK: LLM didn't produce valid SCENE_PROMPTS — use defaults
        if scene_prompts == "[]":
            scene_prompts = json.dumps(self.DEFAULT_SCENE_PROMPTS)
            logger.warning(
                "LLM did not output SCENE_PROMPTS tag — using default trading scene prompts"
            )

        # Clean voiceover script: strip timestamps and section labels
        clean_script = re.sub(r"\[\d+-\d+s\]", "", script)
        clean_script = re.sub(r"\*\*(HOOK|PAIN|AGITATE|SOLUTION|PROOF|CTA)\*\*:", "", clean_script)
        clean_script = re.sub(r"(HOOK|PAIN|AGITATE|SOLUTION|PROOF|CTA):", "", clean_script)
        clean_script = re.sub(r"\n{3,}", "\n\n", clean_script).strip()

        logger.info(f"Script: {len(clean_script)} chars | Prompts: {scene_prompts[:80]}")
        return clean_script, scene_prompts

    def _extract_asset_paths(self, output_text: str):
        """
        Always scan disk directly for generated assets — never parse LLM text.
        Filters out placeholder .txt files (only keeps real .png images).
        Pads image list to 5 if some failed, by repeating last available image.
        """
        # ── Audio: scan output/audio/ for any .mp3 ───────────────────────────
        mp3s = sorted(settings.AUDIO_DIR.glob("*.mp3"))
        if mp3s:
            self.state.audio_path = str(mp3s[0])
            logger.info(f"Found audio: {self.state.audio_path}")
        else:
            logger.warning("No .mp3 found in output/audio/ — voiceover missing")

        # ── Images: scan output/images/ for real .png only ───────────────────
        # Filter out .txt placeholders — only real PNG images are valid
        real_images = sorted(settings.IMAGES_DIR.glob("scene_*.png"))
        self.state.image_paths = [str(p) for p in real_images]
        logger.info(f"Found {len(self.state.image_paths)} real PNG images")

        # FIX 3 — Pad to 5 images by repeating last available (avoids missing scene crash)
        if self.state.image_paths:
            while len(self.state.image_paths) < 5:
                self.state.image_paths.append(self.state.image_paths[-1])
                logger.warning("Padded missing image with last available scene")
        else:
            logger.warning("No PNG images found at all — video will have black scenes")

    def _copy_assets_to_public(self, remotion_dir: Path) -> tuple[list[str], str]:
        """
        FIX 1 + FIX 2 — Copy assets into remotion_project/public/ and
        return Remotion-compatible relative paths (/images/..., /audio/...).
        Remotion's staticFile() ONLY accepts paths relative to /public — never absolute.
        """
        import shutil

        public_images_dir = remotion_dir / "public" / "images"
        public_audio_dir = remotion_dir / "public" / "audio"
        public_images_dir.mkdir(parents=True, exist_ok=True)
        public_audio_dir.mkdir(parents=True, exist_ok=True)

        # Copy images → remotion_project/public/images/
        relative_image_paths = []
        seen_names: set[str] = set()
        for abs_path in self.state.image_paths:
            src = Path(abs_path)
            if not src.exists() or not src.suffix == ".png":
                logger.warning(f"Skipping missing/invalid image: {abs_path}")
                continue
            dest_name = src.name
            # Deduplicate names when padding caused repeats
            if dest_name in seen_names:
                stem = src.stem
                ext = src.suffix
                dest_name = f"{stem}_{len(seen_names)}{ext}"
            seen_names.add(dest_name)
            shutil.copy2(str(src), str(public_images_dir / dest_name))
            relative_image_paths.append(f"/images/{dest_name}")
            logger.info(f"Copied image → public/images/{dest_name}")

        # Copy audio → remotion_project/public/audio/
        relative_audio_path = ""
        if self.state.audio_path:
            src_audio = Path(self.state.audio_path)
            if src_audio.exists():
                shutil.copy2(str(src_audio), str(public_audio_dir / src_audio.name))
                relative_audio_path = f"/audio/{src_audio.name}"
                logger.info(f"Copied audio → public/audio/{src_audio.name}")
            else:
                logger.warning(f"Audio file not found: {self.state.audio_path}")

        return relative_image_paths, relative_audio_path

    def _run_remotion_render(self) -> Path:
        """
        1. Copies all assets into remotion_project/public/
        2. Converts absolute OS paths → Remotion-relative /images/ /audio/ paths
        3. Writes props.json with clean relative paths
        4. Runs npx remotion render with Windows-compatible npx path
        """
        import shutil

        remotion_dir = settings.BASE_DIR / "remotion_project"

        # FIX 1 + FIX 2 — copy assets and get relative paths
        relative_image_paths, relative_audio_path = self._copy_assets_to_public(remotion_dir)

        if not relative_image_paths:
            logger.error("No valid images to render — aborting Remotion render")
            return settings.VIDEOS_DIR / "cwt_ad.mp4"

        # Write props.json with RELATIVE paths only (never absolute)
        props_path = remotion_dir / "props.json"
        props = {
            "audioPath": relative_audio_path,       # e.g. "/audio/voiceover.mp3"
            "imagePaths": relative_image_paths,      # e.g. ["/images/scene_01.png"]
            "script": self.state.script,
            "durationSeconds": settings.AD_DURATION_SECONDS,
        }
        props_path.write_text(json.dumps(props, indent=2), encoding="utf-8")
        logger.info(f"Remotion props written → {props_path}")
        logger.info(f"Audio path in props: {relative_audio_path}")
        logger.info(f"Image paths in props: {relative_image_paths}")

        output_mp4 = settings.VIDEOS_DIR / "cwt_ad.mp4"
        output_mp4.parent.mkdir(parents=True, exist_ok=True)

        # FIX — Windows needs npx.cmd; Unix uses npx
        # shutil.which() finds the correct executable on any OS
        npx_cmd = shutil.which("npx") or shutil.which("npx.cmd") or "npx"
        logger.info(f"Using npx at: {npx_cmd}")

        cmd = [
            npx_cmd, "remotion", "render",
            "src/index.ts",
            "CWTAd",
            str(output_mp4),
            "--props", str(props_path),
        ]

        logger.info(f"Running Remotion render...")
        try:
            result = subprocess.run(
                cmd,
                cwd=str(remotion_dir),
                capture_output=True,
                text=True,
                timeout=300,
                shell=False,
            )
            if result.returncode != 0:
                logger.error(f"Remotion stderr:\n{result.stderr[-2000:]}")
                logger.error(f"Remotion stdout:\n{result.stdout[-1000:]}")
                logger.warning("Remotion render failed — all other assets are still saved")
            else:
                logger.info(f"✓ Remotion render success → {output_mp4}")
        except FileNotFoundError:
            logger.error(
                "npx not found on PATH. Make sure Node.js is installed "
                "and 'cd remotion_project && npm install' has been run."
            )
        except subprocess.TimeoutExpired:
            logger.error("Remotion render timed out after 5 minutes")

        return output_mp4