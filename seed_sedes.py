from backend.database import SessionLocal
from backend.models import Sede

def seed_sedes():
    db = SessionLocal()
    sedes_data = [
        "SEDE RECUERDO",
        "SEDE VERSALLES",
        "SEDE SAN IGNACIO",
        "SEDE LAS CUADRAS VIP"
    ]
    
    try:
        for nombre in sedes_data:
            # Verificar si existe
            exists = db.query(Sede).filter(Sede.sd_nombre == nombre).first()
            if not exists:
                # Crear la sede
                new_sede = Sede(sd_nombre=nombre, sd_direccion="Dirección pendiente")
                db.add(new_sede)
                print(f"Agregada: {nombre}")
            else:
                print(f"Ya existe: {nombre}")
        
        db.commit()
        print("Seeding completado.")
    except Exception as e:
        print(f"Error seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_sedes()
