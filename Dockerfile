# 1. Use a lightweight Python base
FROM python:3.12-slim

# 2. Install system dependencies for PDF parsing (PyMuPDF)
# We combine commands and clean up the cache to keep the image small
RUN apt-get update && apt-get install -y \
    build-essential \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Create a non-root user for security
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"

WORKDIR /app

# 4. Install Python dependencies
# TRICK: We install CPU-only Torch first to save ~1.5GB of space
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy your application code
COPY --chown=user . .

# 6. Production startup command
# We use 1 worker because AI models are heavy; Cloud Run will scale up if needed.
# $PORT is provided automatically by Google Cloud Run.
CMD gunicorn app.main:app \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --timeout 120