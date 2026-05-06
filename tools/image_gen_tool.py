"""
tools/image_gen_tool.py
Generates ad scene images using HuggingFace InferenceClient.

FIX: Force provider="hf-inference" on InferenceClient.
This explicitly routes to HF's own free serverless GPUs instead of fal-ai/replicate.
The 402 errors were caused by InferenceClient auto-selecting fal-ai (paid).
Setting provider="hf-inference" locks it to HF's own backend — free with your token.

FIX 2: field_validator on ImageGenToolInput.prompts coerces list → JSON string
before Pydantic type-checks it. This eliminates the attempt #1 validation error
where CrewAI's agent passes a Python list instead of a JSON string.

MODEL: black-forest-labs/FLUX.1-schnell
- Supported by hf-inference provider
- Fast (4 steps), high quality
"""

import io
import json
from pathlib import Path
from typing import Any, Type

from huggingface_hub import InferenceClient
from PIL import Image
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, field_validator
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings
from utils.logger import get_logger

logger = get_logger("image_gen_tool")

# Force HF's own free serverless backend — never fal-ai or replicate
HF_PROVIDER = "hf-inference"
DEFAULT_MODEL = "black-forest-labs/FLUX.1-schnell"


class ImageGenToolInput(BaseModel):
    prompts: str = Field(
        description=(
            "JSON array of image prompts, one per scene. "
            'Example: ["energetic trader watching charts, cinematic", '
            '"phone showing trading app with green profits"]'
        )
    )

    @field_validator("prompts", mode="before")
    @classmethod
    def coerce_to_string(cls, v: Any) -> str:
        """
        Accept prompts as either a JSON string or a Python list.
        CrewAI's agent sometimes passes a raw list — this converts it
        to a JSON string before Pydantic validates the type, eliminating
        the attempt #1 validation error entirely.
        """
        if isinstance(v, list):
            logger.debug(f"prompts received as list ({len(v)} items) — converting to JSON string")
            return json.dumps(v)
        if isinstance(v, str):
            return v
        # any other type — best-effort serialise
        return json.dumps(v) if v is not None else "[]"


class ImageGenTool(BaseTool):
    """
    Generates scene images using HF InferenceClient with provider="hf-inference".
    Falls back to solid-color placeholder PNGs if API fails — never .txt files.
    """

    name: str = "AdImageGenerator"
    description: str = (
        "Generates high-quality ad scene images from text prompts "
        "using Hugging Face free image generation. Input: JSON array of prompts. "
        "Returns paths to generated PNG images."
    )
    args_schema: Type[BaseModel] = ImageGenToolInput

    def _run(self, prompts: str) -> str:
        try:
            prompt_list = json.loads(prompts)
            if not isinstance(prompt_list, list):
                prompt_list = [str(prompt_list)]
        except (json.JSONDecodeError, ValueError):
            prompt_list = [prompts]

        logger.info(f"Generating {len(prompt_list)} images | provider={HF_PROVIDER} | model={DEFAULT_MODEL}")
        image_paths = []

        for i, prompt in enumerate(prompt_list):
            enhanced = self._enhance_prompt(prompt)
            logger.info(f"Image {i+1}/{len(prompt_list)}: {enhanced[:80]}...")
            try:
                path = self._generate_image(enhanced, i)
                image_paths.append(str(path))
            except Exception as e:
                logger.error(f"Image {i+1} failed after retries: {e}")
                placeholder = self._create_color_placeholder(i, prompt)
                image_paths.append(str(placeholder))

        return json.dumps({
            "status": "success",
            "image_count": len(image_paths),
            "image_paths": image_paths,
        })

    def _enhance_prompt(self, prompt: str) -> str:
        return (
            f"{prompt}, professional advertisement photography, "
            "4k, sharp focus, vibrant colors, commercial quality, cinematic lighting"
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=5, max=30))
    def _generate_image(self, prompt: str, index: int) -> Path:
        if not settings.HF_API_TOKEN:
            logger.warning("No HF_API_TOKEN — creating color placeholder")
            return self._create_color_placeholder(index, prompt)

        # provider="hf-inference" forces HF's own free serverless backend
        # Without this, InferenceClient auto-picks fal-ai/replicate (paid)
        client = InferenceClient(
            token=settings.HF_API_TOKEN,
            provider=HF_PROVIDER,
        )

        logger.info(f"Calling InferenceClient | provider={HF_PROVIDER} | model={DEFAULT_MODEL}")
        image: Image.Image = client.text_to_image(
            prompt,
            model=DEFAULT_MODEL,
        )

        output_path = settings.IMAGES_DIR / f"scene_{index + 1:02d}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(output_path))
        logger.info(f"Saved image → {output_path}")
        return output_path

    def _create_color_placeholder(self, index: int, prompt: str) -> Path:
        """
        Creates a real solid-color PNG as placeholder.
        Valid image file — Remotion renders it without crashing.
        """
        colors = [
            (15, 23, 42),
            (30, 41, 59),
            (20, 30, 48),
            (23, 37, 84),
            (10, 20, 40),
        ]
        color = colors[index % len(colors)]
        img = Image.new("RGB", (1024, 576), color=color)

        output_path = settings.IMAGES_DIR / f"scene_{index + 1:02d}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(output_path))
        logger.info(f"Color placeholder → {output_path} | prompt: {prompt[:60]}")
        return output_path