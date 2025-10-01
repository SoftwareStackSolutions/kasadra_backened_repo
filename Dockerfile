
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy artifact
COPY artifact.zip .

# Unzip and install dependencies
RUN apt-get update && apt-get install -y unzip \
 && unzip artifact.zip -d . \
 && pip install --no-cache-dir -r learning_app/requirements.txt \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set PYTHONPATH so Python can find learning_app
ENV PYTHONPATH=/app

# Change working dir to FastAPI app folder
WORKDIR /app/learning_app

EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

