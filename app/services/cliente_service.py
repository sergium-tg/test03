from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Tuple
from app.models.models import Cliente
from app.schemas.schemas import ClienteCreate, ClienteUpdate

class ClienteService:
    @staticmethod
    def create_cliente(db: Session, cliente_data: ClienteCreate) -> Optional[Cliente]:
        """Crear un nuevo cliente"""
        # Verificar si el cliente ya existe
        existing = db.query(Cliente).filter(
            or_(Cliente.id == cliente_data.id, Cliente.email == cliente_data.email)
        ).first()
        
        if existing:
            return None
        
        cliente = Cliente(**cliente_data.model_dump())
        db.add(cliente)
        db.commit()
        db.refresh(cliente)
        return cliente
    
    @staticmethod
    def get_cliente_by_id(db: Session, cliente_id: int) -> Optional[Cliente]:
        """Obtener un cliente por ID"""
        return db.query(Cliente).filter(Cliente.id == cliente_id).first()
    
    @staticmethod
    def get_all_clientes(db: Session) -> List[Cliente]:
        """Obtener todos los clientes"""
        return db.query(Cliente).all()
    
    @staticmethod
    def update_cliente(
        db: Session, 
        cliente_id: int, 
        cliente_data: ClienteUpdate
    ) -> Optional[Cliente]:
        """Actualizar un cliente"""
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        
        if not cliente:
            return None
        
        update_data = cliente_data.model_dump(exclude_unset=True)
        
        if not update_data:
            return cliente  # No hay cambios
        
        # Verificar si el email ya existe en otro cliente
        if "email" in update_data and update_data["email"] != cliente.email:
            existing_email = db.query(Cliente).filter(
                Cliente.email == update_data["email"],
                Cliente.id != cliente_id
            ).first()
            if existing_email:
                raise ValueError("El email ya está registrado")
        
        for key, value in update_data.items():
            setattr(cliente, key, value)
        
        db.commit()
        db.refresh(cliente)
        return cliente
    
    @staticmethod
    def delete_cliente(db: Session, cliente_id: int) -> bool:
        """Eliminar un cliente"""
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        
        if not cliente:
            return None
        
        # Verificar si tiene órdenes asociadas
        if cliente.ordenes:
            return False
        
        db.delete(cliente)
        db.commit()
        return True
    
    @staticmethod
    def search_and_sort_clientes(
        db: Session,
        q: Optional[str] = None,
        sort: str = "apellido",
        order: str = "asc",
        offset: int = 0,
        limit: int = 10
    ) -> Tuple[List[Cliente], int]:
        """Buscar y ordenar clientes con paginación"""
        query = db.query(Cliente)
        
        # Búsqueda
        if q:
            search_filter = or_(
                Cliente.nombre.ilike(f"%{q}%"),
                Cliente.apellido.ilike(f"%{q}%"),
                Cliente.email.ilike(f"%{q}%")
            )
            query = query.filter(search_filter)
        
        # Total de resultados
        total = query.count()
        
        # Ordenamiento
        if sort == "nombre":
            query = query.order_by(Cliente.nombre.desc() if order == "desc" else Cliente.nombre.asc())
        else:  # por defecto apellido
            query = query.order_by(Cliente.apellido.desc() if order == "desc" else Cliente.apellido.asc())
        
        # Paginación
        results = query.offset(offset).limit(limit).all()
        
        return results, total