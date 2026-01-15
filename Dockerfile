FROM python:3.12-slim

# 1. Install system dependencies for PDF parsing
RUN apt-get update && apt-get install -y \
    build-essential \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Set up a non-root user (Standard security)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"

WORKDIR /app

# 3. Install Python dependencies
COPY --chown=user requirements.txt .
# Ensure you have 'gunicorn' and 'uvicorn[standard]' in your requirements.txt
RUN pip install --no-cache-dir --user -r requirements.txt

# 4. Copy the rest of your app code
COPY --chown=user . .

# 5. Production command using Gunicorn
# Using the "Shell Form" (no brackets) so $PORT is replaced by a real number
CMD gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT