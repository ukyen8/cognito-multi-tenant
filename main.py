from fastapi import FastAPI
from api_methods.tenants import router as tenant_router
from api_methods.notes import router as notes_router
from api_methods.auth import router as auth_router


app = FastAPI()
app.include_router(tenant_router, prefix="/api/v1")
app.include_router(notes_router, prefix="/api/v1", tags=["notes"])
app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
