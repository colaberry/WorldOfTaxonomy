"""SHA-256 file hashing utility for data provenance audit trail."""
from __future__ import annotations

import hashlib


def sha256_of_file(path: str) -> str:
    """Compute SHA-256 hex digest of a file, reading in 8 KiB chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
