FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY rk-core/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# App
COPY rk-core /app/rk-core

WORKDIR /app/rk-core

EXPOSE 5000

# Pre-build embeddings at image build time (cached in the image)
# Comment out the next line and run manually if you don't have HF_API_KEY at build time
# RUN python scripts/build_embeddings.py || true

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
