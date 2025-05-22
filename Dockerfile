FROM python:3.10-slim

# Set working directory 
WORKDIR /app

# Copy the backend artifact ZIP file
COPY artifact.zip ./artifact.zip

# Install unzip, curl, Node.js, and npm, then install serve
RUN apt-get update && apt-get install -y unzip curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g serve

# Unzip the artifact
RUN unzip artifact.zip -d backend-project && \
    BACKEND_DIR=$(find backend-project -mindepth 1 -maxdepth 1 -type d | head -n 1) && \
    echo "Detected project folder: $BACKEND_DIR" && \
    mv "$BACKEND_DIR" backend-app

# Change working directory to the actual project code
WORKDIR /app/backend-app

# Optional: Install pip requirements if any
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Expose your app port (e.g., FastAPI default port)
EXPOSE 8000

# Run the Python app (adjust as needed)
CMD ["python", "main.py"]
