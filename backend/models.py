from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Paciente(Base):
    __tablename__ = "Paciente"

    pt_id = Column(Integer, primary_key=True, index=True)
    pt_nombre = Column(String)
    pt_cedula = Column(String, unique=True, index=True)
    pt_empresa_id = Column(Integer, ForeignKey("Empresas.em_id"), nullable=True)

    citas = relationship("Cita", back_populates="paciente")
    empresa = relationship("Empresa", back_populates="pacientes")

class Empresa(Base):
    __tablename__ = "Empresas"

    em_id = Column(Integer, primary_key=True, index=True)
    em_nombre = Column(String(100))
    em_created_at = Column(String, nullable=True)
    em_updated_at = Column(String, nullable=True)
    em_cant_max = Column(Integer, nullable=True) # Cantidad de turnos
    em_cant_pri = Column(Integer, nullable=True) # Cantidad prioridad (opcional)

    pacientes = relationship("Paciente", back_populates="empresa")

class Cita(Base):
    __tablename__ = "Citas"

    c_id = Column(Integer, primary_key=True, index=True)
    c_paciente_id = Column(Integer, ForeignKey("Paciente.pt_id"))
    c_sede = Column(String)
    c_laboratorio = Column(String)
    c_fecha = Column(String)
    c_estado = Column(String, default="Pendiente")
    c_estado_id = Column(Integer, ForeignKey("Estados.id"), nullable=True)
    c_created_at = Column(String, nullable=True)
    c_updated_at = Column(String, nullable=True)

    paciente = relationship("Paciente", back_populates="citas")
    estado = relationship("Estado", back_populates="citas")

class Usuario(Base):
    __tablename__ = "Usuarios"

    usr_id = Column(Integer, primary_key=True, index=True)
    usr_name = Column(String, unique=True, index=True)
    usr_password = Column(String)
    rol_id = Column(Integer, ForeignKey("Roles.r_id"), nullable=True)
    usr_created_at = Column(String, nullable=True)
    usr_updated_at = Column(String, nullable=True)

    rol = relationship("Rol", back_populates="usuarios")

class Sede(Base):
    __tablename__ = "Sedes"

    sd_id = Column(Integer, primary_key=True, index=True)
    sd_nombre = Column(String(255), unique=True, index=True)
    sd_direccion = Column(String, nullable=True)
    sd_map_coord = Column(String, nullable=True)
    sd_cant_turnos = Column(Integer, nullable=True)
    sd_dias_atencion = Column(String, nullable=True) # Días disponibles
    sd_created_at = Column(String, nullable=True)
    sd_updated_at = Column(String, nullable=True)

class Rol(Base):
    __tablename__ = "Roles"

    r_id = Column(Integer, primary_key=True, index=True)
    r_name = Column(String(255))
    r_created_at = Column(String, nullable=True)
    r_updated_at = Column(String, nullable=True)

    usuarios = relationship("Usuario", back_populates="rol")

class Estado(Base):
    __tablename__ = "Estados"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))

    citas = relationship("Cita", back_populates="estado")
