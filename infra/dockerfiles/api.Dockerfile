FROM python:3.11-slim

WORKDIR /app
COPY api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY api/ ./api/
WORKDIR /app/api
EXPOSE 5000
CMD ["python", "artefato_tracker.py"]
