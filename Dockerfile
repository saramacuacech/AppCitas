# Usar una imagen base liviana de Python
FROM python:3.11-slim

# Evitar que Python genere archivos .pyc y permitir que los logs lleguen al terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias (si las hay)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requerimientos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Exponer el puerto que usará FastAPI (usualmente 8000 o el que defina el host)
EXPOSE 8000

# Comando para ejecutar la aplicación (Backend)
# En producción, usamos gunicorn con workers de uvicorn para mejor rendimiento
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "backend.main:app", "--bind", "0.0.0.0:8000"]
