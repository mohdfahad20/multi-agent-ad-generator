"""
agents/video_creator.py
Agent 4 — Video Creator
Orchestrates image generation (HuggingFace), voiceover (ElevenLabs),
and triggers the Remotion render to produce the final 60-second MP4.
"""

from crewai import Agent

from tools.elevenlabs_tool import ElevenLabsTool
from tools.image_gen_tool import ImageGenTool
from utils.llm import get_llm
from utils.logger import get_logger

logger = get_logger("agent.videocreator")


def create_video_creator() -> Agent:
    logger.info("Creating Video Creator agent")

    return Agent(
        role="AI Video Production Director",
        goal=(
            "Produce all assets for the 60-second ad video: "
            "(1) Generate scene images from the provided prompts using AdImageGenerator, "
            "(2) Generate the voiceover audio from the script using ElevenLabsVoiceover, "
            "(3) Report all asset paths so the Remotion renderer can assemble the final video. "
            "Ensure each tool is called exactly once and all output paths are confirmed."
        ),
        backstory=(
            "You are an AI-powered video production director who specialises in "
            "assembling programmatic ad videos. You coordinate image generation, "
            "voice synthesis, and video composition pipelines with military precision. "
            "You understand that every asset must be created, verified, and handed "
            "off correctly for the final render to succeed. You never skip steps "
            "and always confirm file paths before declaring the job done."
        ),
        tools=[ImageGenTool(), ElevenLabsTool()],
        llm=get_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )