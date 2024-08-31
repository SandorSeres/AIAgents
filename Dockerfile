# Alap kép meghatározása, Python 3.11 verzióval
FROM python:3.11-slim

# Munkakönyvtár létrehozása a konténeren belül
WORKDIR /app

# A szükséges Python csomagok telepítéséhez szükséges függőségek telepítése
RUN apt-get update && apt-get install -y \
    gcc git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# A requirements fájl másolása és a pip csomagok telepítése
COPY requirements.txt .
COPY .env .

RUN pip install --no-cache-dir -r requirements.txt

# A forráskód és konfigurációk másolása a konténerbe
COPY config/ config/
COPY src/ src/
COPY static/ static/

# A konténer indításakor futtatandó parancs megadása
CMD ["python", "src/server.py"]

