from backend.database import SessionLocal
from backend.models import Empresa

def seed_empresas():
    db = SessionLocal()
    empresas_data = [
        "EMSSANAR",
        "MALLAMAS",
    ]

    try:
        for nombre in empresas_data:
            exists = db.query(Empresa).filter(Empresa.em_nombre == nombre).first()

            if not exists:
                new_empresa = Empresa(
                    em_nombre=nombre,
                    em_cant_max=0,
                    em_cant_pri=0,
                )
                db.add(new_empresa)
                print(f"Agregada: {nombre}")
            else:
                print(f"Ya existe: {nombre}")

        db.commit()
        print("Seeding de empresas completado.")
    except Exception as e:
        print(f"Error seeding empresas: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_empresas()
