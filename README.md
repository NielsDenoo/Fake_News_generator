# AI News Storyteller

[![Python Checks](https://github.com/NielsDenoo/Fake_News_generator/actions/workflows/checks.yml/badge.svg)](https://github.com/NielsDenoo/Fake_News_generator/actions/workflows/checks.yml)
[![Docker Build](https://github.com/NielsDenoo/Fake_News_generator/actions/workflows/docker-build.yml/badge.svg)](https://github.com/NielsDenoo/Fake_News_generator/actions/workflows/docker-build.yml)

Interactive AI news storytelling app using LangChain, Ollama, Stable Diffusion, NewsAPI, and Dash.

It is a project made for the subject AI Edge.

## Quick Start with Docker (Recommended)

The fastest way to run the app is using Docker. All dependencies and models are included.

### Prerequisites

1. **Docker** - [Install Docker](https://docs.docker.com/get-docker/)
2. **Ollama** - [Install Ollama](https://ollama.com/download) and pull the llama3:8b model:
   ```bash
   ollama pull llama3:8b
   ollama serve
   ```
3. **NewsAPI Key** - Get a free key at [newsapi.org/register](https://newsapi.org/register)
4. **Create `.env` file** in the project root:
   ```bash
   NEWS_API_KEY=your_actual_newsapi_key_here
   ```

### Run the App

**Step 1: Build the Docker image**
```bash
docker build -t fake_news_generator .
```
*This downloads all dependencies and ML models (~7GB). Takes 5-10 minutes on first run.*

**Step 2: Start the container**
```bash
docker run -d --name fake_news_app --network host --env-file .env fake_news_generator
```

**What this does:**
- `-d` = Run in detached mode (background)
- `--name fake_news_app` = Names the container for easy management
- `--network host` = Allows container to reach Ollama on localhost:11434
- `--env-file .env` = Loads your NewsAPI key from `.env` file
- `fake_news_generator` = The image name

**Step 3: Access the app**

Open your browser to: **http://localhost:7860**

### Useful Commands

**Watch logs (see progress and errors):**
```bash
docker logs -f fake_news_app
```

**Stop the container:**
```bash
docker stop fake_news_app
```

**Remove the container:**
```bash
docker rm fake_news_app
```

**Restart with fresh state:**
```bash
docker rm -f fake_news_app
docker run -d --name fake_news_app --network host --env-file .env fake_news_generator
```

**Check if container is running:**
```bash
docker ps --filter "name=fake_news_app"
```

### Alternative: Docker without host networking

If `--network host` doesn't work on your system (e.g., macOS/Windows):

```bash
docker run -d --name fake_news_app \
  -p 7860:7860 \
  -e OLLAMA_BASE_URL="http://host.docker.internal:11434" \
  --add-host=host.docker.internal:host-gateway \
  --env-file .env \
  fake_news_generator
```

**What this does:**
- `-p 7860:7860` = Maps container port to host port
- `-e OLLAMA_BASE_URL=...` = Points to Ollama on host machine
- `--add-host=...` = Allows container to resolve `host.docker.internal`

### Using Pre-built Image from GitHub

Instead of building locally, pull the pre-built image:

```bash
docker pull ghcr.io/nielsdenoo/fake-news-generator:latest
docker run -d --name fake_news_app --network host --env-file .env ghcr.io/nielsdenoo/fake-news-generator:latest
```

## Local Development (Without Docker)

### Requirements
- Python 3.11+
- Ollama with llama3:8b model
- NewsAPI key

### Setup

1. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env and add your NEWS_API_KEY
   ```

4. **Run the app:**
   ```bash
   python app.py
   ```

5. **Access at:** http://localhost:7860

## How to Use the App

1. **Load News** - Select a category (General, Tech, Sports, etc.) and click "Load Latest News"
2. **Choose Title** - Click one of the three AI-rewritten titles
3. **Select Continuation** - Pick one of three story continuation ideas
4. **Generate Story** - The app automatically generates a fake news story and image

The entire workflow takes ~2-5 minutes depending on your hardware.

## Troubleshooting

### Container won't start

**Check if Ollama is running:**
```bash
ollama serve
# In another terminal:
curl http://localhost:11434/api/version
```

**Verify `.env` file exists with your NewsAPI key:**
```bash
cat .env
# Should show: NEWS_API_KEY=your_key_here
```

**View container logs for errors:**
```bash
docker logs fake_news_app
```

### "Connection refused" to Ollama

**Using `--network host` (Linux):**
- Ensure Ollama is running: `ollama serve`
- Verify model is pulled: `ollama list` (should show llama3:8b)

**Using port mapping (Mac/Windows):**
```bash
docker run -d --name fake_news_app \
  -p 7860:7860 \
  -e OLLAMA_BASE_URL="http://host.docker.internal:11434" \
  --add-host=host.docker.internal:host-gateway \
  --env-file .env \
  fake_news_generator
```

### NewsAPI 401 Unauthorized

- Check your API key is valid at [newsapi.org](https://newsapi.org)
- Ensure `.env` has `NEWS_API_KEY=...` with no quotes or extra spaces
- Restart container after fixing `.env`

### Image generation is slow or hangs

**Normal behavior:**
- First run downloads SDXL-Turbo model (~7GB) - takes 5-10 minutes
- Each image takes 30-90 seconds on CPU
- Watch progress: `docker logs -f fake_news_app`

**Enable GPU (if you have NVIDIA GPU):**
```bash
docker run -d --name fake_news_app \
  --gpus all \
  --network host \
  -e FORCE_CPU_IMAGE=false \
  --env-file .env \
  fake_news_generator
```

### UI not loading at localhost:7860

**Check if container is running:**
```bash
docker ps --filter "name=fake_news_app"
```

**Test connection:**
```bash
curl http://localhost:7860/
```

**Common fixes:**
- Wait 1-2 minutes for models to load on first run
- Check logs: `docker logs fake_news_app`
- Restart container: `docker rm -f fake_news_app && docker run -d ...`

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
