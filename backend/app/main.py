from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config.logging_config import setup_logging
from app.config.settings import settings
from app.routers import auth, user, assess, report, system, admin

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version="2.0.0",
    description="App Reader — AI Readiness Assessment Platform with 9-Layer Analysis",
)

origins = ["*"] if settings.CORS_ALLOW_ALL else settings.CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,   prefix="/api/auth",   tags=["Auth"])
app.include_router(user.router,   prefix="/api/user",   tags=["User"])
app.include_router(assess.router, prefix="/api/assess", tags=["Assessment"])
app.include_router(report.router, prefix="/api/report", tags=["Report"])
app.include_router(system.router, prefix="/api/system", tags=["System"])
app.include_router(admin.router,  prefix="/api",         tags=["Admin"])

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
