from fastapi import FastAPI
from app.api.routes.health import router as health_router
from app.api.routes.ingest import router as ingest_router
from app.api.routes.search import router as search_router
from app.api.routes.graph import router as graph_router
from app.db.init_db import init_db
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.answer import router as answer_router
from app.api.routes import transcript
from app.api.routes.discovery import router as discovery_router
from app.api.routes import ws
from app.api.routes.sow import router as sow_router
from app.api.routes.export import router as export_router
from app.api.routes import template
from app.api.routes import debug_search

app = FastAPI(title="Enterprise OS")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
async def root():
    return {"status": "running"}

app.include_router(health_router, prefix="/api")
app.include_router(ingest_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(graph_router, prefix="/api")
app.include_router(answer_router, prefix="/api")
app.include_router(transcript.router, prefix="/api")
app.include_router(discovery_router, prefix="/api")
app.include_router(ws.router, prefix="/api")
app.include_router(sow_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(template.router, prefix="/api/template")
app.include_router(debug_search.router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # TEMPORARILY for debugging.
    # allow_origins=[
    #     "http://localhost:3000",
    #     "http://127.0.0.1:3000"
    # ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)