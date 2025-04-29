from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import traceback
import os
import bcrypt
from starlette.middleware.base import BaseHTTPMiddleware
from .core.production_cors import ProductionCORSMiddleware

from .core.config import settings
from .api.routes import content_generation, quiz, topic, user
from .db.session import SessionLocal, Base, engine
from .db.models import User

app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    debug=True,
)

# Print out CORS configuration details for debugging
print(f"Configuring CORS with allowed origins: {settings.CORS_ORIGINS}")

# ─── 1) CORS: Using Production CORS Middleware ─────────────────────────────────
app.add_middleware(
    ProductionCORSMiddleware,
    allowed_origins=settings.CORS_ORIGINS
)

# ─── Diagnostic DB Info ─────────────────────────────────────────────────────
print(f"Database URL: {settings.DATABASE_URL}")
db_path = settings.DATABASE_URL.replace("sqlite:///", "")
print(f"Database absolute path: {os.path.abspath(db_path)}")
print(f"Database exists: {os.path.exists(os.path.abspath(db_path))}")

# ─── Startup: ensure tables + admin user ──────────────────────────────────────
@app.on_event("startup")
async def startup_db_client():
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print(f"Admin user exists: {admin.username}, {admin.email}")
            valid = bcrypt.checkpw(
                "admin123".encode("utf-8"),
                admin.hashed_password.encode("utf-8"),
            )
            print(f"Admin password valid: {valid}")
        else:
            print("WARNING: Admin user does not exist!")
        db.close()
    except Exception:
        print("Database startup error:")
        print(traceback.format_exc())

# ─── 2) Strip '/api-proxy' prefix ────────────────────────────────────────────
class StripApiProxyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api-proxy"):
            request.scope["path"] = request.url.path[len("/api-proxy"):]
        return await call_next(request)

app.add_middleware(StripApiProxyMiddleware)

# ─── 3) Exception handler that still emits CORS headers ──────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin", "")
    headers = {}
    
    # Only set the Access-Control-Allow-Origin header if the origin is in our allowed list
    if origin in settings.CORS_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        headers["Access-Control-Allow-Headers"] = "*"
        headers["Access-Control-Expose-Headers"] = "*"
    
    print("UNHANDLED ERROR:", traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
        headers=headers,
    )

# ─── 4) Your API routers ────────────────────────────────────────────────────
app.include_router(user.router, prefix=settings.API_V1_STR, tags=["users"])
app.include_router(topic.router, prefix=settings.API_V1_STR, tags=["topics"])
app.include_router(quiz.router, prefix=settings.API_V1_STR, tags=["quizzes"])
app.include_router(
    content_generation.router, prefix=settings.API_V1_STR, tags=["content"]
)

# ─── 5) Root endpoint ───────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Welcome to AI-Powered Learning Companion API"}

# ─── 6) Run ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)
