"""Safe upload handling: streamed size caps + magic-byte content validation.

The previous handlers did `await file.read()` with no size limit (OOM/DoS risk)
and trusted client-supplied content types. These helpers read with a hard cap
and verify the real file type from its leading bytes.
"""
from __future__ import annotations

from fastapi import HTTPException, UploadFile, status

_CHUNK = 64 * 1024


async def read_capped(file: UploadFile, max_bytes: int) -> bytes:
    """Read an UploadFile fully but refuse anything over max_bytes (HTTP 413).

    Resets the file cursor afterwards so the stream can be re-read.
    """
    buf = bytearray()
    while True:
        chunk = await file.read(_CHUNK)
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds the maximum allowed size of {max_bytes // (1024 * 1024)} MB.",
            )
    if not buf:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file.")
    try:
        await file.seek(0)
    except Exception:
        pass
    return bytes(buf)


def is_pdf(data: bytes) -> bool:
    return data[:5] == b"%PDF-"


def is_image(data: bytes) -> bool:
    return (
        data[:3] == b"\xff\xd8\xff"  # JPEG
        or data[:8] == b"\x89PNG\r\n\x1a\n"  # PNG
        or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")  # WEBP
        or data[:6] in (b"GIF87a", b"GIF89a")  # GIF
    )


def is_audio(data: bytes) -> bool:
    return (
        data[:4] == b"\x1aE\xdf\xa3"  # EBML (webm / matroska — what MediaRecorder emits)
        or data[:4] == b"OggS"  # OGG
        or (data[:4] == b"RIFF" and data[8:12] == b"WAVE")  # WAV
        or data[:3] == b"ID3"  # MP3 w/ id3
        or data[:2] == b"\xff\xfb"  # MP3 frame
        or data[4:8] == b"ftyp"  # MP4/M4A
    )


def ensure_pdf(data: bytes) -> None:
    if not is_pdf(data):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is not a valid PDF.")


def ensure_image(data: bytes) -> None:
    if not is_image(data):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is not a valid image.")


def ensure_audio(data: bytes) -> None:
    if not is_audio(data):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is not a recognized audio format.")
