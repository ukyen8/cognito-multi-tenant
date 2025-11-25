"""FastAPI app entrypoint for the multi-tenant data processing platform."""

import os

from fastapi import FastAPI
from api_methods.tenants import router as tenant_router
from api_methods.notes import router as notes_router


root_path = ""
if os.environ.get("ENVIRONMENT", "local") != "local":
    root_path = "/live/"

app = FastAPI(root_path=root_path)
app.include_router(tenant_router, prefix="/api/v1", tags=["tenants"])
app.include_router(notes_router, prefix="/api/v1", tags=["notes"])
