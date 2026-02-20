from azure.storage.blob import ContentSettings
from azure.storage.blob.aio import BlobServiceClient

from src.application.services.blob_storage_service_base import BlobStorageServiceBase
from src.config.settings import Settings


class BlobStorageService(BlobStorageServiceBase):
    """Azure Blob Storage implementation of BlobStorageServiceBase.

    To switch providers (e.g. AWS S3), create a new class that implements
    BlobStorageServiceBase and update the binding in container.py.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the Azure Blob Storage client.

        Args:
            settings: Application settings containing the storage connection string.
        """
        self._client = BlobServiceClient.from_connection_string(settings.blob_storage_connection_string)

    async def upload(
        self,
        container_name: str,
        blob_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        async with self._client.get_blob_client(container=container_name, blob=blob_name) as blob_client:
            await blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type),
            )
            return blob_client.url

    async def download(self, container_name: str, blob_name: str) -> bytes:
        async with self._client.get_blob_client(container=container_name, blob=blob_name) as blob_client:
            stream = await blob_client.download_blob()
            return await stream.readall()

    async def delete(self, container_name: str, blob_name: str) -> bool:
        async with self._client.get_blob_client(container=container_name, blob=blob_name) as blob_client:
            if not await blob_client.exists():
                return False
            await blob_client.delete_blob()
            return True

    async def exists(self, container_name: str, blob_name: str) -> bool:
        async with self._client.get_blob_client(container=container_name, blob=blob_name) as blob_client:
            return await blob_client.exists()

    async def close(self) -> None:
        await self._client.close()
