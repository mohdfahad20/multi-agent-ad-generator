"""
config/settings.py
Centralized configuration — reads from .env, validates, and exposes typed settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")


class Settings:
    # ── LLM ──────────────────────────────────────────────────────────────────
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = os.getenv(
        "OPENROUTER_MODEL", "openai/gpt-oss-120b:free"
    )

    # ── Apify ─────────────────────────────────────────────────────────────────
    APIFY_API_TOKEN: str = os.getenv("APIFY_API_TOKEN", "")

    # ── Google Drive ──────────────────────────────────────────────────────────
    GDRIVE_FILE_ID: str = os.getenv("GDRIVE_FILE_ID", "")
    GDRIVE_CREDENTIALS_PATH: str = os.getenv(
        "GDRIVE_CREDENTIALS_PATH",
        str(Path(__file__).parent.parent / "config" / "gdrive_credentials.json"),
    )
    GDRIVE_TOKEN_PATH: str = os.getenv(
        "GDRIVE_TOKEN_PATH",
        str(Path(__file__).parent.parent / "config" / "gdrive_token.json"),
    )

    # ── ElevenLabs ────────────────────────────────────────────────────────────
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    # ── Hugging Face (image gen) ──────────────────────────────────────────────
    HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")

    # ── App ───────────────────────────────────────────────────────────────────
    CWT_NICHE: str = os.getenv(
        "CWT_NICHE", "trading signals, stock market, financial freedom"
    )
    CWT_WEBSITE: str = os.getenv("CWT_WEBSITE", "crowdwisdomtrading.com")
    AD_DURATION_SECONDS: int = int(os.getenv("AD_DURATION_SECONDS", "60"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ── Paths ─────────────────────────────────────────────────────────────────
    BASE_DIR: Path = Path(__file__).parent.parent
    OUTPUT_DIR: Path = BASE_DIR / "output"
    JSON_DIR: Path = OUTPUT_DIR / "json"
    SCRIPTS_DIR: Path = OUTPUT_DIR / "scripts"
    AUDIO_DIR: Path = OUTPUT_DIR / "audio"
    IMAGES_DIR: Path = OUTPUT_DIR / "images"
    VIDEOS_DIR: Path = OUTPUT_DIR / "videos"
    LOGS_DIR: Path = BASE_DIR / "logs"

    def validate(self) -> list[str]:
        """Return list of missing required env vars."""
        missing = []
        required = {
            "OPENROUTER_API_KEY": self.OPENROUTER_API_KEY,
            "APIFY_API_TOKEN": self.APIFY_API_TOKEN,
        }
        for name, val in required.items():
            if not val or val.startswith("sk-or-v1-xxx") or val.startswith("apify_api_xxx"):
                missing.append(name)
        return missing


settings = Settings()