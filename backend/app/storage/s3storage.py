
from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.core.config import settings
from app.storage.base import StorageBase

import boto3


class S3Storage(StorageBase):

    def __init__(self):
        self.client = boto3.client( "s3", region_name=settings.AWS_REGION,)
        self.bucket = settings.S3_BUCKET_NAME

    def upload(self, key: str,data: bytes,content_type: str = "application/octet-stream") -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            ServerSideEncryption="AES256",
        )

    def download(self, key: str) -> bytes:
        try:
            response = self.client.get_object(Bucket=self.bucket,Key=key,)
            return response["Body"].read()

        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]

            if error_code in ("404", "NoSuchKey", "NotFound"):
                raise HTTPException(
                    status_code=404,
                    detail="File missing from storage",
                )

            raise

    def delete(self, key: str) -> None:
        self.client.delete_object(
            Bucket=self.bucket,
            Key=key,
        )

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(
                Bucket=self.bucket,
                Key=key,
            )
            return True

        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]

            if error_code in ("404", "NoSuchKey", "NotFound"):
                return False

            raise


storage = S3Storage()
