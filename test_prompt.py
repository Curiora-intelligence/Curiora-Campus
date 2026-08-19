import sys
from transformers import AutoTokenizer, AutoProcessor
from app.services.curio import CURIO_SYSTEM_PROMPT

tokenizer = AutoTokenizer.from_pretrained("mlx-community/gpt-oss-20b-MXFP4-Q8")
history = [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello!"},
    {"role": "user", "content": "What does this code do?"},
    {"role": "assistant", "content": "It does X."},
    {"role": "user", "content": "Explain the code deeply."}
]
messages = [{"role": "system", "content": CURIO_SYSTEM_PROMPT}] + history

try:
    formatted_prompt = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=False,
    )
    print("FORMATTED PROMPT:")
    print("---------------------------------")
    print(formatted_prompt)
    print("---------------------------------")
except Exception as e:
    print("ERROR:", e)
