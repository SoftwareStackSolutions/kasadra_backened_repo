# Use an official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install unzip
RUN apt-get update && apt-get install -y unzip

# Copy and unzip the Python artifact
COPY artifact.zip ./artifact.zip
RUN unzip artifact.zip -d .

# Install dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose the port FastAPI runs on
EXPOSE 8000

# Run FastAPI app using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
