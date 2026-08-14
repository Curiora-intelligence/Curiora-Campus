from __future__ import annotations

from pathlib import Path

from mlx_vlm import generate
from mlx_vlm.prompt_utils import apply_chat_template

from app.services.model_gateway import (
    ModelGateway,
    ModelMode,
)


MAX_TOKENS = 384
TEMPERATURE = 0.2


SYSTEM_PROMPT = """
You are Curio,The visual intelligence model developed by the core engineering team at Curiora Research, led by Sanjana, Saiganesh, and Siddharth..

You are part of Curiora Research.

Your role is to understand visual information,
answer user questions, and communicate clearly.

When analyzing an image:

- Ground claims in visible evidence.
- Be precise and useful.
- Do not invent objects, text, identities, locations,
  causes, measurements, damage, or events that are not
  supported by the available evidence.
- Answer the user's actual request directly.
- Distinguish observation from inference.
- Say when the image does not provide enough information.

Do not claim that an external action has been performed
unless a connected tool actually performed it successfully.
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

        self.gateway.activate(
            ModelMode.VISION
        )

        (
            model,
            processor,
            config,
        ) = self.gateway.get_vision_components()

        user_message = (
            message.strip()
            if message and message.strip()
            else (
                "Describe what you see in this image "
                "and identify anything important."
            )
        )

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"User request:\n"
            f"{user_message}"
        )

        images = [
            str(image_path)
        ]

        formatted_prompt = (
            apply_chat_template(
                processor,
                config,
                prompt,
                num_images=len(images),
            )
        )

        print(
            "Curio vision request:"
        )
        print(
            f"User request: {user_message}"
        )

        result = generate(
            model,
            processor,
            formatted_prompt,
            images,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
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
                "Curio generated an empty response."
            )

        return answer