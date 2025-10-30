from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

# ============== Esquemas de Autenticación ==============

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserResponse(BaseModel):
    username: str
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ============== Esquemas de Cliente ==============

class OrdenBase(BaseModel):
    """Esquema base para Orden (preparado para futura implementación)"""
    consecutivo: int
    tipo: str
    id_cliente: int

class OrdenResponse(OrdenBase):
    class Config:
        from_attributes = True

class ClienteBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    apellido: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    contacto: int = Field(..., ge=300000000, le=9999999999)
    direccion: Optional[str] = Field(None, max_length=255)

class ClienteCreate(ClienteBase):
    id: int = Field(..., ge=100000, description="El documento debe tener al menos 6 dígitos")

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    apellido: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    contacto: Optional[int] = Field(None, ge=300000000, le=9999999999)
    direccion: Optional[str] = Field(None, max_length=255)

class ClienteResponse(ClienteBase):
    id: int
    ordenes: List[OrdenResponse] = []
    
    class Config:
        from_attributes = True