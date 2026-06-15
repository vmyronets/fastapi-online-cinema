"""
Async S3 storage client implementation.

Uses aioboto3 to interact with S3-compatible storage (MinIO/AWS S3).
Implements the S3StorageInterface for uploading files and generating
pre-signed URLs for file access.
"""

from io import BytesIO

import aioboto3

from src.config.settings import settings
from src.security.interfaces import S3StorageInterface
from src.security.exceptions import S3FileUploadError


class S3StorageClient(S3StorageInterface):
    """
    Async S3 storage client using aioboto3.

    Connects to an S3-compatible service (MinIO in development,
    AWS S3 in production) and provides file upload and URL
    generation capabilities.

    Attributes:
        endpoint_url: The S3 service endpoint URL.
        access_key: The S3 access key for authentication.
        secret_key: The S3 secret key for authentication.
        bucket_name: The target S3 bucket name.
    """

    def __init__(self) -> None:
        """Initialize S3 client with settings from application config."""
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self.access_key = settings.S3_ACCESS_KEY
        self.secret_key = settings.S3_SECRET_KEY
        self.bucket_name = settings.S3_BUCKET_NAME

    def _get_session(self) -> aioboto3.Session:
        """
        Create a new aioboto3 session.

        Returns:
            aioboto3.Session: A configured aioboto3 session.
        """
        return aioboto3.Session(
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        )

    async def upload_file(self, file_name: str, file_data: bytes) -> None:
        """
        Upload a file to the configured S3 bucket.

        Steps:
        - Create an aioboto3 session and S3 client.
        - Upload the file bytes to the specified key in the bucket.

        Args:
            file_name: The key/path for the file in the bucket.
            file_data: The raw file bytes to upload.

        Raises:
            S3FileUploadError: If the upload fails for any reason.
        """
        session = self._get_session()
        try:
            async with session.client("s3", endpoint_url=self.endpoint_url) as s3:
                await s3.upload_fileobj(
                    BytesIO(file_data),
                    self.bucket_name,
                    file_name,
                )
        except Exception as e:
            raise S3FileUploadError(f"Failed to upload file '{file_name}': {e}")

    async def get_file_url(self, file_name: str) -> str:
        """
        Generate a pre-signed URL for accessing a file in S3.

        The URL is valid for 1 hour (3600 seconds) by default.

        Args:
            file_name: The key/path of the file in the bucket.

        Returns:
            str: A pre-signed URL for downloading/viewing the file.
        """
        session = self._get_session()
        async with session.client("s3", endpoint_url=self.endpoint_url) as s3:
            url = await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": file_name},
                ExpiresIn=3600,
            )
        return url
