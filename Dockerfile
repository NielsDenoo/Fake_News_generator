FROM python:3.11-slim

ARG SKIP_HEAVY=false

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ezaeaze
WORKDIR /app

# Install minimal system dependencies often required by imaging libraries
ENV DEBIAN_FRONTEND=noninteractive
# Use quiet, retry and --fix-missing options to avoid long interactive hangs
RUN apt-get update -qq \
     && apt-get install -y --no-install-recommends -o APT::Acquire::Retries=3 \
         -o Acquire::http::Timeout=10 \
         --fix-missing \
         libgl1 \
         libglib2.0-0 \
         libjpeg-dev \
         libpng-dev \
         ffmpeg \
         ca-certificates \
     && apt-get clean \
     && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Python deps first (cache layer)
COPY requirements.txt /app/requirements.txt
COPY requirements-ci.txt /app/requirements-ci.txt
RUN if [ "${SKIP_HEAVY}" = "true" ]; then \
        pip install --no-cache-dir -r /app/requirements-ci.txt; \
    else \
        pip install --no-cache-dir -r /app/requirements.txt; \
    fi

# Copy project
COPY . /app

# Do not copy local secrets by default; users should pass via env or --env-file
EXPOSE 7860

CMD ["python", "app.py"]
