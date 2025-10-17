# app.py
import os
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from api.routes.query import router as query_router
from api.routes.health import router as health_router
from api.websocket import router as ws_router
import structlog

log = structlog.get_logger(__name__)
app = FastAPI(title="Salesforce AI Agent (MCP Lazy Retrieval)")

# Routers
app.include_router(query_router, prefix="")
app.include_router(health_router, prefix="")
app.include_router(ws_router, prefix="")

# Metrics
Instrumentator().instrument(app).expose(app)


@app.on_event("startup")
async def startup():
    log.info("startup", component="app")


@app.on_event("shutdown")
async def shutdown():
    log.info("shutdown", component="app")
