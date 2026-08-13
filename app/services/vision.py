from __future__ import annotations
import threading
from pathlib import Path
from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config


MODEL_ID = "mlx-community/Qwen3-VL-8B-Instruct-8bit"

MAX_TOKENS = 384
TEMPERATURE = 0.2


model = None
processor = None
config = None

model_lock = threading.Lock()
inference_lock = threading.Lock()


SYSTEM_PROMPT = """
You are Curio, The visual intelligence model developed by the core engineering team at Curiora Research, led by Sanjana, Saiganesh, and Siddharth..

Your job is to help people understand the visual world.

Analyze only what is visually supported by the image.

Be precise and useful.

Do not invent objects, text, damage, locations, identities, causes,
measurements, or events that cannot reasonably be supported by the image.

When the user asks about something specific, answer that question directly.

If the image contains something potentially important, explain why it
may matter without presenting speculation as fact.

If the image does not provide enough information to answer confidently,
say so clearly.

Keep responses concise enough for an interactive assistant while still
providing useful reasoning.
""".strip()


def load_model() -> tuple:
    """
    Load Curio exactly once.

    The model is loaded lazily so importing this module does not immediately
    allocate approximately 10+ GB of unified memory.
    """

    global model
    global processor
    global config

    if (
        model is not None
        and processor is not None
        and config is not None
    ):
        return model, processor, config

    with model_lock:

        if (
            model is not None
            and processor is not None
            and config is not None
        ):
            return model, processor, config


        model, processor = load(MODEL_ID)
        config = load_config(MODEL_ID)

    return model, processor, config


def analyze_image(image_path: str | Path,message: str = "",) -> str:
    """
    Analyze one image with Qwen3-VL and return plain text.

    Parameters
    ----------
    image_path:
        Path to the temporary/local image file.

    message:
        User's question or instruction about the image.
    """

    image_path = Path(image_path)

    if not image_path.is_file():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    model, processor, config = load_model()

    user_message = message.strip()

    if not user_message:
        user_message = (
            "Describe what you see in this image and identify "
            "anything important that the user should know."
        )

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"User's request:\n"
        f"{user_message}"
    )

    # IMPORTANT:
    # mlx-vlm expects the image collection here.
    # Passing str(image_path) directly can result in the path being
    # treated as an iterable of characters.
    images = [str(image_path)]

    formatted_prompt = apply_chat_template(
        processor,
        config,
        prompt,
        num_images=len(images),
    )

    print("Curio is analyzing an image...")
    print(f"User request: {user_message}")

    # Qwen3-VL inference uses MLX GPU.
    # A lock prevents two simultaneous demo requests from competing
    # aggressively for the same 16 GB unified-memory pool.
    with inference_lock:

        result = generate(
            model,
            processor,
            formatted_prompt,
            images,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            verbose=False,
        )

    answer = getattr(result, "text", None)

    if answer is None:
        answer = str(result)

    answer = answer.strip()

    if not answer:
        raise RuntimeError("Curio generated an empty response.")

    return answer
