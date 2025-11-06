import boto3
import uuid
import re
from fastapi import HTTPException, UploadFile
from botocore.exceptions import BotoCoreError, ClientError
from app.config import settings
from urllib.parse import urlparse
from sqlalchemy.orm import Session

def generate_safe_filename(folder_prefix: str, base_name: str, original_filename: str) -> str:
    file_ext = original_filename.split(".")[-1] if "." in original_filename else "jpg"
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", base_name.strip().lower())
    return f"{folder_prefix}/{safe_name}.{file_ext}"


def upload_file_to_s3(file: UploadFile, file_name: str) -> str:
    if not settings.AWS_S3_BUCKET:
        raise HTTPException(status_code=500, detail="AWS_S3_BUCKET not configured")

    region = settings.AWS_REGION
    base_url = f"https://{settings.AWS_S3_BUCKET}.s3.{region}.amazonaws.com"

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        aws_session_token=settings.AWS_SESSION_TOKEN,
        region_name=region
    )

    try:
        s3.upload_fileobj(
            file.file,
            settings.AWS_S3_BUCKET,
            file_name,
            ExtraArgs={"ContentType": file.content_type}
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")

    return f"{base_url}/{file_name}"


from ..config import settings  # adjust import if needed

def delete_old_file_from_s3(image_url: str):
    """Deletes an existing file from S3, given its full image URL."""
    if not image_url or not image_url.startswith("http"):
        return

    # Extract the S3 object key safely
    parsed_url = urlparse(image_url)
    key = parsed_url.path.lstrip("/")  # removes leading '/'

    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        aws_session_token=settings.AWS_SESSION_TOKEN,
        region_name=settings.AWS_REGION
    )

    try:
        s3.delete_object(Bucket=settings.AWS_S3_BUCKET, Key=key)
        print(f"Deleted from S3: {key}")
    except ClientError as e:
        print(f"Failed to delete from S3: {e}")

