# app/utils/s3.py
import boto3
import os
from fastapi import HTTPException
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Read S3 config from environment
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

async def upload_file_to_s3(file, filename: str) -> str:
    """
    Uploads a file to S3 and returns the public URL.
    """
    try:
        s3_client.upload_fileobj(
            file.file,
            AWS_BUCKET_NAME,
            filename,
            ExtraArgs={
                "ContentType": file.content_type  # use the MIME type from UploadFile
            }
        )
        return f"https://{AWS_BUCKET_NAME}.s3.amazonaws.com/{filename}"
    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to S3: {str(e)}")
