from google.cloud import storage
import uuid

async def upload_file_to_gcs(file, folder_name):
    bucket_name = "kasadra-project-bucket"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Generate unique filename
    unique_name = f"{folder_name}/{uuid.uuid4()}_{file.filename}"

    blob = bucket.blob(unique_name)
    blob.upload_from_file(file.file, content_type=file.content_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{unique_name}"
    return public_url
