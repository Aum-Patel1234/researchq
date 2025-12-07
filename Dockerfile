# Use official Python 3.12 slim image
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=$PATH:/.local/bin

WORKDIR /app

# Install system deps used in your CI (faiss deps + curl/git)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libopenblas-dev libomp-dev curl git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install uv into /.local (same script used in CI)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Ensure uv is available
RUN /.local/bin/uv --version

# Use uv to create a reproducible venv and install deps
# - create venv (uv venv creates .venv by default)
# - upgrade installer and install project deps and dev-tools
RUN /.local/bin/uv venv && \
    /.local/bin/uv pip install --upgrade pip setuptools wheel && \
    /.local/bin/uv pip install -r requirements.txt || true && \
    /.local/bin/uv pip install ruff pytest || true

# Expose Streamlit port
EXPOSE 8501

# Default command: run Streamlit headless with uv wrapper
CMD ["/.local/bin/uv", "run", "streamlit", "run", "streamlit_app.py", "--server.headless", "true", "--server.port", "8501"]
