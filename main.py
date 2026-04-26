from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import docs_router, methodology_router
from app.api import storage_router
from app.core.database import Base, engine, SessionLocal
from app.core.config import settings
from app.services.methodology_service import seed_if_empty
import os

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    seed_if_empty(db)
finally:
    db.close()

app = FastAPI(title="irvinbot-docs", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(docs_router.router, prefix="/docs", tags=["docs"])
app.include_router(methodology_router.router, prefix="/methodology", tags=["methodology"])
app.include_router(storage_router.router, prefix="/storage", tags=["storage"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "docs"}
