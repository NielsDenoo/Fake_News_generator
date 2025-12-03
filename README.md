# AI News Storyteller

Interactive AI news storytelling app using LangChain, Ollama, Stable Diffusion, NewsAPI, and Gradio.

## Requirements

- Python 3.10+
- A virtual environment (there is already a `.venv` in the workspace)
- **Ollama installed locally** (download at https://ollama.com/download)
- **llama3:8b model pulled in Ollama** (`ollama pull llama3:8b`)
- **CUDA-compatible GPU** (recommended for Stable Diffusion; CPU fallback supported)
- **NewsAPI key** (free tier available at https://newsapi.org/register)

## Setup

1. Install and start Ollama:

```bash
# Download from https://ollama.com/download
# Then pull the model:
ollama pull llama3:8b

# Start Ollama server (if not running):
ollama serve
```

2. Copy `.env.example` to `.env` and add your NewsAPI key:

```bash
cp .env.example .env
# edit .env and add:
# NEWS_API_KEY=...
```

3. Install dependencies (inside your `.venv`):

```bash
pip install -r requirements.txt
```

**Note**: First run will download SDXL-Turbo model (~7GB). This happens automatically.

## Run

```bash
python -m app
```

This starts a Gradio UI at `http://localhost:7860`.

## Usage

- Click `Load Latest News` to fetch top headlines.
- Choose one of the three rewritten title buttons.
- Click `Generate Continuations` to create 3 continuation ideas.
- Choose a continuation, then click `Generate Final Story & Image`.

## Troubleshooting

### Ollama Connection Error

If you see connection errors to Ollama:
- Ensure Ollama is running: `ollama serve`
- Verify the model is pulled: `ollama list` (should show llama3:8b)

### CUDA Out of Memory

If image generation fails with CUDA OOM:
- Close other GPU applications
- The app will automatically fall back to CPU (slower but works)

### Missing API Keys

Ensure `NEWS_API_KEY` is set in your `.env` file.

## Notes

- **100% local and free**: Text generation uses Ollama (llama3:8b), image generation uses Stable Diffusion SDXL-Turbo
- The app stores session state in memory for the current process
- Image generation creates a single 1024x1024 square image per story
- First run downloads SDXL-Turbo model automatically (~7GB)
