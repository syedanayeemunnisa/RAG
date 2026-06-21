import uuid
from pathlib import Path

import cohere
import groq

from .config import COHERE_API_KEY, GROQ_API_KEY
from .weaviate_client import client as wv_client

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 5


def chunk_text(text: str):
    """Return overlapping chunks from raw text."""
    chunks = []
    i = 0
    while i < len(text):
        end = i + CHUNK_SIZE
        chunks.append(text[i:end])
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def load_pdf(file_path: Path):
    """Extract raw text from a PDF file."""
    from pypdf import PdfReader

    reader = PdfReader(str(file_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def embed_texts(texts):
    """Embed a list of text strings using Cohere."""
    co = cohere.Client(COHERE_API_KEY)
    resp = co.embed(texts=texts, model="embed-english-v3.0")
    return resp.embeddings


def upsert_chunks(chunks, embeddings, source_name: str):
    """Store chunks and embeddings in Weaviate."""
    objects = [
        {
            "class": "DocumentChunk",
            "id": str(uuid.uuid4()),
            "properties": {"text": txt, "source": source_name},
            "vector": vec,
        }
        for txt, vec in zip(chunks, embeddings)
    ]
    with wv_client.batch as batch:
        for obj in objects:
            batch.add_data_object(obj)


def retrieve(query: str):
    """Return top-k relevant chunks for a query."""
    co = cohere.Client(COHERE_API_KEY)
    emb = co.embed(texts=[query], model="embed-english-v3.0").embeddings[0]
    result = (
        wv_client.query.get("DocumentChunk", ["text"])
        .with_near_vector({"vector": emb})
        .with_limit(TOP_K)
        .do()
    )
    return [item["text"] for item in result["data"]["Get"]["DocumentChunk"]]


def generate_answer(question: str, context_chunks):
    """Call Groq LLM with context to produce an answer."""
    prompt = (
        "You are a helpful assistant. Answer the user's question using the provided context.\n"
        f"Context:\n{chr(10).join(context_chunks)}\n\nQuestion: {question}\nAnswer:"
    )
    client = groq.Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content


def process_pdf_upload(file_path: Path, source_name: str):
    """Full pipeline: load PDF, chunk, embed, and upsert."""
    text = load_pdf(file_path)
    chunks = chunk_text(text)
    embeddings = embed_texts(chunks)
    upsert_chunks(chunks, embeddings, source_name)
    return len(chunks)
