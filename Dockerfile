FROM python:3.12-slim

# Install system dependencies for PDF parsing
RUN apt-get update && apt-get install -y \
    build-essential \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up a new user named "user" with user ID 1000 (HF requirement)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"

WORKDIR /app

# Install dependencies as the non-root user
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy the rest of your app code
COPY --chown=user . .

# Hugging Face expects port 7860
EXPOSE 7860

# Production command using Gunicorn
# Points to 'app/main.py' -> 'app' object
sh -c "gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT"