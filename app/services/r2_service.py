import uuid
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def upload_fileobj(file_obj, key: str, content_type: str = "application/octet-stream") -> str:
    """Upload a file-like object to R2 and return its public URL."""
    _client().upload_fileobj(
        file_obj,
        settings.R2_BUCKET_NAME,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return f"{settings.R2_PUBLIC_URL.rstrip('/')}/{key}"


def delete_object(key: str) -> None:
    try:
        _client().delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
    except ClientError:
        pass


def make_key(prefix: str, filename: str) -> str:
    return f"{prefix}/{uuid.uuid4()}_{filename}"
