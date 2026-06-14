from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Local imports
from .pdf_ingest import load_pdf
from .embeddings import embed_texts
from .vector_store import InMemoryVectorStore

# Load env vars (API keys)
load_dotenv()

# Initialize in‑memory store (singleton for the app lifecycle)
vector_store = InMemoryVectorStore()

router = APIRouter()

@router.get("/status")
async def get_status():
    """Return whether a PDF is already indexed and the chunk count."""
    return JSONResponse(content={
        "indexed": len(vector_store.texts) > 0,
        "chunks": len(vector_store.texts)
    })


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload a PDF, split it, embed, and store in memory.
    Returns the number of chunks stored.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Save to a temporary location
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)
    file_path = temp_dir / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Load and split PDF
    chunks = load_pdf(str(file_path))
    if not chunks:
        raise HTTPException(status_code=500, detail="Failed to extract any text from PDF")

    # Generate embeddings
    embeddings = embed_texts(chunks, input_type="search_document")
    # Store in memory
    vector_store.add(embeddings, chunks)
    # Save cache to disk so it persists across restarts
    vector_store.save_to_disk("vector_store_cache.npz")

    # Cleanup uploaded file
    try:
        file_path.unlink()
    except Exception:
        pass

    return JSONResponse(content={"status": "ok", "chunks": len(chunks)})

@router.post("/query")
async def query_rag(question: dict):
    """Receive a JSON body like {"question": "..."} and return an answer.
    Performs a simple similarity search on the stored vectors, then calls Groq.
    """
    import logging
    logger = logging.getLogger("uvicorn.error")
    
    query = question.get("question")
    if not query:
        raise HTTPException(status_code=400, detail="Missing 'question' field")

    try:
        logger.info(f"Received query: {query}")
        # Embed the query
        query_vec = embed_texts([query], input_type="search_query")[0]
        # Retrieve top chunks
        top_chunks = vector_store.search(query_vec, top_k=5)
        context = "\n\n".join([text for text, _score in top_chunks])

        # Build prompt for Groq LLM
        prompt = f"You are an assistant that answers questions based on the given context.\n\nContext:\n{context}\n\nQuestion: {query}\nAnswer:"

        # Call Groq API
        from groq import Groq
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY not set in environment")
        client = Groq(api_key=groq_api_key)
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=512,
        )
        answer = response.choices[0].message.content
        
        # Return answer along with source chunks and similarity scores
        return JSONResponse(content={
            "answer": answer,
            "sources": [{"text": text, "score": score} for text, score in top_chunks]
        })
    except Exception as e:
        logger.exception("Error during query_rag execution:")
        raise HTTPException(status_code=500, detail=str(e))
