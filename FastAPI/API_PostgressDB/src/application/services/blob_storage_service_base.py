from abc import ABC, abstractmethod


class BlobStorageServiceBase(ABC):
    """Abstract base class for blob storage operations.

    Implement this interface with a provider-specific class (e.g. Azure, S3) and
    bind it in the DI container. Use cases depend only on this interface, so
    switching providers requires no changes outside the infrastructure layer.
    """

    @abstractmethod
    async def upload(
        self,
        container_name: str,
        blob_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload raw bytes to blob storage.

        Args:
            container_name: The storage container or bucket name.
            blob_name: The path/name of the blob within the container.
            data: The raw bytes to upload.
            content_type: The MIME type of the content.

        Returns:
            The public URL of the uploaded blob.
        """

    @abstractmethod
    async def download(self, container_name: str, blob_name: str) -> bytes:
        """Download a blob and return its raw bytes.

        Args:
            container_name: The storage container or bucket name.
            blob_name: The path/name of the blob within the container.

        Returns:
            The raw bytes of the blob.
        """

    @abstractmethod
    async def delete(self, container_name: str, blob_name: str) -> bool:
        """Delete a blob.

        Args:
            container_name: The storage container or bucket name.
            blob_name: The path/name of the blob within the container.

        Returns:
            True if the blob was deleted, False if it did not exist.
        """

    @abstractmethod
    async def exists(self, container_name: str, blob_name: str) -> bool:
        """Check whether a blob exists.

        Args:
            container_name: The storage container or bucket name.
            blob_name: The path/name of the blob within the container.

        Returns:
            True if the blob exists, False otherwise.
        """
