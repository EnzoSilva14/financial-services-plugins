from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import whatsapp, auth, admin, n8n
from app.services.session_service import SessionService
from app.database import engine, Base
from app.config import get_settings
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup
@app.on_event("startup")
async def startup():
    logger.info("🚀 Iniciando OSIRA Wealth Agent...")
    
    # Conectar ao Redis
    session_service = SessionService()
    await session_service.connect()
    
    logger.info("✅ Conectado ao Redis")

# Routers
app.include_router(whatsapp.router, prefix="/api", tags=["WhatsApp"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(n8n.router, prefix="/api", tags=["n8n Integration"])

@app.get("/")
async def root():
    return {"message": "OSIRA Wealth Agent API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
