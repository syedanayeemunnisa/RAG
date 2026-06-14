from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router as rag_router
from .rag import preload_default_pdf

app = FastAPI(title="PDF‑RAG Service")

# Enable CORS for the front‑end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the hard‑coded contract PDF at startup
@app.on_event("startup")
async def startup_event():
    preload_default_pdf()

app.include_router(rag_router)
