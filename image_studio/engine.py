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
        "size_format": "object",
        "price": 0.03,
        "supports_negative": True,
    },
    "flux-klein": {
        "endpoint": "https://fal.run/fal-ai/flux-2/klein/9b",
        "display": "FLUX 2 Klein 9B",
        "description": "Fast (<1s) generation with strong quality from FLUX 2. Great for iteration and quick drafts.",
        "default_steps": 4,
        "max_steps": 8,
        "size_format": "image_size_preset",
        "price": 0.006,
        "supports_negative": True,
        "extra_params": {"output_format": "png"},
    },
    "flux-klein-v1": {
        "endpoint": "https://fal.run/fal-ai/flux/klein/9b",
        "display": "FLUX Klein 9B (v1)",
        "description": "Original FLUX Klein 9B endpoint. Kept for compatibility with older workflows.",
        "default_steps": 4,
        "max_steps": 8,
        "size_format": "image_size_preset",
        "price": 0.006,
        "supports_negative": True,
        "extra_params": {"output_format": "png"},
    },
    "flux-2-pro": {
        "endpoint": "https://fal.run/fal-ai/flux-2-pro",
        "display": "FLUX 2 Pro",
        "description": "Latest FLUX 2 generation. Best overall quality with improved prompt adherence.",
        "default_steps": 50,
        "max_steps": 50,
        "size_format": "image_size_preset",
        "price": 0.04,
        "supports_negative": True,
        "extra_params": {"output_format": "png", "guidance_scale": 4.5, "num_images": 1},
    },
    "gpt-image-1.5": {
        "endpoint": "https://fal.run/fal-ai/gpt-image-1.5",
        "display": "GPT Image 1.5",
        "description": "OpenAI's GPT Image model. Excels at text rendering, complex multi-subject prompts, and following nuanced style instructions.",
        "default_steps": 8,
        "max_steps": 20,
        "size_format": "gpt_literal",
        "price": 0.034,
        "supports_negative": False,
    },
    "gpt-image-2": {
        "endpoint": "https://fal.run/fal-ai/gpt-image-2",
        "display": "GPT Image 2",
        "description": "Newest OpenAI image model. Better at text, precise compositions, and creative interpretation of detailed briefs.",
        "default_steps": 8,
        "max_steps": 20,
        "size_format": "image_size_preset",
        "price": 0.08,
        "supports_negative": False,
    },
    "nano-banana-2": {
        "endpoint": "https://fal.run/fal-ai/nano-banana-2",
        "display": "Nano Banana 2 (Gemini)",
        "description": "Google's newest image generation and editing model. State of the art for fast generation and natural-language edits.",
        "default_steps": None,
        "max_steps": None,
        "size_format": "aspect_ratio_enum",
        "extra_params": {"output_format": "png"},
        "price": 0.08,
        "supports_negative": False,
    },
    "nano-banana-pro": {
        "endpoint": "https://fal.run/fal-ai/nano-banana-pro",
        "display": "Nano Banana Pro (Gemini 3 Pro Image)",
        "description": "Gemini 3 Pro Image. Reasoning depth, strong text rendering, and natural-language editing.",
        "default_steps": None,
        "max_steps": None,
        "size_format": "aspect_ratio_enum",
        "extra_params": {"output_format": "png", "safety_tolerance": "5"},
        "price": 0.15,
        "supports_negative": False,
    },
    "clarity-upscaler": {
        "endpoint": "https://fal.run/fal-ai/clarity-upscaler",
        "display": "Clarity Upscaler",
        "description": "2x or 4x AI upscaling with sharpness enhancement.",
        "default_steps": None,
        "max_steps": None,
        "size_format": None,
        "price": 0.04,
        "supports_negative": False,
    },
    # --- Image-to-video models ---
    "kling-video": {
        "endpoint": "https://fal.run/fal-ai/kling-video/v3/pro/image-to-video",
        "display": "Kling Video v3 Pro",
        "description": "Kling v3 image-to-video. High quality motion synthesis, camera movement control, up to 10s clips.",
        "default_steps": None,
        "max_steps": None,
        "size_format": "video_ratio",
        "price": 0.35,
        "supports_negative": False,
        "kind": "video",
        "extra_params": {"duration": "5"},
    },
    "veo-fast": {
        "endpoint": "https://fal.run/fal-ai/veo3.1/fast/image-to-video",
        "display": "Veo 3.1 Fast",
        "description": "Google Veo 3.1 fast image-to-video. Fast, high-quality motion synthesis with audio support.",
        "default_steps": None,
        "max_steps": None,
        "size_format": "video_ratio",
        "price": 0.40,
        "supports_negative": False,
        "kind": "video",
        "extra_params": {"duration": "5s", "fps": 24},
    },
    # --- Inpainting model ---
    "flux-inpaint": {
        "endpoint": "https://fal.run/fal-ai/nano-banana-2/edit",
        "display": "Nano Banana 2 Inpaint",
        "description": "Region inpainting via Nano Banana 2 (Gemini). Replaces only the masked area of an image while preserving everything else. Pass image_url + mask_url (white = regenerate, black = keep).",
        "default_steps": None,
        "max_steps": None,
        "size_format": "aspect_ratio_enum",
        "price": 0.08,
        "supports_negative": False,
        "kind": "inpaint",
        "extra_params": {"output_format": "png"},
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
    # Social-ready formats
    "twitter-post": {"width": 1200, "height": 675},
    "twitter-header": {"width": 1500, "height": 500},
    "instagram-story": {"width": 1080, "height": 1920},
    "instagram-post": {"width": 1080, "height": 1080},
    "youtube-thumb": {"width": 1280, "height": 720},
}

ASPECT_RATIO_ALIASES: Dict[str, str] = {
    "1:1": "square",
    "16:9": "landscape",
    "9:16": "portrait",
    "wide": "landscape",
    "tall": "portrait",
    "social": "twitter-post",
    "x-post": "twitter-post",
    "twitter": "twitter-post",
    "x-header": "twitter-header",
    "banner": "twitter-header",
    "story": "instagram-story",
    "ig-story": "instagram-story",
    "ig-post": "instagram-post",
    "yt": "youtube-thumb",
    "youtube": "youtube-thumb",
    "video-thumb": "youtube-thumb",
}

# Base (canonical) aspect ratios used when a model can't express a
# non-standard social size. Social sizes always fall back to their
# closest standard shape.
_SOCIAL_BASE: Dict[str, str] = {
    "twitter-post": "landscape",
    "twitter-header": "landscape",
    "instagram-story": "portrait",
    "instagram-post": "square",
    "youtube-thumb": "landscape",
}


def _base_ratio(ar_key: str) -> str:
    """Return the canonical base ratio for a given aspect key."""
    return _SOCIAL_BASE.get(ar_key, ar_key)

# Size format mappings for models that don't use the standard {width, height} object
# GPT Image 1.5 uses literal dimension strings
GPT_LITERAL_SIZES: Dict[str, str] = {
    "square": "1024x1024",
    "landscape": "1792x1024",
    "portrait": "1024x1792",
}

# GPT Image 2 and FLUX 2 Pro use preset enums (same style as FLUX but different values)
IMAGE_SIZE_PRESETS: Dict[str, str] = {
    "square": "square_hd",
    "landscape": "landscape_16_9",
    "portrait": "portrait_16_9",
}

# Nano Banana (Gemini) models use aspect ratio enums like "16:9", "1:1", "9:16"
ASPECT_RATIO_ENUMS: Dict[str, str] = {
    "square": "1:1",
    "landscape": "16:9",
    "portrait": "9:16",
}

# Video models use ratio strings like "16:9" directly
VIDEO_RATIOS: Dict[str, str] = {
    "square": "1:1",
    "landscape": "16:9",
    "portrait": "9:16",
    "twitter-post": "16:9",
    "twitter-header": "16:9",
    "instagram-story": "9:16",
    "instagram-post": "1:1",
    "youtube-thumb": "16:9",
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
    raw = detail.get("detail") or detail.get("message") or str(detail)
    if isinstance(raw, list):
        # FAL validation errors: [{"type": ..., "loc": [...], "msg": ..., "ctx": {...}}]
        parts = []
        for item in raw:
            if isinstance(item, dict):
                loc = ".".join(str(x) for x in item.get("loc", []))
                msg = item.get("msg", "")
                parts.append(f"{loc}: {msg}" if loc else msg)
            else:
                parts.append(str(item))
        msg = "; ".join(parts) if parts else str(raw)
    else:
        msg = str(raw)
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
    negative_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate an image via FAL.

    Args:
        prompt: What to generate.
        model: Model key from MODELS.
        aspect_ratio: Aspect ratio key (square, landscape, portrait, or a
            social-ready alias like twitter-post, instagram-story).
        seed: Random seed (-1 = random).
        steps: Inference steps (auto if None).
        negative_prompt: Things to avoid (only supported by FLUX models).

    Returns:
        dict with keys: image_url, seed, model, preset_name, steps,
        aspect_ratio, width, height, cost_usd
    """
    model_info = MODELS.get(model)
    if model_info is None:
        raise ValueError(
            f"Unknown model '{model}'. Available: {', '.join(MODELS)}"
        )

    ar_key = resolve_aspect_ratio(aspect_ratio)
    size_format = model_info.get("size_format", "object")
    # For non-object formats, fall back to the closest standard ratio
    effective_ar = ar_key if size_format == "object" else _base_ratio(ar_key)

    # Build payload based on model's size format
    payload: Dict[str, Any] = {"prompt": prompt}

    if size_format == "object":
        size = ASPECT_RATIO_SIZES[ar_key]
        payload["image_size"] = size
        w, h = size["width"], size["height"]
    elif size_format == "gpt_literal":
        dims_str = GPT_LITERAL_SIZES[effective_ar]
        payload["image_size"] = dims_str
        dims = dims_str.split("x")
        w, h = int(dims[0]), int(dims[1])
    elif size_format == "image_size_preset":
        preset = IMAGE_SIZE_PRESETS[effective_ar]
        payload["image_size"] = preset
        canon = ASPECT_RATIO_SIZES[effective_ar]
        w, h = canon["width"], canon["height"]
    elif size_format == "aspect_ratio_enum":
        payload["aspect_ratio"] = ASPECT_RATIO_ENUMS[effective_ar]
        canon = ASPECT_RATIO_SIZES[effective_ar]
        w, h = canon["width"], canon["height"]
    else:
        size = ASPECT_RATIO_SIZES[ar_key]
        payload["image_size"] = size
        w, h = size["width"], size["height"]

    # Negative prompts (FLUX models only)
    if negative_prompt:
        if not model_info.get("supports_negative", False):
            raise ValueError(
                f"Model '{model}' does not support negative prompts. "
                "Use a FLUX model (flux-pro, flux-klein, flux-2-pro) instead."
            )
        payload["negative_prompt"] = negative_prompt

    # Nano Banana models don't use inference steps; skip if not defined
    if model_info.get("default_steps") is not None:
        steps = steps if steps is not None else model_info["default_steps"]
        if model_info["max_steps"] and steps > model_info["max_steps"]:
            steps = model_info["max_steps"]
        payload["num_inference_steps"] = steps
    else:
        steps = None

    # Merge model-specific extra params (output_format, safety_tolerance, etc.)
    for key, val in (model_info.get("extra_params") or {}).items():
        payload[key] = val

    payload["seed"] = seed

    result = _request(model_info["endpoint"], payload)
    images = result.get("images") or []
    if not images:
        raise RuntimeError(f"FAL returned no images: {json.dumps(result)[:300]}")

    return {
        "image_url": images[0]["url"],
        "seed": result.get("seed", seed),
        "model": model,
        "steps": steps,
        "aspect_ratio": ar_key,
        "width": w,
        "height": h,
        "cost_usd": model_info.get("price", 0.0),
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
        "cost_usd": MODELS["clarity-upscaler"].get("price", 0.0),
    }


def edit(
    image_url: str,
    prompt: str,
    *,
    model: str = "gpt-image-1.5",
    aspect_ratio: str = "square",
    steps: Optional[int] = None,
) -> Dict[str, Any]:
    """Edit an existing image via FAL (img2img).

    Accepts a source image URL and a prompt describing the edit.
    Works with GPT Image 1.5 (best for precise edits), FLUX 2 Pro,
    and FLUX 2 Klein 9B.

    Returns:
        dict with keys: image_url, model, aspect_ratio, width, height, steps
    """
    model_info = MODELS.get(model)
    if model_info is None:
        raise ValueError(f"Unknown model '{model}'. Available: gpt-image-1.5, flux-2-pro, flux-klein")

    ar_key = resolve_aspect_ratio(aspect_ratio)
    size_format = model_info.get("size_format", "object")

    payload: Dict[str, Any] = {
        "prompt": prompt,
        "image_urls": [image_url],
    }

    if size_format == "gpt_literal":
        payload["image_size"] = GPT_LITERAL_SIZES[ar_key]
        dims = GPT_LITERAL_SIZES[ar_key].split("x")
        w, h = int(dims[0]), int(dims[1])
    elif size_format == "image_size_preset":
        payload["image_size"] = IMAGE_SIZE_PRESETS[ar_key]
        canon = ASPECT_RATIO_SIZES[ar_key]
        w, h = canon["width"], canon["height"]
    elif size_format == "aspect_ratio_enum":
        payload["aspect_ratio"] = ASPECT_RATIO_ENUMS[ar_key]
        canon = ASPECT_RATIO_SIZES[ar_key]
        w, h = canon["width"], canon["height"]
    else:
        size = ASPECT_RATIO_SIZES[ar_key]
        payload["image_size"] = size
        w, h = size["width"], size["height"]

    # Nano Banana models don't use inference steps; skip if not defined
    if model_info.get("default_steps") is not None:
        steps = steps if steps is not None else model_info["default_steps"]
        if model_info["max_steps"] and steps > model_info["max_steps"]:
            steps = model_info["max_steps"]
        payload["num_inference_steps"] = steps
    else:
        steps = None

    # Merge model-specific extra params
    for key, val in (model_info.get("extra_params") or {}).items():
        payload[key] = val

    # Edit endpoints use the same base URL with /edit suffix
    base_endpoint = model_info["endpoint"]
    edit_endpoint = f"{base_endpoint}/edit"

    result = _request(edit_endpoint, payload)
    images = result.get("images") or []
    if not images:
        raise RuntimeError(f"Edit endpoint returned no images: {json.dumps(result)[:300]}")

    return {
        "image_url": images[0]["url"],
        "seed": result.get("seed", -1),
        "model": model,
        "steps": steps,
        "aspect_ratio": ar_key,
        "width": w,
        "height": h,
        "cost_usd": model_info.get("price", 0.0),
    }


def animate(
    image_url: str,
    prompt: str,
    *,
    model: str = "kling-video",
    aspect_ratio: str = "landscape",
    duration: Optional[str] = None,
) -> Dict[str, Any]:
    """Animate a still image into a short video clip via FAL.

    Args:
        image_url: Public URL of the source image.
        prompt: What motion / camera work to add ("slow dolly-in on the subject, waves lapping").
        model: Video model key ('kling-video' or 'veo-fast').
        aspect_ratio: Output ratio (landscape, portrait, square, or social alias).
        duration: Clip length. Model clamps. Kling: '5' or '10'. Veo: '5s' or '8s'.

    Returns:
        dict with keys: video_url, model, aspect_ratio, cost_usd
    """
    model_info = MODELS.get(model)
    if model_info is None:
        raise ValueError(
            f"Unknown video model '{model}'. Available: kling-video, veo-fast"
        )
    if model_info.get("kind") != "video":
        raise ValueError(f"Model '{model}' is not a video model.")

    ar_key = resolve_aspect_ratio(aspect_ratio)
    ratio = VIDEO_RATIOS.get(ar_key, "16:9")

    payload: Dict[str, Any] = {
        "prompt": prompt,
        "image_url": image_url,
        "aspect_ratio": ratio,
    }
    # Model-specific extra params (duration, fps, etc.)
    for key, val in (model_info.get("extra_params") or {}).items():
        payload[key] = val
    if duration:
        payload["duration"] = duration

    result = _request(model_info["endpoint"], payload, timeout=300)
    video = result.get("video") or {}
    video_url = video.get("url") or result.get("video_url") or ""
    if not video_url:
        raise RuntimeError(f"FAL returned no video: {json.dumps(result)[:300]}")

    return {
        "video_url": video_url,
        "model": model,
        "aspect_ratio": ar_key,
        "duration": payload.get("duration"),
        "cost_usd": model_info.get("price", 0.0),
    }


def inpaint(
    image_url: str,
    mask_url: str,
    prompt: str,
    *,
    model: str = "flux-inpaint",
    seed: int = -1,
    steps: Optional[int] = None,
    negative_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """Inpaint (region-edit) an image via FAL using a mask.

    Args:
        image_url: Public URL of the source image.
        mask_url: Public URL of a black-and-white mask image. White areas are
            regenerated; black areas are preserved.
        prompt: What to generate in the masked region.
        model: Inpaint model key ('flux-inpaint').
        seed: Random seed (-1 = random).
        steps: Inference steps.
        negative_prompt: Things to avoid (FLUX models only).

    Returns:
        dict with keys: image_url, model, seed, width, height, cost_usd
    """
    model_info = MODELS.get(model)
    if model_info is None:
        raise ValueError(f"Unknown model '{model}'. Available: flux-inpaint")
    if model_info.get("kind") != "inpaint":
        raise ValueError(f"Model '{model}' is not an inpaint model.")

    size = ASPECT_RATIO_SIZES["square"]
    w, h = size["width"], size["height"]

    payload: Dict[str, Any] = {
        "prompt": prompt,
        "image_urls": [image_url],
        "mask_urls": [mask_url],
    }

    # Merge model-specific extra params (output_format, etc.)
    for key, val in (model_info.get("extra_params") or {}).items():
        payload[key] = val

    # Nano Banana models don't use inference steps
    steps = None

    payload["seed"] = seed

    result = _request(model_info["endpoint"], payload)
    images = result.get("images") or []
    if not images:
        raise RuntimeError(f"FAL returned no images: {json.dumps(result)[:300]}")

    return {
        "image_url": images[0]["url"],
        "seed": result.get("seed", seed),
        "model": model,
        "steps": steps,
        "aspect_ratio": "square",
        "width": w,
        "height": h,
        "cost_usd": model_info.get("price", 0.0),
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
