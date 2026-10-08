"""Abstract Storage Service compatible with Local Filesystem and S3 / MinIO.

Provides unified interface for document persistence across all storage targets.
"""

import io
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

from django.conf import settings

logger = logging.getLogger(__name__)


class BaseStorageService(ABC):
    """Abstract interface defining required storage operations."""

    @abstractmethod
    def save_file(
        self,
        storage_key: str,
        content: BinaryIO | bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Save file content to the target storage.

        Args:
            storage_key: Unique identifier/path for the file.
            content: File-like binary object or bytes.
            content_type: MIME type of the file.

        Returns:
            The normalized storage_key.
        """
        pass

    @abstractmethod
    def get_file(self, storage_key: str) -> io.BytesIO:
        """Retrieve file content as a binary stream."""
        pass

    @abstractmethod
    def delete_file(self, storage_key: str) -> bool:
        """Delete file at storage_key.

        Returns True if deleted or did not exist.
        """
        pass

    @abstractmethod
    def file_exists(self, storage_key: str) -> bool:
        """Check whether a file exists at storage_key."""
        pass

    @abstractmethod
    def get_url(self, storage_key: str, expires_in: int = 3600) -> str:
        """Retrieve a downloadable URL or presigned URL for the storage key."""
        pass


class LocalStorageService(BaseStorageService):
    """Local filesystem storage using Django MEDIA_ROOT."""

    def __init__(self, base_dir: Path | str | None = None):
        self._custom_base_dir = Path(base_dir) if base_dir else None

    @property
    def base_dir(self) -> Path:
        base = self._custom_base_dir or Path(settings.MEDIA_ROOT)
        base.mkdir(parents=True, exist_ok=True)
        return base

    def _get_path(self, storage_key: str) -> Path:
        # Strip leading slashes to prevent root traversal
        clean_key = storage_key.lstrip("/\\")
        path = (self.base_dir / clean_key).resolve()
        # Security check: ensure path stays within base_dir
        if not path.is_relative_to(self.base_dir.resolve()):
            raise ValueError(f"Path traversal detected: {storage_key}")
        return path

    def save_file(
        self,
        storage_key: str,
        content: BinaryIO | bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        dest_path = self._get_path(storage_key)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, (bytes, bytearray)):
            dest_path.write_bytes(content)
        else:
            with open(dest_path, "wb") as f:
                if hasattr(content, "chunks"):
                    for chunk in content.chunks():
                        f.write(chunk)
                elif hasattr(content, "read"):
                    f.write(content.read())
                else:
                    raise TypeError("Unsupported content type for file save")

        logger.info(f"Saved file to local storage: {dest_path}")
        return storage_key

    def get_file(self, storage_key: str) -> io.BytesIO:
        path = self._get_path(storage_key)
        if not path.is_file():
            raise FileNotFoundError(f"File not found in local storage: {storage_key}")
        return io.BytesIO(path.read_bytes())

    def delete_file(self, storage_key: str) -> bool:
        try:
            path = self._get_path(storage_key)
            if path.is_file():
                path.unlink()
                logger.info(f"Deleted local file: {path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file {storage_key}: {e}")
            return False

    def file_exists(self, storage_key: str) -> bool:
        try:
            path = self._get_path(storage_key)
            return path.is_file()
        except ValueError:
            return False

    def get_url(self, storage_key: str, expires_in: int = 3600) -> str:
        clean_key = storage_key.lstrip("/\\")
        media_url = getattr(settings, "MEDIA_URL", "/media/")
        if not media_url.endswith("/"):
            media_url += "/"
        return f"{media_url}{clean_key}"


class S3StorageService(BaseStorageService):
    """S3 and MinIO compatible object storage implementation."""

    def __init__(
        self,
        bucket_name: str | None = None,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region_name: str | None = None,
    ):
        try:
            import boto3
            from botocore.client import Config
        except ImportError:
            raise ImportError(
                "boto3 package is required for S3StorageService. Run 'pip install boto3'."
            )

        self.bucket_name = bucket_name or getattr(
            settings, "AWS_STORAGE_BUCKET_NAME", "amanus-documents"
        )
        self.endpoint_url = endpoint_url or getattr(settings, "AWS_S3_ENDPOINT_URL", None)
        self.access_key = access_key or getattr(settings, "AWS_ACCESS_KEY_ID", "")
        self.secret_key = secret_key or getattr(settings, "AWS_SECRET_ACCESS_KEY", "")
        self.region_name = region_name or getattr(settings, "AWS_S3_REGION_NAME", "us-east-1")

        session = boto3.session.Session()
        self.s3_client = session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region_name,
            config=Config(signature_version="s3v4"),
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        try:
            from botocore.exceptions import ClientError

            try:
                self.s3_client.head_bucket(Bucket=self.bucket_name)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code")
                if error_code in ("404", "NoSuchBucket"):
                    logger.info(f"Creating S3 bucket: {self.bucket_name}")
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
        except Exception as e:
            logger.warning(f"Could not verify or create S3 bucket {self.bucket_name}: {e}")

    def save_file(
        self,
        storage_key: str,
        content: BinaryIO | bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        extra_args = {"ContentType": content_type}

        if isinstance(content, (bytes, bytearray)):
            file_obj = io.BytesIO(content)
        elif hasattr(content, "read"):
            if hasattr(content, "seek"):
                content.seek(0)
            file_obj = content
        else:
            raise TypeError("Unsupported content format for S3 upload")

        self.s3_client.upload_fileobj(
            file_obj,
            self.bucket_name,
            storage_key,
            ExtraArgs=extra_args,
        )
        logger.info(f"Uploaded file to S3 ({self.bucket_name}): {storage_key}")
        return storage_key

    def get_file(self, storage_key: str) -> io.BytesIO:
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=storage_key)
        body = response["Body"].read()
        return io.BytesIO(body)

    def delete_file(self, storage_key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=storage_key)
            logger.info(f"Deleted S3 object: {storage_key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting S3 object {storage_key}: {e}")
            return False

    def file_exists(self, storage_key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=storage_key)
            return True
        except ClientError:
            return False

    def get_url(self, storage_key: str, expires_in: int = 3600) -> str:
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": storage_key},
                ExpiresIn=expires_in,
            )
            return url
        except Exception as e:
            logger.warning(f"Failed to generate presigned S3 URL for {storage_key}: {e}")
            return f"{self.endpoint_url or ''}/{self.bucket_name}/{storage_key}"


_storage_instance: BaseStorageService | None = None


def get_storage_service() -> BaseStorageService:
    """Storage factory returning the configured storage backend."""
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    backend = getattr(settings, "STORAGE_BACKEND", "local")

    if backend == "s3":
        try:
            _storage_instance = S3StorageService()
            return _storage_instance
        except Exception as e:
            logger.warning(
                f"S3 storage initialization failed ({e}), falling back to LocalStorageService."
            )

    _storage_instance = LocalStorageService()
    return _storage_instance


def reset_storage_service() -> None:
    """Helper for testing to reset cached storage instance."""
    global _storage_instance
    _storage_instance = None
