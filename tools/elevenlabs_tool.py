"""
tools/elevenlabs_tool.py
Generates voiceover audio from ad script text using ElevenLabs API.
Saves MP3 to output/audio/voiceover.mp3
"""

import json
from pathlib import Path
from typing import Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from utils.logger import get_logger

logger = get_logger("elevenlabs_tool")

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


class ElevenLabsToolInput(BaseModel):
    script: str = Field(description="The ad script text to convert to voiceover audio")
    voice_id: str = Field(
        default="",
        description="ElevenLabs voice ID. Defaults to ELEVENLABS_VOICE_ID from env.",
    )


class ElevenLabsTool(BaseTool):
    """
    Converts ad script text to a professional voiceover MP3
    using ElevenLabs text-to-speech API.
    Free tier: 10,000 characters/month.
    """

    name: str = "ElevenLabsVoiceover"
    description: str = (
        "Converts an ad script to a professional voiceover MP3 file "
        "using ElevenLabs TTS. Returns the path to the saved audio file."
    )
    args_schema: Type[BaseModel] = ElevenLabsToolInput

    def _run(self, script: str, voice_id: str = "") -> str:
        vid = voice_id or settings.ELEVENLABS_VOICE_ID
        logger.info(f"Generating voiceover | chars={len(script)} | voice={vid}")

        if not settings.ELEVENLABS_API_KEY:
            logger.warning("No ElevenLabs key — creating placeholder audio file")
            return self._create_placeholder(script)

        try:
            audio_path = self._generate_audio(script, vid)
            logger.info(f"Voiceover saved → {audio_path}")
            return json.dumps({"status": "success", "audio_path": str(audio_path)})
        except Exception as e:
            logger.error(f"ElevenLabs failed: {e}", exc_info=True)
            return json.dumps({"status": "error", "message": str(e)})

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    def _generate_audio(self, script: str, voice_id: str) -> Path:
        url = ELEVENLABS_TTS_URL.format(voice_id=voice_id)
        headers = {
            "xi-api-key": settings.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": script,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
                "style": 0.3,
                "use_speaker_boost": True,
            },
        }

        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        output_path = settings.AUDIO_DIR / "voiceover.mp3"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)
        return output_path

    def _create_placeholder(self, script: str) -> str:
        """Create a placeholder text file when API key is missing."""
        placeholder = settings.AUDIO_DIR / "voiceover_PLACEHOLDER.txt"
        placeholder.parent.mkdir(parents=True, exist_ok=True)
        placeholder.write_text(
            f"[PLACEHOLDER AUDIO]\nScript text:\n\n{script}\n\n"
            "Add ELEVENLABS_API_KEY to .env to generate real audio.",
            encoding="utf-8",
        )
        return json.dumps(
            {
                "status": "placeholder",
                "audio_path": str(placeholder),
                "note": "Add ELEVENLABS_API_KEY to generate real audio",
            }
        )