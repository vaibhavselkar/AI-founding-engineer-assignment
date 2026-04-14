from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.api.aeo import router as aeo_router
from app.api.fanout import router as fanout_router

# ─── App Setup ─────────────────────────────────────────────

app = FastAPI(
    title="AEGIS — Answer Engine & Generative Intelligence Suite",
    description=(
        "Content intelligence platform that scores, diagnoses, "
        "and improves content for AEO and GEO optimization."
    ),
    version="1.0.0",
)

# ─── Routers ───────────────────────────────────────────────

app.include_router(
    aeo_router,
    prefix="/api/aeo",
    tags=["AEO Content Scorer"]
)

app.include_router(
    fanout_router,
    prefix="/api/fanout",
    tags=["Query Fan-Out Engine"]
)

# ─── Static Files ──────────────────────────────────────────

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ─── Frontend ──────────────────────────────────────────────

@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))