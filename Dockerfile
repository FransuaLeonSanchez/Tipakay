FROM python:3.12-slim

# Evitar escritura de archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Asegurar que la salida de Python se envíe directamente a la terminal
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema en una sola capa
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip

# Copiar e instalar requirements primero para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Usar uvicorn directamente en lugar de python main.py
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]