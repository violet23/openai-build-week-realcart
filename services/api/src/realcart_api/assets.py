"""Private local image cache used by live connectors and generated portraits."""

from __future__ import annotations

import base64
import hashlib
import ipaddress
import socket
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import httpx

from realcart_api.schemas import ImageAsset
from realcart_api.settings import settings

_CONTENT_EXTENSIONS = {
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
_EXTENSION_CONTENT = {value: key for key, value in _CONTENT_EXTENSIONS.items()}
_MAX_IMAGE_BYTES = 8 * 1024 * 1024
ImageSource = Literal["fixture", "gmail", "pinterest", "generated"]


class ImageAssetError(RuntimeError):
    """Raised when a remote or generated image cannot be stored safely."""


class AssetStore:
    def __init__(self, root: Path | None = None, public_base_url: str | None = None) -> None:
        self.root = root or settings.asset_dir
        self.public_base_url = (public_base_url or settings.api_public_base_url).rstrip("/")
        self.root.mkdir(parents=True, exist_ok=True)

    def store_bytes(
        self,
        data: bytes,
        *,
        source: ImageSource,
        alt_text: str,
        mime_type: str,
    ) -> ImageAsset:
        normalized_type = mime_type.split(";", 1)[0].strip().lower()
        extension = _CONTENT_EXTENSIONS.get(normalized_type)
        if extension is None:
            raise ImageAssetError(f"Unsupported image type: {normalized_type}")
        if not data or len(data) > _MAX_IMAGE_BYTES:
            raise ImageAssetError("Image is empty or exceeds the 8 MB RealCart limit")
        asset_id = hashlib.sha256(data).hexdigest()[:24]
        path = self.root / f"{asset_id}{extension}"
        if not path.exists():
            path.write_bytes(data)
        return ImageAsset(
            id=asset_id,
            source=source,
            image_url=f"{self.public_base_url}/api/assets/{asset_id}",
            alt_text=alt_text.strip() or "Imported product image",
            mime_type=normalized_type,
        )

    def cache_remote_image(
        self,
        url: str,
        *,
        source: ImageSource,
        alt_text: str,
        client: httpx.Client | None = None,
    ) -> ImageAsset:
        _validate_public_https_url(url)
        owns_client = client is None
        active_client = client or httpx.Client(follow_redirects=True, timeout=10)
        try:
            with active_client.stream("GET", url) as response:
                response.raise_for_status()
                _validate_public_https_url(str(response.url))
                mime_type = response.headers.get("content-type", "").split(";", 1)[0]
                if mime_type not in _CONTENT_EXTENSIONS:
                    raise ImageAssetError("Remote URL did not return a supported image")
                chunks: list[bytes] = []
                byte_count = 0
                for chunk in response.iter_bytes():
                    byte_count += len(chunk)
                    if byte_count > _MAX_IMAGE_BYTES:
                        raise ImageAssetError("Remote image exceeds the 8 MB limit")
                    chunks.append(chunk)
        except (httpx.HTTPError, OSError) as error:
            raise ImageAssetError("Unable to cache remote image") from error
        finally:
            if owns_client:
                active_client.close()
        return self.store_bytes(
            b"".join(chunks),
            source=source,
            alt_text=alt_text,
            mime_type=mime_type,
        )

    def path_for(self, asset_id: str) -> Path | None:
        if not asset_id or any(character not in "0123456789abcdef" for character in asset_id):
            return None
        matches = list(self.root.glob(f"{asset_id}.*"))
        return matches[0] if len(matches) == 1 else None

    def data_url_for(self, asset: ImageAsset) -> str:
        path = self.path_for(asset.id)
        if path is None:
            raise ImageAssetError(f"Unknown image asset: {asset.id}")
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{asset.mime_type};base64,{encoded}"

    def mime_type_for(self, path: Path) -> str:
        return _EXTENSION_CONTENT.get(path.suffix.lower(), "application/octet-stream")


def _validate_public_https_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ImageAssetError("Only public HTTPS image URLs are accepted")
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM
            )
        }
    except OSError as error:
        raise ImageAssetError("Image hostname could not be resolved") from error
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ImageAssetError("Private or local image hosts are not accepted")


asset_store = AssetStore()
