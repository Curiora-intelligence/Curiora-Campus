from __future__ import annotations

import gc
from enum import Enum
from threading import Lock

import mlx.core as mx
from mlx_vlm import load
from mlx_vlm.utils import load_config


class ModelMode(str, Enum):
    TEXT = "text"
    VISION = "vision"


class ModelGateway:
    """
    Central model lifecycle manager for Curio.

    Development target:
        M4 MacBook Air / 16 GB unified memory

    Policy:
        Keep only one heavyweight model resident at a time.
    """

    VISION_MODEL_ID = (
        "mlx-community/Qwen3-VL-8B-Instruct-8bit"
    )

    def __init__(self) -> None:
        self._lock = Lock()

        self._active_mode: ModelMode | None = None

        self._vision_model = None
        self._vision_processor = None
        self._vision_config = None

        self._text_model = None
        self._text_processor = None

    # =========================================================
    # PUBLIC API
    # =========================================================

    def activate(self, mode: ModelMode) -> None:
        """
        Make the requested model the active resident model.
        """

        with self._lock:

            if self._active_mode == mode:
                return

            print(
                f"Curio model switch: "
                f"{self._active_mode} -> {mode}"
            )

            self._release_active_model()

            if mode == ModelMode.VISION:
                self._load_vision_model()

            elif mode == ModelMode.TEXT:
                self._load_text_model()

            else:
                raise ValueError(
                    f"Unsupported model mode: {mode}"
                )

            self._active_mode = mode

    def get_active_mode(self) -> ModelMode | None:
        return self._active_mode

    def get_vision_components(self):
        """
        Return:
            model,
            processor,
            config

        Only valid after activate(VISION).
        """

        if self._active_mode != ModelMode.VISION:
            raise RuntimeError(
                "Vision model is not active."
            )

        if (
            self._vision_model is None
            or self._vision_processor is None
            or self._vision_config is None
        ):
            raise RuntimeError(
                "Vision model components are unavailable."
            )

        return (
            self._vision_model,
            self._vision_processor,
            self._vision_config,
        )

    def get_text_components(self):
        """
        Return:
            model,
            processor

        Only valid after activate(TEXT).
        """

        if self._active_mode != ModelMode.TEXT:
            raise RuntimeError(
                "Text model is not active."
            )

        if (
            self._text_model is None
            or self._text_processor is None
        ):
            raise RuntimeError(
                "Text model components are unavailable."
            )

        return (
            self._text_model,
            self._text_processor,
        )

    # =========================================================
    # MODEL LOADING
    # =========================================================

    def _load_vision_model(self) -> None:

        print(
            "Loading Curio vision model..."
        )

        print(
            f"Model: {self.VISION_MODEL_ID}"
        )

        (
            self._vision_model,
            self._vision_processor,
        ) = load(
            self.VISION_MODEL_ID
        )

        self._vision_config = load_config(
            self.VISION_MODEL_ID
        )

        print(
            "Curio vision model loaded."
        )

    def _load_text_model(self) -> None:
        """
        Placeholder for gpt-oss integration.

        We are intentionally not loading a text model yet.
        """

        raise NotImplementedError(
            "Text model integration is the next step."
        )

    # =========================================================
    # MEMORY MANAGEMENT
    # =========================================================

    def _release_active_model(self) -> None:

        if self._active_mode == ModelMode.VISION:

            print(
                "Releasing Curio vision model..."
            )

            self._vision_model = None
            self._vision_processor = None
            self._vision_config = None

        elif self._active_mode == ModelMode.TEXT:

            print(
                "Releasing Curio text model..."
            )

            self._text_model = None
            self._text_processor = None

        self._active_mode = None

        self._clear_memory()

    @staticmethod
    def _clear_memory() -> None:

        gc.collect()

        try:
            mx.eval(
                mx.array(
                    0,
                    dtype=mx.float32,
                )
            )

        except Exception:
            pass

        try:
            mx.metal.clear_cache()

        except Exception:
            pass

        gc.collect()