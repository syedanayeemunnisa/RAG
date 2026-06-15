from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router as api_router
from fastapi.staticfiles import StaticFiles

import os
from .pdf_ingest import load_pdf
from .embeddings import embed_texts
from .routes import vector_store

app = FastAPI(title="PDF RAG API", docs_url="/docs")

@app.on_event("startup")
async def startup_event():
    cache_path = "vector_store_cache.npz"
    print("Checking for cached vector store...")
    if vector_store.load_from_disk(cache_path):
        print(f"Loaded {len(vector_store.texts)} chunks from cache: {cache_path}")
        return

    pdf_path = os.getenv("DEFAULT_PDF_PATH")
    if not pdf_path:
        print("DEFAULT_PDF_PATH is not set. Skipping auto-load.")
        return

    print(f"Checking for default PDF at: {pdf_path}")
    if os.path.exists(pdf_path):
        try:
            print("Loading and indexing hardcoded PDF (this may take a few seconds)...")
            chunks = load_pdf(pdf_path)
            if chunks:
                # Limit to first 400 chunks to stay within Cohere trial rate limits (100k tokens/min)
                chunks_to_index = chunks[:400]
                print(f"Indexing first {len(chunks_to_index)} of {len(chunks)} total chunks...")
                embeddings = embed_texts(chunks_to_index)
                vector_store.add(embeddings, chunks_to_index)
                vector_store.save_to_disk(cache_path)
                print(f"Successfully loaded, indexed, and cached {len(chunks_to_index)} chunks from {pdf_path}")
            else:
                print("PDF was empty or text extraction failed.")
        except Exception as e:
            print(f"Error loading default PDF on startup: {e}")
    else:
        print(f"Default PDF not found at {pdf_path}. Skipping auto-load.")



# Allow local frontend to access API
app.include_router(api_router, prefix="/api")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# Root endpoint for health check
@app.get("/")
async def health_check():
    return {"status": "ok"}
