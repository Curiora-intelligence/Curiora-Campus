from __future__ import annotations

from threading import Lock

from app.core.runtime import (RuntimeInfo,RuntimeKind,detect_runtime)
from app.runtimes.base import RuntimeAdapter
from app.runtimes.mlx_runtime import MLXRuntime
from app.runtimes.torch_runtime import TorchRuntime


class ModelMode(str):
    TEXT = "text"
    VISION = "vision"


class ModelGateway:
    """
    Curio model gateway.

    Responsibilities:

    1. Detect the best available execution runtime.
    2. Keep runtime-specific implementation details out
       of Curio's application/service layer.
    3. Route multimodal inference through the selected
       runtime adapter.
    4. Prepare the architecture for future LLM/VLM
       model switching.

    Runtime priority:

        Apple Silicon + MLX
            ↓
        NVIDIA + CUDA
            ↓
        CPU + PyTorch
    """

    VISION_MODEL_ID = ("mlx-community/Qwen3-VL-8B-Instruct-8bit")

    TORCH_VISION_MODEL_ID = ("Qwen/Qwen3-VL-8B-Instruct")

    def __init__(self) -> None:

        self._lock = Lock()

        self._runtime_info: RuntimeInfo | None = None
        self._runtime: RuntimeAdapter | None = None

    # =========================================================
    # RUNTIME
    # =========================================================

    @property
    def runtime_info(self) -> RuntimeInfo:

        if self._runtime_info is None:
            self._runtime_info = detect_runtime()

        return self._runtime_info

    @property
    def runtime(self) -> RuntimeAdapter:

        if self._runtime is None:

            info = self.runtime_info

            if info.kind == RuntimeKind.MLX:

                self._runtime = MLXRuntime()

            elif info.kind == RuntimeKind.CUDA:

                self._runtime = TorchRuntime(
                    device="cuda"
                )

            elif info.kind == RuntimeKind.CPU:

                self._runtime = TorchRuntime(
                    device="cpu"
                )

            else:
                raise RuntimeError(
                    f"Unsupported Curio runtime: "
                    f"{info.kind}"
                )

        return self._runtime

    # =========================================================
    # VISION
    # =========================================================

    def generate_vision(self,*,image_path: str,prompt: str,max_tokens: int = 384,temperature: float = 0.2) -> str:

        with self._lock:

            model_id = (self.VISION_MODEL_ID if self.runtime_info.kind == RuntimeKind.MLX else self.TORCH_VISION_MODEL_ID)

            return self.runtime.generate_vision(
                model_id=model_id,
                image_path=image_path,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )

    # =========================================================
    # LIFECYCLE
    # =========================================================

    def release(self) -> None:

        with self._lock:

            if self._runtime is not None:
                self._runtime.release()

            self._runtime = None
            self._runtime_info = None