from fastapi import APIRouter, HTTPException, status, Depends, Query, Request, Response
from sqlalchemy.orm import Session
from typing import List
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.schemas.schemas import ClienteCreate, ClienteUpdate, ClienteResponse
from app.services.cliente_service import ClienteService
from app.core.config import RATE_LIMIT_API_PER_MIN

router = APIRouter(prefix="/clientes", tags=["Clientes"])
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")

def user_or_ip_key(request: Request) -> str:
    """Rate limiting por usuario autenticado o IP"""
    return getattr(request.state, "user_id", None) or get_remote_address(request)

@router.post("", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMIT_API_PER_MIN, key_func=user_or_ip_key)
def crear_cliente(
    request: Request,
    cliente_data: ClienteCreate,
    db: Session = Depends(get_db)
):
    """
    Crear un nuevo cliente.
    
    - **id**: Documento de identidad (mínimo 6 dígitos)
    - **nombre**: Nombre del cliente
    - **apellido**: Apellido del cliente
    - **email**: Correo electrónico único
    - **contacto**: Número de teléfono
    - **direccion**: Dirección (opcional)
    """
    cliente = ClienteService.create_cliente(db, cliente_data)
    
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cliente con ese ID o email ya existe en la base de datos"
        )
    
    return cliente

@router.get("/todos", response_model=List[ClienteResponse])
@limiter.limit(RATE_LIMIT_API_PER_MIN, key_func=user_or_ip_key)
def listar_clientes(
    request: Request,
    db: Session = Depends(get_db)
):
    """Listar todos los clientes"""
    return ClienteService.get_all_clientes(db)

@router.get("/{cliente_id}", response_model=ClienteResponse)
@limiter.limit(RATE_LIMIT_API_PER_MIN, key_func=user_or_ip_key)
def obtener_cliente(
    request: Request,
    cliente_id: int,
    db: Session = Depends(get_db)
):
    """Obtener información de un cliente por ID"""
    cliente = ClienteService.get_cliente_by_id(db, cliente_id)
    
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no encontrado"
        )
    
    return cliente

@router.put("/{cliente_id}", response_model=ClienteResponse)
@limiter.limit(RATE_LIMIT_API_PER_MIN, key_func=user_or_ip_key)
def actualizar_cliente(
    request: Request,
    cliente_id: int,
    cliente_data: ClienteUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar información de un cliente.
    
    Todos los campos son opcionales. Solo se actualizarán los campos proporcionados.
    """
    try:
        cliente = ClienteService.update_cliente(db, cliente_id, cliente_data)
        
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente con ID {cliente_id} no encontrado"
            )
        
        return cliente
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(RATE_LIMIT_API_PER_MIN, key_func=user_or_ip_key)
def eliminar_cliente(
    request: Request,
    cliente_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar un cliente por ID"""
    result = ClienteService.delete_cliente(db, cliente_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con ID {cliente_id} no encontrado"
        )
    
    if result is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el cliente porque tiene órdenes asociadas"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("", response_model=List[ClienteResponse])
@limiter.limit(RATE_LIMIT_API_PER_MIN, key_func=user_or_ip_key)
def buscar_clientes(
    request: Request,
    response: Response,
    q: str = Query(None, description="Buscar por nombre, apellido o email"),
    sort: str = Query("apellido", regex="^(nombre|apellido)$", description="Ordenar por: nombre | apellido"),
    order: str = Query("asc", regex="^(asc|desc)$", description="Orden: asc | desc"),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Resultados por página"),
    db: Session = Depends(get_db)
):
    """
    Buscar y filtrar clientes con paginación.
    
    - **q**: Término de búsqueda (busca en nombre, apellido y email)
    - **sort**: Campo para ordenar (nombre o apellido)
    - **order**: Orden ascendente o descendente
    - **page**: Número de página
    - **limit**: Cantidad de resultados por página
    """
    offset = (page - 1) * limit
    results, total = ClienteService.search_and_sort_clientes(
        db, q=q, sort=sort, order=order, offset=offset, limit=limit
    )
    
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(page)
    response.headers["X-Per-Page"] = str(limit)
    response.headers["X-Total-Pages"] = str((total + limit - 1) // limit)
    
    return results