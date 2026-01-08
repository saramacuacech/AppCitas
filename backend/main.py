from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, database

# Crear las tablas en la base de datos
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Dependencia para obtener la sesión de base de datos
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Configurar CORS para permitir peticiones desde el frontend (Flet en modo web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir a los dominios autorizados
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoginRequest(BaseModel):
    usuario: str
    password: str

class RegisterRequest(BaseModel):
    usuario: str
    password: str

class CitaCreate(BaseModel):
    nombre_paciente: str
    cedula_paciente: str
    sede: str
    laboratorio: str
    fecha: str
    empresa_paciente: str | None = None

import hashlib

def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

@app.on_event("startup")
def startup_event():
    db = database.SessionLocal()
    try:
        # Seed Roles
        roles = ["Admin", "Agente", "Paciente"]
        for r_name in roles:
            existing_role = db.query(models.Rol).filter(models.Rol.r_name == r_name).first()
            if not existing_role:
                db.add(models.Rol(r_name=r_name))
        db.commit()

        # Seed Estados
        estados = ["Pendiente", "Confirmada", "Cancelada", "No asistió"]
        for e_name in estados:
            existing_estado = db.query(models.Estado).filter(models.Estado.name == e_name).first()
            if not existing_estado:
                db.add(models.Estado(name=e_name))
        db.commit()

        # Seed Users
        # Admin
        admin_user = db.query(models.Usuario).filter(models.Usuario.usr_name == "admin").first()
        if not admin_user:
            # Buscar ID del rol Admin
            rol_admin = db.query(models.Rol).filter(models.Rol.r_name == "Admin").first()
            db.add(models.Usuario(usr_name="admin", usr_password=hash_password("admin123"), rol_id=rol_admin.r_id))
        
        # Agente
        agente_user = db.query(models.Usuario).filter(models.Usuario.usr_name == "agente").first()
        if not agente_user:
             # Buscar ID del rol Agente
            rol_agente = db.query(models.Rol).filter(models.Rol.r_name == "Agente").first()
            db.add(models.Usuario(usr_name="agente", usr_password=hash_password("agente123"), rol_id=rol_agente.r_id))

        db.commit()
        print("Datos de inicio (Roles, Estados, Usuarios) verificados/creados.")
    finally:
        db.close()

@app.post("/citas")
def crear_cita(cita: CitaCreate, db: Session = Depends(get_db)):
    # Validar turnos disponibles antes de crear la cita
    sede = db.query(models.Sede).filter(models.Sede.sd_nombre == cita.sede).first()
    if sede and sede.sd_cant_turnos:
        # Contar citas existentes para esta sede y fecha
        turnos_ocupados = db.query(models.Cita).filter(
            models.Cita.c_sede == cita.sede,
            models.Cita.c_fecha == cita.fecha
        ).count()
        
        # Verificar si hay turnos disponibles
        if turnos_ocupados >= sede.sd_cant_turnos:
            raise HTTPException(
                status_code=400, 
                detail=f"No hay turnos disponibles para la sede {cita.sede} en la fecha {cita.fecha}. Turnos ocupados: {turnos_ocupados}/{sede.sd_cant_turnos}"
            )
    
    empresa_id = None
    if cita.empresa_paciente:
        # Buscar o crear empresa
        empresa = db.query(models.Empresa).filter(models.Empresa.em_nombre == cita.empresa_paciente).first()
        if not empresa:
            empresa = models.Empresa(em_nombre=cita.empresa_paciente)
            db.add(empresa)
            db.commit()
            db.refresh(empresa)
        empresa_id = empresa.em_id
        
        # Validar turnos por empresa
        if empresa.em_cant_max:
            turnos_ocupados_empresa = db.query(models.Cita).join(models.Paciente).filter(
                models.Paciente.pt_empresa_id == empresa_id,
                models.Cita.c_fecha == cita.fecha
            ).count()
            
            if turnos_ocupados_empresa >= empresa.em_cant_max:
                raise HTTPException(
                    status_code=400,
                    detail=f"La empresa {cita.empresa_paciente} no tiene cupos disponibles para la fecha {cita.fecha}."
                )

    # 1. Buscar si el paciente existe por cédula
    paciente = db.query(models.Paciente).filter(models.Paciente.pt_cedula == cita.cedula_paciente).first()
    
    # 2. Si no existe, crearlo
    if not paciente:
        paciente = models.Paciente(
            pt_nombre=cita.nombre_paciente,
            pt_cedula=cita.cedula_paciente,
            pt_empresa_id=empresa_id
        )
        db.add(paciente)
        db.commit()
        db.refresh(paciente)
    else:
        # Si existe y se proporcionó nueva empresa, actualizar
        if empresa_id:
            paciente.pt_empresa_id = empresa_id
            db.commit()
    
    # Buscar estado inicial "Pendiente"
    estado_pendiente = db.query(models.Estado).filter(models.Estado.name == "Pendiente").first()

    # 3. Crear la Cita vinculada al paciente
    nueva_cita = models.Cita(
        c_paciente_id=paciente.pt_id,
        c_sede=cita.sede,
        c_laboratorio=cita.laboratorio,
        c_fecha=cita.fecha,
        c_estado="Pendiente", # Mantener compatibilidad string
        c_estado_id=estado_pendiente.id if estado_pendiente else None
    )
    db.add(nueva_cita)
    db.commit()
    
    return {"message": "Cita creada con éxito", "cita_id": nueva_cita.c_id}

@app.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    usuario_limpio = request.usuario.strip()

    if not usuario_limpio:
        raise HTTPException(status_code=400, detail="El usuario no puede estar vacío")

    existing_user = db.query(models.Usuario).filter(
        models.Usuario.usr_name == usuario_limpio
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    rol_paciente = db.query(models.Rol).filter(
        models.Rol.r_name == "Paciente"
    ).first()

    new_user = models.Usuario(
        usr_name=usuario_limpio,
        usr_password=hash_password(request.password),
        rol_id=rol_paciente.r_id if rol_paciente else None
    )

    db.add(new_user)
    db.commit()

    return {"message": "Registro exitoso"}

@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(
        models.Usuario.usr_name == request.usuario
    ).first()

    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if usuario.usr_password != hash_password(request.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    return {
        "usr_id": usuario.usr_id,
        "usr_name": usuario.usr_name,
        "r_name": usuario.rol.r_name
    }

@app.get("/sedes")
def get_sedes(db: Session = Depends(get_db)):
    sedes = db.query(models.Sede).all()
    return [{
        "id": s.sd_id, 
        "nombre": s.sd_nombre, 
        "dias_atencion": s.sd_dias_atencion,
        "sd_cant_turnos": s.sd_cant_turnos
    } for s in sedes]

@app.get("/sedes/{sede_id}/dias-disponibles")
def get_dias_disponibles(sede_id: int, db: Session = Depends(get_db)):
    sede = db.query(models.Sede).filter(models.Sede.sd_id == sede_id).first()
    if not sede:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    return {"dias_atencion": sede.sd_dias_atencion}

@app.get("/sedes/{sede_nombre}/turnos-disponibles")
def get_turnos_disponibles(sede_nombre: str, fecha: str, db: Session = Depends(get_db)):
    """
    Verifica los turnos disponibles para una sede en una fecha específica.
    """
    # Buscar la sede por nombre
    sede = db.query(models.Sede).filter(models.Sede.sd_nombre == sede_nombre).first()
    if not sede:
        raise HTTPException(status_code=404, detail="Sede no encontrada")
    
    # Si no hay turnos configurados, permitir ilimitados
    turnos_totales = sede.sd_cant_turnos if sede.sd_cant_turnos else 0
    
    # Contar citas existentes para esta sede y fecha
    turnos_ocupados = db.query(models.Cita).filter(
        models.Cita.c_sede == sede_nombre,
        models.Cita.c_fecha == fecha
    ).count()
    
    # Calcular disponibles
    if turnos_totales == 0:
        # Sin límite configurado
        return {
            "turnos_totales": None,
            "turnos_ocupados": turnos_ocupados,
            "turnos_disponibles": None,
            "tiene_disponibilidad": True
        }
    else:
        turnos_disponibles = turnos_totales - turnos_ocupados
        return {
            "turnos_totales": turnos_totales,
            "turnos_ocupados": turnos_ocupados,
            "turnos_disponibles": max(0, turnos_disponibles),
            "tiene_disponibilidad": turnos_disponibles > 0
        }

@app.get("/empresas/{empresa_nombre}/turnos-disponibles")
def get_turnos_empresa_disponibles(empresa_nombre: str, fecha: str, db: Session = Depends(get_db)):
    """
    Verifica los turnos disponibles para una empresa en una fecha específica.
    """
    # Buscar la empresa por nombre
    empresa = db.query(models.Empresa).filter(models.Empresa.em_nombre == empresa_nombre).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    # Si no hay turnos configurados, permitir ilimitados
    turnos_totales = empresa.em_cant_max if empresa.em_cant_max else 0
    
    # Contar citas existentes para esta empresa y fecha
    turnos_ocupados = db.query(models.Cita).join(models.Paciente).filter(
        models.Paciente.pt_empresa_id == empresa.em_id,
        models.Cita.c_fecha == fecha
    ).count()
    
    # Calcular disponibles
    if turnos_totales == 0:
        return {
            "turnos_totales": None,
            "turnos_ocupados": turnos_ocupados,
            "turnos_disponibles": None,
            "tiene_disponibilidad": True
        }
    else:
        turnos_disponibles = turnos_totales - turnos_ocupados
        return {
            "turnos_totales": turnos_totales,
            "turnos_ocupados": turnos_ocupados,
            "turnos_disponibles": max(0, turnos_disponibles),
            "tiene_disponibilidad": turnos_disponibles > 0
        }

@app.get("/citas")
def get_citas(db: Session = Depends(get_db)):
    # Idealmente filtrar por rol, pero por simplicidad retornamos todo (para el agente)
    citas = db.query(models.Cita).all()
    # Construir respuesta con datos relacionados
    resultado = []
    for c in citas:
        paciente = db.query(models.Paciente).filter(models.Paciente.pt_id == c.c_paciente_id).first()
        estado = db.query(models.Estado).filter(models.Estado.id == c.c_estado_id).first()
        
        # Obtener nombre de la empresa si existe
        empresa_nombre = "Particular"
        if paciente and paciente.pt_empresa_id:
            empresa = db.query(models.Empresa).filter(models.Empresa.em_id == paciente.pt_empresa_id).first()
            if empresa:
                empresa_nombre = empresa.em_nombre

        resultado.append({
            "id": c.c_id,
            "paciente_nombre": paciente.pt_nombre if paciente else "Desconocido",
            "paciente_cedula": paciente.pt_cedula if paciente else "Desconocido",
            "empresa": empresa_nombre,
            "sede": c.c_sede,
            "laboratorio": c.c_laboratorio,
            "fecha": c.c_fecha,
            "estado": estado.name if estado else c.c_estado
        })
    return resultado

@app.put("/citas/{cita_id}")
def update_cita(cita_id: int, data: dict, db: Session = Depends(get_db)):
    cita = db.query(models.Cita).filter(models.Cita.c_id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    cita.c_fecha = data["fecha"]
    cita.c_estado = data["estado"]
    db.commit()

    return {"message": "Cita actualizada"}

@app.delete("/citas/{cita_id}")
def delete_cita(cita_id: int, db: Session = Depends(get_db)):
    cita = db.query(models.Cita).filter(models.Cita.c_id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    db.delete(cita)
    db.commit()
    return {"message": "Cita eliminada"}

# Endpoints Admin
class SedeUpdate(BaseModel):
    cant_turnos: int | None = None
    dias_atencion: str | None = None

class EmpresaUpdate(BaseModel):
    cant_turnos: int | None = None

@app.put("/sedes/{sede_id}")
def update_sede(sede_id: int, sede_update: SedeUpdate, db: Session = Depends(get_db)):
    sede = db.query(models.Sede).filter(models.Sede.sd_id == sede_id).first()
    if not sede:
         raise HTTPException(status_code=404, detail="Sede no encontrada")
    
    if sede_update.cant_turnos is not None:
        sede.sd_cant_turnos = sede_update.cant_turnos
    if sede_update.dias_atencion is not None:
        sede.sd_dias_atencion = sede_update.dias_atencion
        
    db.commit()
    return {"message": "Sede actualizada"}

@app.get("/empresas")
def get_empresas(db: Session = Depends(get_db)):
    empresas = db.query(models.Empresa).all()
    return [{"id": e.em_id, "nombre": e.em_nombre, "cant_turnos": e.em_cant_max} for e in empresas]

@app.put("/empresas/{empresa_id}")
def update_empresa(empresa_id: int, empresa_update: EmpresaUpdate, db: Session = Depends(get_db)):
    empresa = db.query(models.Empresa).filter(models.Empresa.em_id == empresa_id).first()
    if not empresa:
         raise HTTPException(status_code=404, detail="Empresa no encontrada")
    
    if empresa_update.cant_turnos is not None:
        empresa.em_cant_max = empresa_update.cant_turnos
        
    db.commit()
    return {"message": "Empresa actualizada"}

@app.put("/usuarios/{usr_id}/username")
def update_username(
    usr_id: int,
    data: dict,
    db: Session = Depends(get_db)
):
    usuario = db.query(models.Usuario).filter(models.Usuario.usr_id == usr_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.usr_name = data["username"]
    db.commit()

    return {"message": "Nombre de usuario actualizado"}

@app.put("/usuarios/{usr_id}/password")
def update_password(usr_id: int, data: dict, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(
        models.Usuario.usr_id == usr_id
    ).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    usuario.usr_password = hash_password(data["password"])
    db.commit()

    return {"message": "Contraseña actualizada"}

@app.get("/")
def read_root():
    return {"message": "API de Citas activa"}
