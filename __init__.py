"""Hermes Image Studio — Hermes plugin entry point.

Registers 5 tools into the ``image-studio`` toolset:

- ``image_studio_generate`` — Generate an image with a style preset
- ``image_studio_upscale`` — Upscale a generated image
- ``image_studio_batch`` — Generate multiple variants with different seeds
- ``image_studio_presets`` — List all available style presets
- ``image_studio_history`` — Browse recent generations

Each tool wraps FAL.ai's API with preset-aware prompt engineering,
auto-saving to a configured output directory, and SQLite history tracking.

Installation: symlink or copy this directory into ~/.hermes/plugins/image-studio/
then run ``hermes plugins enable image-studio``.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from tools.registry import tool_error, tool_result

from image_studio import engine, history, organizer, presets

# ---------------------------------------------------------------------------
# Tool schemas (JSON Schema for each tool)
# ---------------------------------------------------------------------------

GENERATE_SCHEMA = {
    "name": "image_studio_generate",
    "description": "Generate an AI image using a style preset. Supports photorealistic, cinematic, vintage, fantasy, illustration, minimalist, noir, and studio styles. The prompt is automatically enhanced with the preset's stylistic prefix/suffix and tuned parameters.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Describe what to generate. Be specific about subjects, setting, lighting, and mood.",
            },
            "preset": {
                "type": "string",
                "description": "Style preset name. Use image_studio_presets to see all options.",
                "default": "cinematic",
            },
            "aspect_ratio": {
                "type": "string",
                "description": 'Aspect ratio: "landscape" (16:9), "square" (1:1), or "portrait" (9:16).',
                "default": "landscape",
            },
            "seed": {
                "type": "integer",
                "description": "Random seed for reproducibility. -1 = random.",
                "default": -1,
            },
        },
        "required": ["prompt"],
    },
}

UPSCALE_SCHEMA = {
    "name": "image_studio_upscale",
    "description": "Upscale a previously generated image by 2x using Clarity Upscaler. Accepts a FAL URL from a prior generation.",
    "parameters": {
        "type": "object",
        "properties": {
            "image_url": {
                "type": "string",
                "description": "Public URL of the image to upscale (from a prior generation or any accessible image URL).",
            },
        },
        "required": ["image_url"],
    },
}

BATCH_SCHEMA = {
    "name": "image_studio_batch",
    "description": "Generate multiple variants of the same prompt with different random seeds. Each image is saved and tracked independently. Use this for exploring compositions, finding the best seed, or creating variety packs.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Describe what to generate.",
            },
            "count": {
                "type": "integer",
                "description": "Number of variants to generate (2-8).",
                "default": 4,
            },
            "preset": {
                "type": "string",
                "description": "Style preset name.",
                "default": "cinematic",
            },
            "aspect_ratio": {
                "type": "string",
                "description": 'Aspect ratio: "landscape", "square", or "portrait".',
                "default": "landscape",
            },
        },
        "required": ["prompt"],
    },
}

PRESETS_SCHEMA = {
    "name": "image_studio_presets",
    "description": "List all available style presets with descriptions and default parameters. Call this first if you are unsure which preset to use.",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

HISTORY_SCHEMA = {
    "name": "image_studio_history",
    "description": "Browse recent image generations. Shows prompt, preset, seed, model, and file path for each entry. Optionally re-generate a past image with a tweaked prompt.",
    "parameters": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Number of recent generations to show (max 50).",
                "default": 10,
            },
        },
    },
}

EDIT_SCHEMA = {
    "name": "image_studio_edit",
    "description": "Edit an existing image by providing a new prompt describing the change. Uses GPT Image 1.5 (best for precise edits like turning a circle into a square) or FLUX 2 Pro. The source image can be from a prior generation or any accessible image URL.",
    "parameters": {
        "type": "object",
        "properties": {
            "image_url": {
                "type": "string",
                "description": "URL of the image to edit. Use the image_url from a prior generation result.",
            },
            "prompt": {
                "type": "string",
                "description": "Describe what to change. Be specific: 'turn the red circle into a blue square', 'add a dirt path leading to the front door', 'make it look like a watercolor painting'.",
            },
            "aspect_ratio": {
                "type": "string",
                "description": 'Aspect ratio: "square" (1:1), "landscape" (16:9), or "portrait" (9:16).',
                "default": "square",
            },
        },
        "required": ["image_url", "prompt"],
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_OUTPUT_ROOT = os.environ.get(
    "HERMES_IMAGE_STUDIO_OUTPUT",
    os.path.expanduser("/Volumes/Spare Drive/Personal Stuff/Image Studio"),
)


def _check_fal_available() -> bool:
    """Gate all tools on FAL being configured."""
    try:
        engine._get_fal_key()
        return True
    except RuntimeError:
        return False


def _generate_and_save(
    prompt: str,
    preset_name: str = "cinematic",
    aspect_ratio: str = "landscape",
    seed: int = -1,
) -> Dict[str, Any]:
    """Run a generation, save the output, record history, return results."""
    # Apply preset
    enhanced = presets.apply_preset(preset_name, prompt)
    full_prompt = enhanced["prompt"]
    steps = enhanced["steps"]
    model = enhanced["model"]

    # Generate
    gen = engine.generate(
        full_prompt,
        model=model,
        aspect_ratio=aspect_ratio,
        seed=seed,
        steps=steps,
    )

    # Save locally
    file_path = organizer.save_generated_image(
        gen["image_url"],
        prompt,  # original user prompt for the filename
        preset=preset_name,
        seed=gen["seed"],
        output_root=_OUTPUT_ROOT,
    )

    # Record history
    gen_id = history.record_generation(
        prompt=prompt,
        preset=preset_name,
        model=gen["model"],
        seed=gen["seed"],
        steps=gen.get("steps", steps),
        aspect_ratio=gen.get("aspect_ratio", aspect_ratio),
        width=gen.get("width", 0),
        height=gen.get("height", 0),
        image_url=gen["image_url"],
        file_path=file_path,
    )

    return {
        "gen_id": gen_id,
        "image_url": gen["image_url"],
        "file_path": file_path,
        "seed": gen["seed"],
        "model": gen["model"],
        "preset": preset_name,
        "aspect_ratio": gen.get("aspect_ratio", aspect_ratio),
    }


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


def _handle_generate(prompt: str, **kwargs: Any) -> str:
    preset_name = kwargs.get("preset", "cinematic")
    aspect_ratio = kwargs.get("aspect_ratio", "landscape")
    seed = int(kwargs.get("seed", -1))

    try:
        result = _generate_and_save(prompt, preset_name, aspect_ratio, seed)
        return tool_result(
            result,
            title="Image Generated",
            emoji="🎨",
        )
    except (ValueError, RuntimeError, PermissionError) as exc:
        return tool_error(str(exc))


def _handle_upscale(image_url: str, **kwargs: Any) -> str:
    try:
        upscaled = engine.upscale(image_url)

        # Try to find the source generation in history for a better filename
        source_path = ""
        src = history.find_by_image_url(image_url)
        if src and src.get("file_path"):
            source_path = src["file_path"]
            import os as _os
            base = _os.path.splitext(_os.path.basename(source_path))[0]
            # Save alongside the original with _HD suffix
            root = _os.path.dirname(source_path)
            hd_filename = f"{base}_HD.png"
            file_path = _os.path.join(root, hd_filename)
            # Download the upscaled image
            import urllib.request
            req = urllib.request.Request(upscaled["image_url"],
                                         headers={"User-Agent": "Hermes-ImageStudio/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                with open(file_path, "wb") as f:
                    f.write(resp.read())
        else:
            # No history match, use the generic organizer method
            file_path = organizer.save_upscaled_image(
                upscaled["image_url"], "upscaled", output_root=_OUTPUT_ROOT,
            )

        # Record in upscale history
        src_id = src["id"] if src else None
        history.record_upscale(
            source_image_url=image_url,
            result_image_url=upscaled["image_url"],
            scale=upscaled.get("scale", 2),
            source_gen_id=src_id,
        )

        return tool_result(
            {
                "image_url": upscaled["image_url"],
                "file_path": file_path,
                "scale": upscaled.get("scale", 2),
            },
            title="Image Upscaled",
            emoji="🔍",
        )
    except (ValueError, RuntimeError, PermissionError) as exc:
        return tool_error(str(exc))


def _handle_batch(prompt: str, **kwargs: Any) -> str:
    count = min(int(kwargs.get("count", 4)), 8)
    preset_name = kwargs.get("preset", "cinematic")
    aspect_ratio = kwargs.get("aspect_ratio", "landscape")

    results: List[Dict[str, Any]] = []
    errors: List[str] = []

    for i in range(count):
        try:
            result = _generate_and_save(
                prompt,
                preset_name=preset_name,
                aspect_ratio=aspect_ratio,
                seed=-1,  # random each time
            )
            results.append(result)
        except (ValueError, RuntimeError, PermissionError) as exc:
            errors.append(f"variant {i+1}: {exc}")

    return tool_result(
        {
            "total": len(results),
            "errors": errors if errors else None,
            "generations": [
                {
                    "gen_id": r["gen_id"],
                    "seed": r["seed"],
                    "file_path": r["file_path"],
                }
                for r in results
            ],
        },
        title=f"Batch Complete ({len(results)}/{count} generated)",
        emoji="📸",
    )


def _handle_presets(**kwargs: Any) -> str:
    all_presets = presets.list_presets()
    return tool_result(
        {"presets": all_presets, "default": presets.DEFAULT_PRESET},
        title="Available Style Presets",
        emoji="🎭",
    )


def _handle_edit(image_url: str, prompt: str, **kwargs: Any) -> str:
    aspect_ratio = kwargs.get("aspect_ratio", "square")

    try:
        # Use GPT Image 1.5 for edits (best for prompt fidelity)
        result = engine.edit(
            image_url,
            prompt,
            model="gpt-image-1.5",
            aspect_ratio=aspect_ratio,
        )

        # Save locally
        file_path = organizer.save_generated_image(
            result["image_url"],
            prompt,
            preset="edit",
            seed=result.get("seed", -1),
            output_root=_OUTPUT_ROOT,
        )

        # Record in history
        gen_id = history.record_generation(
            prompt=prompt,
            preset="edit",
            model=result["model"],
            seed=result.get("seed", -1),
            steps=result.get("steps", 8),
            aspect_ratio=result.get("aspect_ratio", aspect_ratio),
            width=result.get("width", 0),
            height=result.get("height", 0),
            image_url=result["image_url"],
            file_path=file_path,
        )

        return tool_result(
            {
                "gen_id": gen_id,
                "image_url": result["image_url"],
                "file_path": file_path,
                "model": result["model"],
                "aspect_ratio": result.get("aspect_ratio", aspect_ratio),
            },
            title="Image Edited",
            emoji="🖌️",
        )
    except (ValueError, RuntimeError, PermissionError) as exc:
        return tool_error(str(exc))


def _handle_history(**kwargs: Any) -> str:
    limit = min(int(kwargs.get("limit", 10)), 50)
    entries = history.recent_generations(limit)

    if not entries:
        return tool_result(
            {"message": "No generations yet. Create one with image_studio_generate."},
            title="Generation History (empty)",
            emoji="📜",
        )

    formatted = []
    for e in entries:
        formatted.append({
            "id": e["id"],
            "created_at": e["created_at"],
            "prompt": e["prompt"],
            "preset": e.get("preset"),
            "seed": e["seed"],
            "file_path": e.get("file_path", ""),
        })

    return tool_result(
        {"generations": formatted, "total": history.count_generations()},
        title=f"Generation History (last {len(entries)})",
        emoji="📜",
    )


# ---------------------------------------------------------------------------
# Tool registration table
# ---------------------------------------------------------------------------

_TOOLS = (
    ("image_studio_generate", GENERATE_SCHEMA, _handle_generate, "🎨"),
    ("image_studio_edit", EDIT_SCHEMA, _handle_edit, "🖌️"),
    ("image_studio_upscale", UPSCALE_SCHEMA, _handle_upscale, "🔍"),
    ("image_studio_batch", BATCH_SCHEMA, _handle_batch, "📸"),
    ("image_studio_presets", PRESETS_SCHEMA, _handle_presets, "🎭"),
    ("image_studio_history", HISTORY_SCHEMA, _handle_history, "📜"),
)


def register(ctx) -> None:
    """Register all Image Studio tools. Called by the Hermes plugin loader."""
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="image-studio",
            schema=schema,
            handler=handler,
            check_fn=_check_fal_available,
            emoji=emoji,
        )
