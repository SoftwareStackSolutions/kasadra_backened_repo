FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy the zipped artifact
COPY artifact.zip .

# Install unzip and pip dependencies
RUN apt-get update && apt-get install -y unzip \
 && unzip artifact.zip -d . \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Expose FastAPI default port
EXPOSE 8000

# Run FastAPI app (update if your main file is inside a folder)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
