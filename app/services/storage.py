try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    boto3 = None

from typing import BinaryIO, Optional
from app.core.config import settings
import uuid


class StorageService:
    """Service for file storage (AWS S3 or compatible)."""

    def __init__(self):
        if HAS_BOTO3 and hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )
            self.bucket_name = settings.S3_BUCKET_NAME
        else:
            self.s3_client = None
            self.bucket_name = None

    async def upload_file(
        self,
        file: BinaryIO,
        file_name: str,
        content_type: Optional[str] = None,
        folder: str = "uploads",
    ) -> str:
        """
        Upload file to S3 and return public URL.

        Args:
            file: File object
            file_name: Original filename
            content_type: MIME type
            folder: S3 folder/prefix

        Returns:
            Public URL of uploaded file
        """

        if not self.s3_client:
            raise Exception("S3 storage not configured")

        # Generate unique filename
        file_extension = file_name.split(".")[-1]
        unique_filename = f"{folder}/{uuid.uuid4()}.{file_extension}"

        try:
            # Upload to S3
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                unique_filename,
                ExtraArgs={
                    "ContentType": content_type or "application/octet-stream",
                    "ACL": "public-read",
                },
            )

            # Return public URL
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{unique_filename}"
            return url

        except Exception as e:
            raise Exception(f"File upload failed: {str(e)}")

    def get_file_url(self, key: str) -> str:
        """Get public URL for a file."""
        return f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"

    async def delete_file(self, key: str) -> bool:
        """Delete file from S3."""
        if not self.s3_client:
            return False

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False


# Singleton instance
storage_service = StorageService()
