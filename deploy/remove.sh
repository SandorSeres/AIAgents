echo y | gcloud run services delete multi-agent-service --region europe-west1
echo y | gcloud container images delete gcr.io/multi-agent-ai/multi-agent-app:latest

