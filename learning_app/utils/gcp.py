from google.cloud import storage

async def upload_file_to_gcs(file, destination_blob_name):
    bucket_name = "kasadra-project-bucket"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_file(file.file, content_type=file.content_type)

    # Don't call blob.make_public() because Uniform Bucket-Level Access is enabled
    public_url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
    return public_url
