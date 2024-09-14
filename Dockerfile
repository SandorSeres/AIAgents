# NVIDIA alapú Python képfájl használata GPU támogatással
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Python telepítése
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev gcc git curl libgl1-mesa-glx libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Frissítjük a pip-et
RUN python3 -m pip install --upgrade pip

# Munkakönyvtár létrehozása
WORKDIR /app

# A requirements fájl másolása és a pip csomagok telepítése
COPY requirements.txt .
COPY .env .

RUN pip install --no-cache-dir -r requirements.txt

# A forráskód és konfigurációk másolása a konténerbe
COPY config/ config/
COPY src/ src/
COPY static/ static/

# A konténer indításakor futtatandó parancs megadása
CMD ["python3", "src/server.py"]
