import os
import httpx
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router
from app.config import CONFIG_DIR, ADMIN_PASSWORD

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UniversalAdapter")

app = FastAPI(title="Universal AI Adapter", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    limits = httpx.Limits(max_keepalive_connections=100, max_connections=500)
    app.state.http_client = httpx.AsyncClient(timeout=60.0, limits=limits)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    logger.info(f"Universal AI Adapter Started.")
    logger.info(f"Admin password is set (length: {len(ADMIN_PASSWORD)})")

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "http_client"):
        await app.state.http_client.aclose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=3000, reload=True)
