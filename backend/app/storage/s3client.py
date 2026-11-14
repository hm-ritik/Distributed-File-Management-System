
import boto3

from app.core.config import settings

s3_client = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
)

S3_BUCKET = settings.S3_BUCKET_NAME
