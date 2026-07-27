"""Output file organizer for Hermes Image Studio.

Downloads generated images from FAL URLs, writes them to dated folders
with descriptive filenames, and tracks paths for history recording.
"""

from __future__ import annotations

import os
import re
import time
import urllib.request
from datetime import datetime, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# Default output root
# ---------------------------------------------------------------------------

DEFAULT_OUTPUT_ROOT = os.environ.get(
    "HERMES_IMAGE_STUDIO_OUTPUT",
    os.path.expanduser("/Volumes/Spare Drive/Personal Stuff/Image Studio"),
)


def _ensure_output_root(root: Optional[str] = None) -> str:
    path = root or DEFAULT_OUTPUT_ROOT
    os.makedirs(path, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Smart filename generation
# ---------------------------------------------------------------------------

_MAX_FILENAME_LEN = 120
_TRUNCATE_SUBJECT = 60


def _sanitize(text: str) -> str:
    """Strip characters that are problematic in filenames."""
    # Replace spaces with hyphens, remove everything that's not alphanumeric
    s = re.sub(r"[^\w\s-]", "", text).strip().lower()
    s = re.sub(r"[-\s]+", "-", s)
    return s


def _extract_keywords(prompt: str, max_chars: int = 60) -> str:
    """Extract the first meaningful words from a prompt for a short subject."""
    # Take first ~60 chars of the prompt, preferring word boundaries
    cleaned = re.sub(r"[^\w\s]", " ", prompt).strip()
    words = cleaned.split()
    subject = ""
    for word in words:
        if len(subject) + len(word) + 1 > max_chars:
            break
        if subject:
            subject += "-"
        subject += word.lower()
    return subject if subject else "untitled"


def build_filename(
    prompt: str,
    *,
    preset: Optional[str] = None,
    seed: int = -1,
    suffix: str = "",
    ext: str = ".png",
) -> str:
    """Build a descriptive, timestamped filename.

    Pattern: YYYYMMDD_HHMMSS_preset_seed_subject[suffix].ext
    Example: 20260726_103042_cinematic_472444619_cowboys-at-sunrise.png
    """
    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    subject = _extract_keywords(prompt, _TRUNCATE_SUBJECT)
    parts = [now]
    if preset:
        parts.append(_sanitize(preset))
    if seed >= 0:
        parts.append(str(seed))
    parts.append(subject)
    if suffix:
        parts.append(_sanitize(suffix))
    filename = "-".join(parts)[:_MAX_FILENAME_LEN] + ext
    return filename


# ---------------------------------------------------------------------------
# Download + save
# ---------------------------------------------------------------------------


def save_generated_image(
    image_url: str,
    prompt: str,
    *,
    preset: Optional[str] = None,
    seed: int = -1,
    output_root: Optional[str] = None,
    subfolder: str = "",
) -> str:
    """Download a generated image from a FAL URL and save it locally.

    Args:
        image_url: Public URL of the image (from FAL response).
        prompt: Original prompt used (for filename generation).
        preset: Style preset name (included in filename).
        seed: Generation seed (included in filename).
        output_root: Base directory. Defaults to Spare Drive / Image Studio.
        subfolder: Optional subfolder (e.g. "batch", "caturday").

    Returns:
        Absolute path to the saved file.
    """
    root = _ensure_output_root(output_root)
    if subfolder:
        root = os.path.join(root, subfolder)
        os.makedirs(root, exist_ok=True)

    filename = build_filename(prompt, preset=preset, seed=seed)
    filepath = os.path.join(root, filename)

    # Download with a user-agent to avoid any CDN blocks
    req = urllib.request.Request(
        image_url,
        headers={"User-Agent": "Hermes-ImageStudio/1.0"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()

    with open(filepath, "wb") as f:
        f.write(data)

    return filepath


def save_upscaled_image(
    image_url: str,
    source_filename: str,
    *,
    output_root: Optional[str] = None,
) -> str:
    """Download an upscaled image and save it alongside the original.

    Appends '_HD' to the source filename base.
    """
    root = _ensure_output_root(output_root)

    base, ext = os.path.splitext(source_filename)
    hd_filename = f"{base}_HD{ext}"
    filepath = os.path.join(root, hd_filename)

    req = urllib.request.Request(
        image_url,
        headers={"User-Agent": "Hermes-ImageStudio/1.0"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()

    with open(filepath, "wb") as f:
        f.write(data)

    return filepath
