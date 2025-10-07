import cloudinary
import cloudinary.uploader
import asyncio
from ..core.config import settings

cloudinary.config(
    cloud_name=settings.cloudinary_cloud_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret,
)


async def upload_image(file_path: str, folder: str = "articles") -> str:
    """Upload an image to Cloudinary and return the secure URL."""
    result = await asyncio.to_thread(
        cloudinary.uploader.upload, file_path, folder=folder
    )
    return result["secure_url"]


async def delete_image(public_id: str) -> None:
    """Delete an image from Cloudinary by public_id."""
    await asyncio.to_thread(cloudinary.uploader.destroy, public_id)
