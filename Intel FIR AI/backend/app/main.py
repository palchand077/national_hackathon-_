import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import engine, Base
from app.config import UPLOAD_DIR
from app.routes import auth, complaints, firs, evidence, ai_model, stats

# Create tables in Database (MySQL or SQLite fallback)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SMART FIR 360",
    description="Digital, BNSS Section 173-aligned Complaint & FIR Management Platform with AI, NLP, and GIS integration",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(complaints.router)
app.include_router(firs.router)
app.include_router(evidence.router)
app.include_router(ai_model.router)
app.include_router(stats.router)

# Mount uploads directory
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Frontend directory
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
    if (FRONTEND_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "system": "SMART FIR 360",
        "bnss_version": "Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)",
        "database": str(engine.url).split("@")[-1] if "@" in str(engine.url) else "SQLite"
    }
