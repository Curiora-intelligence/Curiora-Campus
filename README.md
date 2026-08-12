# Curiora Campus

Curiora Campus includes a campus-service portal and Curio Visual Intelligence,
adapted from the Curiora Research local MLX implementation.

## Run the web app

```bash
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`.

## Enable local visual intelligence

Curio uses `mlx-community/Qwen3-VL-8B-Instruct-8bit`, the model used by the
Curiora Research repository. It is intentionally optional so the campus app
can start without allocating model memory.

On an Apple Silicon Mac with sufficient unified memory, install the vision
runtime and restart the app:

```bash
python -m pip install -r requirements-vision.txt
uvicorn main:app --reload
```

The model downloads on the first image request. Camera and voice controls need
browser permission; camera access also requires `localhost` or HTTPS.
