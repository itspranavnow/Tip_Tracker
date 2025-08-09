from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from typing import Optional

import pandas as pd
import qrcode

from utils import QRCODES_DIR


def generate_qr_png(data: str, filename: Path) -> Path:
    """Generate a QR code PNG file and return its path."""
    img = qrcode.make(data)
    filename.parent.mkdir(parents=True, exist_ok=True)
    img.save(filename)
    return filename


def img_to_bytes(img_path: Path) -> bytes:
    return img_path.read_bytes()


def img_bytes_to_base64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def ensure_waiter_qr(app_base_url: str, waiter_id: str) -> Path:
    """Ensure a QR exists for a waiter, generate if missing."""
    target = QRCODES_DIR / f"{waiter_id}.png"
    if not target.exists():
        url = f"{app_base_url}?waiter_id={waiter_id}"
        generate_qr_png(url, target)
    return target


__all__ = [
    "generate_qr_png",
    "img_to_bytes",
    "img_bytes_to_base64",
    "ensure_waiter_qr",
]


