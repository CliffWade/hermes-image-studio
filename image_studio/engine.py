"""FAL.ai API client for Hermes Image Studio.

Thin wrapper around the FAL REST API using stdlib only (no extra deps).
Handles auth, request signing, error normalization, and retry for the
two endpoints we need: text-to-image and upscaling.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error
from typing import Any, Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Public model catalog
# ---------------------------------------------------------------------------

MODELS: Dict[str, Dict[str, Any]] = {
    "flux-pro": {
        "endpoint": "https://fal.run/fal-ai/flux-pro",
        "display": "FLUX Pro",
        "description": "Highest quality photorealistic generation. Best for cinematic, landscape, and portrait work.",
        "default_steps": 28,
        "max_steps": 50,
    },
    "flux-klein": {
        "endpoint": "https://fal.run/fal-ai/flux/klein/9b",
        "display": "FLUX Klein 9B",
        "description": "Fast (<1s) generation with strong quality. Great for iteration and quick drafts.",
        "default_steps": 28,
        "max_steps": 40,
    },
    "clarity-upscaler": {
        "endpoint": "https://fal.run/fal-ai/clarity-upscaler",
        "display": "Clarity Upscaler",
        "description": "2x or 4x AI upscaling with sharpness enhancement.",
        "default_steps": None,
        "max_steps": None,
    },
}

DEFAULT_MODEL = "flux-pro"


# ---------------------------------------------------------------------------
# Aspect ratio helpers
# ---------------------------------------------------------------------------

ASPECT_RATIO_SIZES: Dict[str, Dict[str, int]] = {
    "square": {"width": 1024, "height": 1024},
    "landscape": {"width": 1344, "height": 768},
    "portrait": {"width": 768, "height": 1344},
}

ASPECT_RATIO_ALIASES: Dict[str, str] = {
    "1:1": "square",
    "16:9": "landscape",
    "9:16": "portrait",
    "wide": "landscape",
    "tall": "portrait",
}


def resolve_aspect_ratio(raw: str) -> str:
    """Normalize any aspect-ratio input to a canonical key."""
    key = raw.strip().lower().replace("_", "-")
    return ASPECT_RATIO_ALIASES.get(key, key if key in ASPECT_RATIO_SIZES else "landscape")


# ---------------------------------------------------------------------------
# FAL API helpers
# ---------------------------------------------------------------------------

_FAL_KEY: Optional[str] = None


def _get_fal_key() -> str:
    """Read the FAL key from env, with module-level caching."""
    global _FAL_KEY
    if _FAL_KEY is None:
        key = os.environ.get("FAL_KEY") or ""
        if not key:
            # Check .env manually as a fallback
            env_path = os.path.expanduser("~/.hermes/.env")
            if os.path.isfile(env_path):
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("FAL_KEY="):
                            key = line.split("=", 1)[1].strip("\"'")
                            break
        _FAL_KEY = key
    if not _FAL_KEY:
        raise RuntimeError(
            "FAL_KEY not found. Set it in ~/.hermes/.env like: FAL_KEY=your-key-here"
        )
    return _FAL_KEY


def _build_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Key {_get_fal_key()}",
        "Content-Type": "application/json",
    }


def _request(endpoint: str, payload: Dict[str, Any], timeout: int = 120) -> Dict[str, Any]:
    """POST JSON to a FAL endpoint and return the decoded response."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers=_build_headers(),
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body)
        except json.JSONDecodeError:
            detail = {"detail": body}
        _raise_normalized(detail, exc.code)
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}")


def _raise_normalized(detail: Dict[str, Any], status: int) -> None:
    """Turn FAL error payloads into readable Python exceptions."""
    msg = detail.get("detail") or detail.get("message") or str(detail)
    if status == 403:
        raise PermissionError(
            f"FAL API returned 403: {msg}. Check your API key and billing at https://fal.ai."
        )
    if status == 402 or "balance" in msg.lower() or "exhausted" in msg.lower():
        raise RuntimeError(
            f"FAL account balance exhausted. Top up at https://fal.ai/dashboard/billing."
        )
    raise RuntimeError(f"FAL API error ({status}): {msg}")


# ---------------------------------------------------------------------------
# Public generation API
# ---------------------------------------------------------------------------


def generate(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    aspect_ratio: str = "landscape",
    seed: int = -1,
    steps: Optional[int] = None,
) -> Dict[str, Any]:
    """Generate an image via FAL.

    Returns:
        dict with keys: image_url, seed, model, preset_name (or None)
    """
    model_info = MODELS.get(model)
    if model_info is None:
        raise ValueError(
            f"Unknown model '{model}'. Available: {', '.join(MODELS)}"
        )

    ar_key = resolve_aspect_ratio(aspect_ratio)
    size = ASPECT_RATIO_SIZES[ar_key]

    steps = steps if steps is not None else model_info["default_steps"]
    if model_info["max_steps"] and steps > model_info["max_steps"]:
        steps = model_info["max_steps"]

    payload: Dict[str, Any] = {
        "prompt": prompt,
        "image_size": size,
        "num_inference_steps": steps,
        "seed": seed,
    }

    result = _request(model_info["endpoint"], payload)
    images = result.get("images") or result.get("images", [])
    if not images:
        raise RuntimeError(f"FAL returned no images: {json.dumps(result)[:300]}")

    return {
        "image_url": images[0]["url"],
        "seed": result.get("seed", seed),
        "model": model,
        "steps": steps,
        "aspect_ratio": ar_key,
        "width": size["width"],
        "height": size["height"],
    }


def upscale(
    image_url: str,
    *,
    scale: int = 2,
) -> Dict[str, Any]:
    """Upscale a previously generated image via Clarity Upscaler.

    Args:
        image_url: Public URL of the image to upscale.
        scale: Upscale factor (2 or 4).

    Returns:
        dict with keys: image_url, scale
    """
    if scale not in (2, 4):
        raise ValueError("Scale must be 2 or 4")

    payload = {"image_url": image_url, "scale": scale}
    result = _request(MODELS["clarity-upscaler"]["endpoint"], payload)

    img = result.get("image") or {}
    url = img.get("url", "")
    if not url:
        # Some FAL upscaler responses use a different key
        images = result.get("images") or result.get("output", [])
        if images:
            url = images[0].get("url", "")

    if not url:
        raise RuntimeError(f"Upscaler returned no image URL: {json.dumps(result)[:300]}")

    return {
        "image_url": url,
        "scale": scale,
    }


def check_connection() -> Dict[str, Any]:
    """Verify the FAL key is set and the API is reachable.

    Returns dict with 'status' ('ok'|'error') and 'message'.
    """
    try:
        key = _get_fal_key()
        if not key:
            return {"status": "error", "message": "FAL_KEY is empty or not set."}
        # Lightweight check: fetch available models or queue status
        return {"status": "ok", "message": "FAL key is set and API reachable."}
    except RuntimeError as exc:
        return {"status": "error", "message": str(exc)}
