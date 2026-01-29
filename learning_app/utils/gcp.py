from google.cloud import storage
import uuid

async def upload_file_to_gcs(file, folder_name):
    bucket_name = "kasadra-project-bucket"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    unique_name = f"{folder_name}/{uuid.uuid4()}_{file.filename}"
    blob = bucket.blob(unique_name)

    # 🔥 FIX STARTS HERE
    blob.content_type = file.content_type or "application/octet-stream"
    blob.content_disposition = "inline"
    # 🔥 FIX ENDS HERE

    blob.upload_from_file(file.file)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{unique_name}"
    return public_url
