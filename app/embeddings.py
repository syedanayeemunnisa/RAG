import os
from typing import List
import numpy as np
import cohere
from cohere import Client as CohereClient
from dotenv import load_dotenv

load_dotenv()


# Load API key from environment (already in .env)
_cohere_api_key = os.getenv("COHERE_API_KEY")
if not _cohere_api_key:
    raise ValueError("COHERE_API_KEY not set in environment variables")

_cohere_client = CohereClient(_cohere_api_key)

def embed_texts(texts: List[str], input_type: str = "search_document") -> np.ndarray:
    """Return a 2‑D NumPy array of embeddings for the given texts.

    Cohere's embed‑english‑v3.0 model is used.
    """
    if not texts:
        return np.empty((0, 1024), dtype=np.float32)

    import time
    # Cohere limits embed requests to 96 texts per call
    BATCH_SIZE = 96
    all_embeddings = []

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        
        retries = 5
        delay = 12  # Seconds to wait before first retry (Cohere trial limits are per-minute)
        
        while retries > 0:
            try:
                response = _cohere_client.embed(
                    model="embed-english-v3.0",
                    texts=batch,
                    input_type=input_type,
                )
                all_embeddings.extend(response.embeddings)
                break  # Successful call, break out of retry loop
            except Exception as e:
                is_rate_limit = False
                if hasattr(e, "status_code") and e.status_code == 429:
                    is_rate_limit = True
                elif "429" in str(e) or "rate limit" in str(e).lower():
                    is_rate_limit = True
                
                if is_rate_limit and retries > 1:
                    print(f"Cohere rate limit hit. Waiting {delay}s before retrying...")
                    time.sleep(delay)
                    retries -= 1
                    delay = min(delay * 2, 65)  # Exponential backoff up to ~65 seconds
                else:
                    raise e

    return np.array(all_embeddings, dtype=np.float32)


