"""Curated style presets for Hermes Image Studio.

Each preset wraps a prompt with stylistic prefixes/suffixes and tuned
parameters (steps, guidance) to produce consistent visual results.
Presets are designed to be composable — the user's main prompt is
injected between the prefix and suffix.

To add a new preset, append an entry to PRESETS and it will
auto-discover through list_presets() and apply_preset().
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Preset catalog
# ---------------------------------------------------------------------------

PRESETS: Dict[str, Dict[str, Any]] = {
    "cinematic": {
        "name": "Cinematic",
        "description": "Movie-grade lighting, rich contrast, shallow depth of field. Great for landscapes, portraits, and action scenes.",
        "prefix": "Cinematic wide shot, professional film lighting, rich contrast, shallow depth of field, 35mm film grain, award-winning cinematography, ",
        "suffix": ", cinematic color grading, dramatic lighting, volumetric atmosphere, hyper-detailed, 8K",
        "steps": 30,
        "model": "flux-pro",
    },
    "photorealistic": {
        "name": "Photorealistic",
        "description": "True-to-life natural look for product shots, environments, and scenes where realism matters most.",
        "prefix": "",
        "suffix": ", photorealistic, natural lighting, sharp focus, detailed textures, true to life, canon eos r5, 50mm lens, natural color palette, ultra realistic",
        "steps": 28,
        "model": "flux-pro",
    },
    "vintage": {
        "name": "Vintage / Old Days",
        "description": "Warm, faded tones with film grain and period-appropriate color grading. Perfect for historical, retro, and nostalgic scenes.",
        "prefix": "Vintage photograph style, warm faded tones, film grain, ",
        "suffix": ", kodachrome, 1970s color palette, slightly desaturated, light leaks, retro aesthetic, timeless composition, aged photo look",
        "steps": 30,
        "model": "flux-pro",
    },
    "fantasy": {
        "name": "Fantasy / Epic",
        "description": "Dramatic, otherworldly scenes with rich colors, magical lighting, and epic scale. Ideal for concept art and imaginative landscapes.",
        "prefix": "Epic fantasy scene, dramatic atmospheric lighting, rich vibrant colors, magical glow, ",
        "suffix": ", concept art, artstation, greg rutkowski inspired, ethereal atmosphere, detailed, majestic, otherworldly, volumetric light, 8K",
        "steps": 32,
        "model": "flux-pro",
    },
    "minimalist": {
        "name": "Minimalist / Clean",
        "description": "Clean, uncluttered compositions with soft lighting and restrained color. Great for modern branding, UI concepts, and editorial shots.",
        "prefix": "Minimalist composition, clean aesthetic, soft diffused lighting, ",
        "suffix": ", muted color palette, simple background, elegant, uncluttered, editorial style, soft shadows, natural tones, high key",
        "steps": 26,
        "model": "flux-pro",
    },
    "illustration": {
        "name": "Digital Illustration",
        "description": "Bold, artistic illustration style with strong lines and vibrant colors. Feels hand-crafted and expressive.",
        "prefix": "Digital illustration, bold artistic style, ",
        "suffix": ", vibrant colors, strong composition, detailed linework, painterly textures, expressive, stylized, 2D digital art, crisp detail",
        "steps": 28,
        "model": "flux-pro",
    },
    "noir": {
        "name": "Film Noir / Moody",
        "description": "High-contrast, shadowy scenes with dramatic chiaroscuro lighting. Perfect for mystery, thriller, and moody atmospheric shots.",
        "prefix": "Film noir style, dramatic chiaroscuro lighting, deep shadows, ",
        "suffix": ", high contrast, black and white, hard light, venetian blinds shadows, moody atmosphere, cinematic, 1940s detective film grain",
        "steps": 30,
        "model": "flux-pro",
    },
    "studio": {
        "name": "Studio / Product",
        "description": "Clean, well-lit studio setup with controlled lighting for product shots, portraits, and food photography.",
        "prefix": "Professional studio photography, controlled lighting setup, ",
        "suffix": ", clean background, softbox lighting, product photography, sharp focus, white background, commercial photography, high key, detailed",
        "steps": 28,
        "model": "flux-pro",
    },
    "gpt-photo": {
        "name": "GPT Photo (Text + Complex Scenes)",
        "description": "GPT Image excels at rendering text, following detailed multi-subject prompts, and nuanced style instructions. Use this for signs, labels, complex compositions, and when the scene has specific constraints.",
        "prefix": "",
        "suffix": ", highly detailed, well-composed, accurate proportions, natural lighting",
        "steps": 8,
        "model": "gpt-image-1.5",
    },
    "gpt-art": {
        "name": "GPT Artistic (Creative + Stylized)",
        "description": "GPT Image's strong instruction-following makes it ideal for specific art styles, creative interpretations, and scenes with precise descriptive requirements.",
        "prefix": "In the style of, ",
        "suffix": ", artistic, creative composition, vibrant colors, expressive, detailed brushwork, stylized",
        "steps": 8,
        "model": "gpt-image-2",
    },
}

# ---------------------------------------------------------------------------
# Preset API
# ---------------------------------------------------------------------------

DEFAULT_PRESET = "cinematic"


def list_presets() -> List[Dict[str, Any]]:
    """Return all presets as a list of dicts with name, description, and params."""
    result = []
    for key, preset in PRESETS.items():
        result.append({
            "key": key,
            "name": preset["name"],
            "description": preset["description"],
            "default_steps": preset["steps"],
            "model": preset.get("model", "flux-pro"),
        })
    return result


def apply_preset(preset_name: str, user_prompt: str) -> Dict[str, Any]:
    """Apply a named preset to a user prompt.

    Returns:
        dict with keys: prompt (the combined prompt), steps, model
    """
    if preset_name not in PRESETS:
        available = ", ".join(PRESETS)
        raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")

    preset = PRESETS[preset_name]
    prefix = preset["prefix"]
    suffix = preset["suffix"]

    # Avoid double-spacing
    combined = f"{prefix}{user_prompt}{suffix}".strip()

    return {
        "prompt": combined,
        "steps": preset["steps"],
        "model": preset.get("model", "flux-pro"),
        "preset_name": preset_name,
    }


def get_preset(preset_name: str) -> Optional[Dict[str, Any]]:
    """Get a single preset by key, or None."""
    raw = PRESETS.get(preset_name)
    if raw is None:
        return None
    return {**raw, "key": preset_name}
