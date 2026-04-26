from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.routes import intent, sim, ws
from src.sim import get_sim


@asynccontextmanager
async def lifespan(app: FastAPI):
    sim_mgr = get_sim()
    sim_mgr.start()
    try:
        yield
    finally:
        sim_mgr.stop()


app = FastAPI(title="BCI × Anima Core", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intent.router)
app.include_router(ws.router)
app.include_router(sim.router)


@app.get("/health")
async def health() -> dict:
    sim_mgr = get_sim()
    return {
        "status": "ok",
        "llm_provider": settings.LLM_PROVIDER,
        "model": settings.LLM_MODEL_FAST,
        "api_key_set": bool(settings.api_key),
        "sim_available": sim_mgr.available,
        "sim_running": sim_mgr.sim is not None,
    }
