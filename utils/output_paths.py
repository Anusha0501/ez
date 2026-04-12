"""Helpers for validating generated artifacts."""

import os
from typing import Optional


def pptx_output_valid(path: Optional[str]) -> bool:
    """True if path exists, is a file, and has non-zero size (real PPTX write)."""
    if not path:
        return False
    try:
        return os.path.isfile(path) and os.path.getsize(path) > 0
    except OSError:
        return False
