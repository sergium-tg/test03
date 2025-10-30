from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import ALLOWED_ORIGINS, RATE_LIMIT_API_PER_MIN
from app.db.session import get_db, engine, Base
from app.services.auth_service import AuthService
from app.schemas.schemas import UserResponse
from app.api.routers import auth, clientes

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Inicializar aplicación
app = FastAPI(
    title="API Web Proyecto v0.3",
    description="API para gestión de Clientes con autenticación JWT, rate limiting y SQLite",
    version="0.3.0"
)

# Configurar rate limiting
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Dependencia para obtener usuario actual
async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserResponse:
    """Dependency para validar JWT y obtener usuario actual"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    username = AuthService.decode_token(token)
    
    if username is None:
        raise credentials_exception
    
    user = AuthService.get_user_by_username(db, username)
    
    if user is None:
        raise credentials_exception
    
    # Guardar user_id en request.state para rate limiting
    request.state.user_id = username
    
    return UserResponse(username=user.username)

def user_or_ip_key(request: Request) -> str:
    """Key function para rate limiting por usuario autenticado o IP"""
    return getattr(request.state, "user_id", None) or get_remote_address(request)

# ============== Rutas Públicas ==============

@app.get("/health", tags=["Sistema"])
async def health_check():
    """
    Endpoint de healthcheck para verificar el estado del sistema.
    
    No requiere autenticación.
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "API Web Proyecto v0.3"
    }

# ============== Rutas de Autenticación ==============

app.include_router(auth.router)

# ============== Rutas Protegidas ==============

@app.get("/me", response_model=UserResponse, tags=["Autenticación"])
@limiter.limit(RATE_LIMIT_API_PER_MIN, key_func=user_or_ip_key)
async def get_current_user_info(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Obtener información del usuario autenticado.
    
    Requiere autenticación JWT.
    """
    return current_user

# Incluir routers con protección JWT
app.include_router(
    clientes.router,
    dependencies=[Depends(get_current_user)]
)

# ============== Manejo de Errores ==============

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return {
        "error": "Not Found",
        "detail": "El recurso solicitado no existe",
        "path": str(request.url)
    }

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return {
        "error": "Internal Server Error",
        "detail": "Ocurrió un error interno en el servidor"
    }

# ============== Inicialización de Datos de Prueba ==============

@app.on_event("startup")
async def startup_event():
    """Crear datos de prueba al iniciar la aplicación"""
    db = next(get_db())
    
    try:
        # Crear usuario de prueba si no existe
        test_user = AuthService.get_user_by_username(db, "admin")
        if not test_user:
            AuthService.create_user(db, "admin", "admin123")
            print("✓ Usuario de prueba creado: admin / admin123")
        
        # Crear clientes de prueba
        from app.services.cliente_service import ClienteService
        from app.schemas.schemas import ClienteCreate
        
        clientes_prueba = [
            ClienteCreate(
                id=18008332,
                nombre="Juan",
                apellido="Duran",
                email="judu1@mail.com",
                contacto=3001000000,
                direccion="Av Caracas #123"
            ),
            ClienteCreate(
                id=12350011,
                nombre="Diana",
                apellido="Valentina",
                email="diva1@mail.com",
                contacto=3002000000,
                direccion="Av Quito #772"
            ),
            ClienteCreate(
                id=22315085,
                nombre="Adam",
                apellido="Santana",
                email="ansa1@mail.com",
                contacto=3003000000
            )
        ]
        
        for cliente_data in clientes_prueba:
            existing = ClienteService.get_cliente_by_id(db, cliente_data.id)
            if not existing:
                ClienteService.create_cliente(db, cliente_data)
                print(f"✓ Cliente de prueba creado: {cliente_data.nombre} {cliente_data.apellido}")
        
        print("✓ Datos de prueba inicializados correctamente")
    except Exception as e:
        print(f"✗ Error al inicializar datos de prueba: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)