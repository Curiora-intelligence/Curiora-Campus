from __future__ import annotations

import gc
from pathlib import Path

from mlx_vlm import generate, load
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config

from app.runtimes.base import RuntimeAdapter


class MLXRuntime(RuntimeAdapter):

    def __init__(self) -> None:
        self._model = None
        self._processor = None
        self._config = None
        self._model_id: str | None = None

    @property
    def name(self) -> str:
        return "MLX"

    @property
    def device(self) -> str:
        return "Apple Silicon GPU"

    def _ensure_model(
        self,
        model_id: str,
    ) -> None:

        if (
            self._model is not None
            and self._processor is not None
            and self._config is not None
            and self._model_id == model_id
        ):
            return

        self.release()

        print(
            f"Loading Curio VLM through MLX: {model_id}"
        )

        (
            self._model,
            self._processor,
        ) = load(model_id)

        self._config = load_config(model_id)
        self._model_id = model_id

        print("Curio VLM loaded through MLX.")

    def generate_vision(
        self,
        *,
        model_id: str,
        image_path: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:

        image = Path(image_path)

        if not image.is_file():
            raise FileNotFoundError(
                f"Image file not found: {image}"
            )

        self._ensure_model(model_id)

        formatted_prompt = apply_chat_template(
            self._processor,
            self._config,
            prompt,
            num_images=1,
        )

        result = generate(
            self._model,
            self._processor,
            formatted_prompt,
            [str(image)],
            max_tokens=max_tokens,
            temperature=temperature,
            verbose=False,
        )

        answer = getattr(
            result,
            "text",
            None,
        )

        if answer is None:
            answer = str(result)

        answer = answer.strip()

        if not answer:
            raise RuntimeError(
                "MLX VLM generated an empty response."
            )

        return answer

    def release(self) -> None:

        self._model = None
        self._processor = None
        self._config = None
        self._model_id = None

        gc.collect()

        try:
            import mlx.core as mx

            mx.metal.clear_cache()

        except Exception:
            pass

        gc.collect()