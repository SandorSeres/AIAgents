#!/bin/bash

# Exit on any error
set -e

# 1. Bejelentkezés a Google Cloud SDK-val
echo "Bejelentkezés a Google Cloud SDK-ba..."
gcloud auth login

# 2. Google Cloud projekt beállítása
PROJECT_ID="multi-agent-ai"
echo "Projekt kiválasztása: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# 3. Szükséges API-k engedélyezése (Cloud Run és Container Registry)
echo "Cloud Run és Container Registry API-k engedélyezése..."
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 4. Docker hitelesítés a Google Container Registry-hez
echo "Docker hitelesítés a Google Container Registry-hez..."
gcloud auth configure-docker

############################################
gcloud init
PROJECT_ID="multi-agent-ai"

# 5. Docker image buildelése
IMAGE_NAME="multi-agent-app"
echo "Docker image buildelése: gcr.io/$PROJECT_ID/$IMAGE_NAME:latest"
docker build -t gcr.io/$PROJECT_ID/$IMAGE_NAME:latest .

# 6. Docker image pusholása a Google Container Registry-be
echo "Docker image feltöltése a Google Container Registry-be..."
docker push gcr.io/$PROJECT_ID/$IMAGE_NAME:latest

# 7. Alkalmazás deployolása a Google Cloud Run-ra
SERVICE_NAME="multi-agent-service"
REGION="europe-west1"
echo "Alkalmazás deployolása a Google Cloud Run-ra..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$IMAGE_NAME:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080

# 8. URL megjelenítése a Cloud Run szolgáltatás eléréséhez
URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format "value(status.url)")
echo "Az alkalmazás sikeresen telepítve. Elérhető itt: $URL"

# 9. (Opcionális) Környezeti változók beállítása
# Példa környezeti változók hozzáadására (távolítsd el a komment jelet, ha szükséges)
# echo "Környezeti változók beállítása..."
# gcloud run services update $SERVICE_NAME \
#   --set-env-vars VAR1=value1,VAR2=value2

# 10. (Opcionális) Titkos adatok hozzáadása
# Példa Secret Manager használatára (távolítsd el a komment jelet, ha szükséges)
# echo "Titkos adatok beállítása a Secret Manager használatával..."
# echo -n "SECRET_VALUE" | gcloud secrets create SECRET_NAME --data-file=-
# gcloud run services update $SERVICE_NAME \
#   --update-secrets ENV_VAR_NAME=SECRET_NAME:latest

echo "Minden lépés sikeresen lefutott!"

