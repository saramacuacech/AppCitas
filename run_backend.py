import uvicorn
import os
import sys

# Asegurar que el directorio actual esté en el path (aunque al correr desde raíz ya debería estar)
sys.path.append(os.getcwd())

if __name__ == "__main__":
    print("Iniciando servidor backend...")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
