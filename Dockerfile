# 1. Use a lightweight Python base
FROM python:3.12-slim

# 2. Install system dependencies for PDF parsing
RUN apt-get update && apt-get install -y \
    build-essential \
    libmupdf-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3. Set up workspace and permissions BEFORE switching to non-root user
WORKDIR /app
RUN useradd -m -u 1000 user && chown -R user:user /app

# 4. Install Python dependencies as root to ensure global availability
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# 5. PRE-DOWNLOAD MODEL: Build phase download
# We run this as root so it can create the cache directory properly
RUN pip install --no-cache-dir torch transformers sentence-transformers && \
    python3 -c "import torch; from sentence_transformers import SentenceTransformer; \
    model = SentenceTransformer('all-MiniLM-L6-v2'); \
    model.save('./model_cache/all-MiniLM-L6-v2')" && \
    chown -R user:user /app/model_cache

# 6. Switch to non-root user for security
USER user
ENV PATH="/home/user/.local/bin:${PATH}"
# Force Transformers to look ONLY at local files at runtime
ENV TRANSFORMERS_OFFLINE=1 
ENV HF_DATASETS_OFFLINE=1

# 7. Copy application code
COPY --chown=user . .

# 8. Production startup (Fixed JSON format to prevent warnings)
# Cloud Run provides $PORT; Gunicorn will listen on it.
CMD ["gunicorn", "app.main:app", \
     "--workers", "1", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8080", \
     "--timeout", "120"]