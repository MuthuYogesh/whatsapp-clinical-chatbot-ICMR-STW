import os
from sentence_transformers import SentenceTransformer
import numpy as np

# Point to a local directory inside your container
MODEL_PATH = "./model_cache/all-MiniLM-L6-v2"

# Check if local model exists, otherwise it will try to download (only during build)
if os.path.exists(MODEL_PATH):
    _model = SentenceTransformer(MODEL_PATH)
else:
    # This branch should only run during your Docker build step
    _model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_texts(texts: list[str]) -> np.ndarray:
    return _model.encode(texts, convert_to_numpy=True)
