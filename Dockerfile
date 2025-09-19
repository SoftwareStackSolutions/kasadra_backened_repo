FROM python:3.10-slim

WORKDIR /app

# Copy the unzipped artifact
COPY app/ .

# Install dependencies
RUN apt-get update && apt-get install -y unzip \
 && pip install --no-cache-dir -r learning_app/requirements.txt \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=/app

WORKDIR /app/learning_app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
