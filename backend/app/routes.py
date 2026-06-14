from fastapi import APIRouter, UploadFile, File, Body
from pathlib import Path
from .rag import process_pdf_upload, retrieve, generate_answer

router = APIRouter()

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    content = await file.read()
    pdf_path = Path("temp") / file.filename
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(content)
    chunk_count = process_pdf_upload(pdf_path, file.filename)
    return {"status": "ok", "chunks": chunk_count}

@router.post("/chat")
async def chat(question: str = Body(...)):
    context = retrieve(question)
    answer = generate_answer(question, context)
    return {"answer": answer, "sources": context}
