"""Pure helpers for bounded image decoding and owned storage keys."""
from __future__ import annotations
import io
import re
from pathlib import Path
from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 20_000_000
MAX_OUTPUT_BYTES = 2 * 1024 * 1024
IDENT = re.compile(r"^[0-9a-f]{32}$")
PREFIX = "/api/media/profile-photos/"


def owned_path(root: Path, url: str | None) -> Path | None:
    if not url or not url.startswith(PREFIX) or not url.endswith('.webp'):
        return None
    ident = url[len(PREFIX):-5]
    if not IDENT.fullmatch(ident):
        return None
    return root / (ident + '.webp')


def process_photo(raw: bytes, declared_type: str | None) -> bytes:
    if declared_type not in ('image/jpeg', 'image/png', 'image/webp'):
        raise HTTPException(415, 'Only JPEG, PNG or WebP supported')
    if len(raw) > MAX_BYTES:
        raise HTTPException(413, 'Image exceeds 5 MB')
    if not raw:
        raise HTTPException(400, 'Empty image')
    # Keep Pillow's decompression-bomb checks scoped to this request via explicit
    # dimensions rather than mutating Image.MAX_IMAGE_PIXELS globally.
    try:
        with Image.open(io.BytesIO(raw)) as im:
            if im.format not in ('JPEG', 'PNG', 'WEBP'):
                raise HTTPException(415, 'Unsupported image format')
            mime = {'JPEG':'image/jpeg', 'PNG':'image/png', 'WEBP':'image/webp'}[im.format]
            if declared_type != mime:
                raise HTTPException(415, 'Image MIME does not match file content')
            if im.width * im.height > MAX_PIXELS:
                raise HTTPException(413, 'Image dimensions exceed limit')
            im.verify()
        with Image.open(io.BytesIO(raw)) as im:
            im = ImageOps.exif_transpose(im)
            im.load()
            if im.width * im.height > MAX_PIXELS:
                raise HTTPException(413, 'Image dimensions exceed limit')
            result = ImageOps.fit(im.convert('RGB'), (512, 512), method=Image.Resampling.LANCZOS)
            with io.BytesIO() as buf:
                result.save(buf, format='WEBP', quality=82, method=5)
                data = buf.getvalue()
            if len(data) > MAX_OUTPUT_BYTES:
                raise HTTPException(413, 'Processed photo exceeds storage limit')
            return data
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise HTTPException(400, 'Invalid or damaged image') from exc
