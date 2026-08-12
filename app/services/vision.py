"""Optional local Curio visual-intelligence model adapter.

This is adapted from Curiora Research.  Importing this module deliberately does
not import or load MLX, so the Campus web app remains usable before the vision
runtime and the large model have been installed.
"""

from __future__ import annotations

import importlib.util
import os
import threading
from pathlib import Path
from typing import Any


MODEL_ID = os.getenv("CURIO_MODEL_ID", "mlx-community/Qwen3-VL-8B-Instruct-8bit")
MAX_TOKENS = 384
TEMPERATURE = 0.2

_model: Any | None = None
_processor: Any | None = None
_config: Any | None = None
_model_lock = threading.Lock()
_inference_lock = threading.Lock()


SYSTEM_PROMPT = """
You are Curio, the visual intelligence model developed by Curiora.

Help people understand the visual world. Analyze only what is visually
supported by the image. Be precise and useful. Do not invent objects, text,
damage, locations, identities, causes, measurements, or events that cannot be
reasonably supported by the image. If there is not enough visual information,
say so clearly. Keep responses concise enough for an interactive assistant.
""".strip()


class VisionBackendUnavailable(RuntimeError):
    """Raised when the optional local MLX vision runtime is not available."""


def vision_status() -> dict[str, str | bool]:
    """Return availability without downloading or allocating the model."""

    if importlib.util.find_spec("mlx_vlm") is None:
        return {
            "available": False,
            "model": MODEL_ID,
            "detail": "The local Curio model is not installed yet.",
        }
    return {
        "available": True,
        "model": MODEL_ID,
        "detail": "Curio will load the local vision model when you send the first image.",
    }


def _load_model() -> tuple[Any, Any, Any]:
    """Load the MLX model once, only when a real analysis request arrives."""

    global _model, _processor, _config

    if _model is not None and _processor is not None and _config is not None:
        return _model, _processor, _config

    with _model_lock:
        if _model is not None and _processor is not None and _config is not None:
            return _model, _processor, _config

        try:
            from mlx_vlm import generate, load  # type: ignore[import-not-found]
            from mlx_vlm.prompt_utils import apply_chat_template  # type: ignore[import-not-found]
            from mlx_vlm.utils import load_config  # type: ignore[import-not-found]
        except ImportError as error:
            raise VisionBackendUnavailable(
                "Curio's local vision runtime is not installed. "
                "Install requirements-vision.txt on an Apple Silicon Mac, then restart the app."
            ) from error

        # Keep helpers attached to the function so the import stays lazy.
        _load_model.generate = generate  # type: ignore[attr-defined]
        _load_model.apply_chat_template = apply_chat_template  # type: ignore[attr-defined]

        try:
            _model, _processor = load(MODEL_ID)
            _config = load_config(MODEL_ID)
        except Exception as error:  # Model download/runtime errors should be user-readable.
            raise VisionBackendUnavailable(
                "Curio could not load its local vision model. "
                "Confirm the model dependencies, internet access for the first download, and available memory."
            ) from error

    return _model, _processor, _config


def analyze_image(image_path: str | Path, message: str = "") -> str:
    """Analyze one image with the Curiora Research Qwen3-VL model."""

    image_path = Path(image_path)
    if not image_path.is_file():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    model, processor, config = _load_model()
    generate = _load_model.generate  # type: ignore[attr-defined]
    apply_chat_template = _load_model.apply_chat_template  # type: ignore[attr-defined]

    user_message = message.strip() or (
        "Describe what you see in this image and identify anything important "
        "that the user should know."
    )
    prompt = f"{SYSTEM_PROMPT}\n\nUser's request:\n{user_message}"
    images = [str(image_path)]

    formatted_prompt = apply_chat_template(
        processor,
        config,
        prompt,
        num_images=len(images),
    )

    # Qwen inference uses the shared MLX GPU; serializing requests prevents
    # concurrent users from exhausting unified memory on a local deployment.
    with _inference_lock:
        result = generate(
            model,
            processor,
            formatted_prompt,
            images,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            verbose=False,
        )

    answer = str(getattr(result, "text", result)).strip()
    if not answer:
        raise RuntimeError("Curio generated an empty response.")
    return answer
