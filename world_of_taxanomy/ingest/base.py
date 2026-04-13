"""Base ingestion utilities - download helper and common functions."""

from __future__ import annotations

import io
import urllib.request
import ssl
import zipfile
from pathlib import Path
from typing import Optional


def ensure_data_file(url: str, local_path: Path, headers: Optional[dict] = None) -> Path:
    """Download file from URL if not already on disk.

    Uses urllib.request (stdlib) - no requests dependency needed.
    Optional headers dict is merged with the default User-Agent header.
    Returns the local path.
    """
    local_path = Path(local_path)
    if local_path.exists():
        print(f"  Using cached: {local_path}")
        return local_path

    local_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading: {url}")
    print(f"  To: {local_path}")

    # Create SSL context that doesn't verify (some gov sites have cert issues)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    request_headers = {"User-Agent": "WorldOfTaxanomy/0.1"}
    if headers:
        request_headers.update(headers)

    req = urllib.request.Request(url, headers=request_headers)
    with urllib.request.urlopen(req, context=ctx) as response:
        data = response.read()
        local_path.write_bytes(data)

    size_kb = len(data) / 1024
    print(f"  Downloaded: {size_kb:.1f} KB")
    return local_path


def ensure_data_file_zip(url: str, local_path: Path, member: str) -> Path:
    """Download a ZIP from URL, extract one member file, and cache it locally.

    If local_path already exists, skip download (cached).
    Returns the local path of the extracted file.

    Args:
        url: URL of the ZIP archive.
        local_path: Where to save the extracted member file.
        member: Name of the file inside the ZIP to extract.
    """
    local_path = Path(local_path)
    if local_path.exists():
        print(f"  Using cached: {local_path}")
        return local_path

    local_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading ZIP: {url}")
    print(f"  Extracting member: {member}")
    print(f"  To: {local_path}")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers={"User-Agent": "WorldOfTaxanomy/0.1"})
    with urllib.request.urlopen(req, context=ctx) as response:
        zip_bytes = response.read()

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        data = zf.read(member)
        local_path.write_bytes(data)

    size_kb = len(data) / 1024
    print(f"  Extracted: {size_kb:.1f} KB")
    return local_path
