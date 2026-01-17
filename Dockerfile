# 1. Use a lightweight Python base
FROM python:3.12-slim

# 2. Install system dependencies for PDF parsing
RUN apt-get update && apt-get install -y \
    build-essential \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Create a non-root user and set up workspace
RUN useradd -m -u 1000 user
WORKDIR /app
RUN chown user:user /app

USER user
ENV PATH="/home/user/.local/bin:${PATH}"
# Force Transformers to look only at local files
ENV TRANSFORMERS_OFFLINE=1 
ENV HF_DATASETS_OFFLINE=1

# 4. Install Python dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# 5. PRE-DOWNLOAD MODEL: Bake the model into the image during build
# This prevents runtime download attempts and 429 errors.
RUN python3 -c "from sentence_transformers import SentenceTransformer; \
    model = SentenceTransformer('all-MiniLM-L6-v2'); \
    model.save('./model_cache/all-MiniLM-L6-v2')"

# 6. Copy application code
COPY --chown=user . .

# 7. Production startup
# Using 1 worker for resource-heavy AI models.
CMD gunicorn app.main:app \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --timeout 120