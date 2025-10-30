import os
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-to-a-secure-random-key-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Rate Limiting
RATE_LIMIT_AUTH_PER_MIN = os.getenv("RATE_LIMIT_AUTH_PER_MIN", "5/minute")
RATE_LIMIT_API_PER_MIN = os.getenv("RATE_LIMIT_API_PER_MIN", "60/minute")
RATE_LIMIT_BURST = os.getenv("RATE_LIMIT_BURST", "10/second")

# CORS
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")