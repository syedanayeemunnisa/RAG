from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router as api_router
from fastapi.staticfiles import StaticFiles

import os

app = FastAPI(title="PDF RAG API", docs_url="/docs")

allowed_origins = [
    "https://wvbrag.netlify.app",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

frontend_origin = os.getenv("FRONTEND_ORIGIN")
if frontend_origin:
    allowed_origins.append(frontend_origin.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Allow local frontend to access API
app.include_router(api_router, prefix="/api")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# Root endpoint for health check
@app.get("/")
async def health_check():
    return {"status": "ok"}
