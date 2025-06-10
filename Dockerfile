FROM python:3.10-slim
# Set working directory
WORKDIR /app 

COPY artifact.zip .

RUN apt-get update && apt-get install -y unzip \
 && unzip artifact.zip -d . \
 && pip install --no-cache-dir -r requirements.txt \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# Change working dir to Fast_API folder where main.py is
WORKDIR /app/Fast_API

EXPOSE 8000

# Run uvicorn from inside Fast_API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
