from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import docs_router
from app.core.database import Base, engine
from app.core.config import settings
import os

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="irvinbot-docs", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(docs_router.router, prefix="/docs", tags=["docs"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "docs"}
