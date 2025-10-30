from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class Cliente(Base):
    __tablename__ = "clientes"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    contacto = Column(Integer, nullable=False)
    direccion = Column(String, nullable=True)
    
    # Relación con órdenes (preparado para futura implementación)
    ordenes = relationship("Orden", back_populates="cliente", cascade="all, delete-orphan")

class Orden(Base):
    """Modelo preparado para futura implementación"""
    __tablename__ = "ordenes"
    
    consecutivo = Column(Integer, primary_key=True, index=True)
    tipo = Column(String, nullable=False)
    id_cliente = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    
    # Relación con cliente
    cliente = relationship("Cliente", back_populates="ordenes")