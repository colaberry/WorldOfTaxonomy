"""Base ingestion utilities - download helper and common functions."""

import urllib.request
import ssl
from pathlib import Path


def ensure_data_file(url: str, local_path: Path) -> Path:
    """Download file from URL if not already on disk.

    Uses urllib.request (stdlib) - no requests dependency needed.
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

    req = urllib.request.Request(url, headers={"User-Agent": "WorldOfTaxanomy/0.1"})
    with urllib.request.urlopen(req, context=ctx) as response:
        data = response.read()
        local_path.write_bytes(data)

    size_kb = len(data) / 1024
    print(f"  Downloaded: {size_kb:.1f} KB")
    return local_path
