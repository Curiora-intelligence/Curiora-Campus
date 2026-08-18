from __future__ import annotations

import gc
from pathlib import Path
from mlx_lm.sample_utils import make_sampler
from mlx_lm import generate as llm_generate
from mlx_lm import load as load_llm

from mlx_vlm import generate as vlm_generate
from mlx_vlm import load as load_vlm
from mlx_vlm.prompt_utils import apply_chat_template as apply_vlm_chat_template
from mlx_vlm.utils import load_config as load_vlm_config

from app.runtimes.base import RuntimeAdapter


class MLXRuntime(RuntimeAdapter):

    def __init__(self) -> None:
        self._model = None
        self._processor = None
        self._tokenizer = None
        self._config = None

        self._model_id: str | None = None
        self._mode: str | None = None

    @property
    def name(self) -> str:
        return "MLX"

    @property
    def device(self) -> str:
        return "Apple Silicon GPU"

    # =========================================================
    # LIFECYCLE
    # =========================================================
    def _clean_text_output(self, text: str) -> str:
        markers = (
        "<|channel|>analysis<|message|>",
        "<|channel|>final<|message|>",
        "<|start|>assistant<|channel|>final<|message|>",
        "<|end|>",
        )

        for marker in markers:
            text = text.replace(marker, "")

        return text.strip()
    
    def _clear_model(self) -> None:
        self._model = None
        self._processor = None
        self._tokenizer = None
        self._config = None
        self._model_id = None
        self._mode = None

        gc.collect()

        try:
            import mlx.core as mx

            mx.clear_cache()

        except Exception:
            try:
                import mlx.core as mx

                mx.metal.clear_cache()

            except Exception:
                pass

        gc.collect()

    def release(self) -> None:
        self._clear_model()

    # =========================================================
    # TEXT / GPT-OSS
    # =========================================================

    def _ensure_text_model(
        self,
        model_id: str,
    ) -> None:

        if (
            self._model is not None
            and self._tokenizer is not None
            and self._model_id == model_id
            and self._mode == "text"
        ):
            return

        self._clear_model()

        print(
            f"Loading Curio LLM through MLX: {model_id}"
        )

        self._model, self._tokenizer = load_llm(
            model_id
        )

        self._model_id = model_id
        self._mode = "text"

        print(
            "Curio LLM loaded through MLX."
        )

    def generate_text(
    self,
    *,
    model_id: str,
    prompt: str,
    max_tokens: int,
    temperature: float,) -> str:

        self._ensure_text_model(model_id)

        messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

        try:
            formatted_prompt = self._tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False,
        )
        except Exception:
            formatted_prompt = prompt

        sampler = make_sampler(
        temp=max(0.0, float(temperature)),
        top_p=1.0,
        top_k=0,
        )

        result = llm_generate(
        self._model,
        self._tokenizer,
        prompt=formatted_prompt,
        max_tokens=max_tokens,
        sampler=sampler,
        verbose=False,
        )

        answer = (
        result
        if isinstance(result, str)
        else str(result)
        ).strip()

        answer = self._clean_text_output(answer)

        if not answer:
            raise RuntimeError(
            "MLX LLM generated an empty response."
            )

        return answer
    # =========================================================
    # VISION / QWEN-VL
    # =========================================================

    def _ensure_vision_model(
        self,
        model_id: str,
    ) -> None:

        if (
            self._model is not None
            and self._processor is not None
            and self._config is not None
            and self._model_id == model_id
            and self._mode == "vision"
        ):
            return

        self._clear_model()

        print(
            f"Loading Curio VLM through MLX: {model_id}"
        )

        (
            self._model,
            self._processor,
        ) = load_vlm(model_id)

        self._config = load_vlm_config(
            model_id
        )

        self._model_id = model_id
        self._mode = "vision"

        print(
            "Curio VLM loaded through MLX."
        )

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

        self._ensure_vision_model(
            model_id
        )

        formatted_prompt = (
            apply_vlm_chat_template(
                self._processor,
                self._config,
                prompt,
                num_images=1,
            )
        )

        result = vlm_generate(
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
        
        for marker in (
        "<|channel|>analysis<|message|>",
        "<|channel|>final<|message|>",
        "<|end|>",
        "<|start|>assistant<|channel|>final<|message|>"):
            answer = answer.replace(marker, "")

        answer = answer.strip()

        answer = self._clean_text_output(answer)

        if not answer:
            raise RuntimeError(
                "MLX VLM generated an empty response."
            )

        return answer