FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy artifact
COPY artifact.zip /app/artifact.zip

# Install unzip and any required build tools
RUN apt-get update && apt-get install -y unzip

# Unzip package
RUN unzip artifact.zip -d .

# Optional: Install dependencies if needed
# RUN pip install .

# Expose FastAPI port
EXPOSE 8000

# Run the FastAPI app (adjust path/module name as needed)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
