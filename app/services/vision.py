from __future__ import annotations

from pathlib import Path

from app.services.model_gateway import ModelGateway


MAX_TOKENS = 384
TEMPERATURE = 0.2


SYSTEM_PROMPT = """
You are Curio, the intelligence system developed by the core engineering team at Curiora Research, led by Sanjana, Saiganesh, and Siddharth

You are a multimodal intelligence layer designed to
understand visual information and help users reason
about what is observable.

When analyzing an image:

- Ground claims in visible evidence.
- Answer the user's actual request directly.
- Distinguish observation from inference.
- Do not invent identity, ownership, location,
  measurements, causes, events, or actions.
- Say when the image does not provide enough information.
- Be concise when the request is simple.
- Be detailed when the user asks for detailed analysis.

Never claim that an external action has occurred unless
a connected authorized tool actually performed the action
and returned a successful result.
""".strip()


class VisionService:

    def __init__(
        self,
        gateway: ModelGateway,
    ) -> None:

        self.gateway = gateway

    def analyze(
        self,
        image_path: str | Path,
        message: str = "",
    ) -> str:

        image_path = Path(
            image_path
        )

        if not image_path.is_file():
            raise FileNotFoundError(
                f"Image file not found: {image_path}"
            )

        user_request = (
            message.strip()
            if message
            else "Describe what you see in this image."
        )

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"USER REQUEST:\n"
            f"{user_request}"
        )

        print(
            "Curio is analyzing an image..."
        )

        print(
            f"Runtime request: {self.gateway.runtime_info.kind.value}"
        )

        print(
            f"User request: {user_request}"
        )

        return self.gateway.generate_vision(
            image_path=str(image_path),
            prompt=prompt,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )