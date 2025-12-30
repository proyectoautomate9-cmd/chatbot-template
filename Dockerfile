FROM python:3.13-slim

WORKDIR /app

# Compilador C por si alguna wheel lo necesita
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Instalar numpy y pandas primero usando wheels
RUN pip install --no-cache-dir numpy==2.0.0 pandas==2.2.1

# Instalar el resto de dependencias (sin tocar numpy/pandas)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "app.main"]
