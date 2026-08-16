from __future__ import annotations

from abc import ABC, abstractmethod


class RuntimeAdapter(ABC):
    """
    Common interface for all Curio inference runtimes.

    Curio's application layer should never need to know whether
    inference is running through MLX, CUDA, or CPU.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def device(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_vision(
        self,
        *,
        model_id: str,
        image_path: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def release(self) -> None:
        raise NotImplementedError