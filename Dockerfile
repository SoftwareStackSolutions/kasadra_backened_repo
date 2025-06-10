FROM python:3.10-slim

<<<<<<< HEAD
# Set working directory
WORKDIR /app 
=======
WORKDIR /app
>>>>>>> 3279e1d55dbd1a19bdb4aa03f33c1a16fde7447b

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
