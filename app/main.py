from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import os

from app.config import settings
from app.database import engine, Base
from app.middleware.mothership import MothershipMiddleware
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.servers import router as servers_router
from app.routers.channels import router as channels_router
from app.routers.messages import router as messages_router
from app.routers.voice import router as voice_router
from app.routers.admin import router as admin_router

import app.models.models

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Waygo API",
    version="1.0.0",
    description="Waygo Communication Platform — All Rights Reserved. Contact: playfabauthenticatorsettings_ on Discord.",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)

app.add_middleware(MothershipMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        t = time.time()
        response = await call_next(request)
        response.headers["X-Process-Time"] = str(round(time.time() - t, 4))
        response.headers["X-Powered-By"] = "Waygo"
        return response


app.add_middleware(TimingMiddleware)

PREFIX = "/api/v1"
app.include_router(auth_router, prefix=PREFIX)
app.include_router(users_router, prefix=PREFIX)
app.include_router(servers_router, prefix=PREFIX)
app.include_router(channels_router, prefix=PREFIX)
app.include_router(messages_router, prefix=PREFIX)
app.include_router(voice_router, prefix=PREFIX)
app.include_router(admin_router, prefix=PREFIX)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def homepage():
    html_path = os.path.join(os.path.dirname(__file__), "home.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok", "service": "Waygo API", "version": "1.0.0"}
