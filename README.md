# AI News Storyteller

[![Python Checks](https://github.com/NielsDenoo/Fake_News_generator/actions/workflows/checks.yml/badge.svg)](https://github.com/NielsDenoo/Fake_News_generator/actions/workflows/checks.yml)
[![Docker Build](https://github.com/NielsDenoo/Fake_News_generator/actions/workflows/docker-build.yml/badge.svg)](https://github.com/NielsDenoo/Fake_News_generator/actions/workflows/docker-build.yml)

Interactive AI news storytelling app using LangChain, Ollama, Stable Diffusion, NewsAPI, and Gradio.

It is a project made for the subject AI Edge.

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

### Option 1: Run Locally (without Docker)

```bash
python -m app
```

This starts a Gradio UI at `http://localhost:7860`.

### Option 2: Run with Docker (Recommended)

Docker provides a consistent environment and handles all dependencies automatically.

**Prerequisites:**
- Docker installed
- Ollama running on your host machine (`ollama serve`)
- `.env` file with your `NEWS_API_KEY`

**Quick Start:**

1. Build the Docker image:

```bash
docker build -t fake_news_generator:test .
```

2. Run the container with host networking (so it can reach Ollama on localhost):

```bash
docker run -d --name fake_news_test --network host --env-file .env fake_news_generator:test
```

3. Access the UI at `http://localhost:7860`

4. Watch progress logs (optional):

```bash
docker logs -f fake_news_test
```

5. Stop the container:

```bash
docker stop fake_news_test
docker rm fake_news_test
```

**Notes:**
- First run downloads SDXL-Turbo model (~7GB) - this takes time
- Image generation runs on CPU by default (stable but slower, ~30-90s per image)
- To use GPU: add `-e FORCE_CPU_IMAGE=false` to the docker run command (requires NVIDIA GPU + Docker GPU support)
- The container uses `--network host` so it can reach Ollama on your host's localhost:11434

**Alternative: Run without host networking**

If you can't use `--network host`, run Ollama on a different port and point to it:

```bash
docker run -d --name fake_news_test \
  --env-file .env \
  -e OLLAMA_BASE_URL="http://host.docker.internal:11434" \
  --add-host=host.docker.internal:host-gateway \
  -p 7860:7860 \
  fake_news_generator:test
```

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
- If using Docker with `--network host`, Ollama must be running on the host at localhost:11434
- If using Docker without host networking, set `OLLAMA_BASE_URL` to point to your host

### Image Generation Hangs or Fails

- By default, image generation uses CPU mode (slower but stable)
- If it hangs: check `docker logs -f fake_news_test` for errors
- First run downloads SDXL-Turbo (~7GB) which takes time
- To enable GPU mode: add `-e FORCE_CPU_IMAGE=false` when running the container (requires NVIDIA GPU + nvidia-docker)

### Missing API Keys

Ensure `NEWS_API_KEY` is set in your `.env` file.

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

- **Python Checks** (`checks.yml`): Runs on every push and PR
  - Code formatting with `black`
  - Type checking with `mypy`
  - Linting with `flake8`
  - Unit tests with `pytest`

- **Docker Build** (`docker-build.yml`): Builds and tests Docker image
  - Builds Docker image on every push and PR
  - Runs smoke tests to verify the image works
  - Pushes to GitHub Container Registry on main branch and tags
  - Available at: `ghcr.io/nielsdenoo/fake-news-generator:latest`

### Using Pre-built Docker Images

Pull and run the latest image from GitHub Container Registry:

```bash
docker pull ghcr.io/nielsdenoo/fake-news-generator:latest
docker run -d --name fake_news_test --network host --env-file .env ghcr.io/nielsdenoo/fake-news-generator:latest
```

## Notes

- **100% local and free**: Text generation uses Ollama (llama3:8b), image generation uses Stable Diffusion SDXL-Turbo
- The app stores session state in memory for the current process
- Image generation creates a single 1024x1024 square image per story
- First run downloads SDXL-Turbo model automatically (~7GB)
