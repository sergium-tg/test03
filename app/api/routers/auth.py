from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.schemas.schemas import UserCreate, UserResponse, Token
from app.services.auth_service import AuthService
from app.core.config import RATE_LIMIT_AUTH_PER_MIN

router = APIRouter(prefix="/auth", tags=["Autenticación"])
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMIT_AUTH_PER_MIN)
def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Registrar un nuevo usuario.
    
    - **username**: Nombre de usuario único (mínimo 3 caracteres)
    - **password**: Contraseña (mínimo 6 caracteres)
    """
    user = AuthService.create_user(db, user_data.username, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado"
        )
    
    return user

@router.post("/login", response_model=Token)
@limiter.limit(RATE_LIMIT_AUTH_PER_MIN)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Iniciar sesión y obtener token JWT.
    
    - **username**: Nombre de usuario
    - **password**: Contraseña
    """
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    access_token = AuthService.create_access_token(data={"sub": user.username})
    
    return Token(access_token=access_token, token_type="bearer")