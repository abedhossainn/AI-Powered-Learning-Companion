import os
import secrets
from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Project name and API settings
    PROJECT_NAME: str = "AI-Powered Learning Companion"
    API_V1_STR: str = "/api/v1"
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173", 
        "http://localhost:5174", 
        "http://10.0.0.10:5174", 
        "http://localhost:3000", 
        "https://ailearning.cbtbags.com",
        "https://apiailearning.cbtbags.com"
    ]
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./learning_companion.db")
    
    # Firebase settings
    FIREBASE_CREDENTIALS_JSON: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_JSON")
    FIREBASE_SERVICE_ACCOUNT_PATH: str = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_PATH", 
        "../firebase-service-account.json"
    )
    
    # AI model settings
    USE_LOCAL_MODELS: bool = os.getenv("USE_LOCAL_MODELS", "False").lower() == "true"
    HUGGINGFACE_API_TOKEN: Optional[str] = os.getenv("HUGGINGFACE_API_TOKEN")
    
    # Knowledge Tracing parameters (BKT - Bayesian Knowledge Tracing)
    BKT_DEFAULT_INIT_P_KNOW: float = 0.3  # Initial probability of knowing a concept
    BKT_DEFAULT_LEARN: float = 0.2  # Probability of learning a concept if previously unknown
    BKT_DEFAULT_GUESS: float = 0.25  # Probability of guessing correctly if unknown
    BKT_DEFAULT_SLIP: float = 0.1  # Probability of making a mistake if known

    # OpenAI settings removed
    
    # Gemini AI settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")  # Add your API key to .env file
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    CONTENT_GENERATION_MODEL: str = os.getenv("CONTENT_GENERATION_MODEL", "gemini-2.0-flash")
    USE_GEMINI: bool = True  # Always use Gemini API since OpenAI is removed

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()