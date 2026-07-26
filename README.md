# Hermes Image Studio

**AI image generation plugin for [Hermes Agent](https://hermes-agent.nousresearch.com).**
Style presets, auto-upscaling, batch generation, and history tracking via FAL.ai.

Generate publish-ready images for social media, articles, and creative projects
directly from your Hermes conversations. No running to another tool.

## Features

- **8 Style Presets** — Cinematic, photorealistic, vintage, fantasy, illustration,
  minimalist, noir, and studio. Each preset tunes prompt phrasing, inference steps,
  and model selection for consistent visual results.
- **Auto-Upscaling** — Every image can be 2x upscaled with a single command.
- **Batch Generation** — Generate 2-8 variants simultaneously with random seeds
  to explore compositions and find the best result.
- **History Tracking** — Every generation is recorded in a local SQLite database.
  Browse, re-find, or reference past creations.
- **Organized Outputs** — Images are saved with descriptive filenames
  (`20260726_103042_cinematic_472444619_cowboys-at-sunrise.png`) to a
  configurable output directory.

## Requirements

- Hermes Agent (any recent version)
- Python 3.10+
- A [FAL.ai](https://fal.ai) account with credits

## Installation

### Option A: Quick install (clone + symlink)

```bash
git clone https://github.com/YOUR_USERNAME/hermes-image-studio.git
ln -s "$PWD/hermes-image-studio" ~/.hermes/plugins/image-studio
```

### Option B: Manual install

Copy the `hermes-image-studio` directory into `~/.hermes/plugins/`:

```bash
cp -r hermes-image-studio ~/.hermes/plugins/image-studio
```

### Enable the plugin

```bash
hermes plugins enable image-studio
```

Restart Hermes (or start a new session). The plugin auto-loads when
`FAL_KEY` is set.

## Setup

Get your FAL.ai API key:

1. Sign up at [fal.ai](https://fal.ai)
2. Go to [fal.ai/dashboard](https://fal.ai/dashboard) and create an API key
3. Add it to `~/.hermes/.env`:

```
FAL_KEY=your-api-key-here
```

That's it. Start a new Hermes session and you're ready.

## Tools

The plugin registers 5 tools into the `image-studio` toolset:

| Tool | What it does |
|------|-------------|
| `image_studio_generate` | Generate a single image with a style preset |
| `image_studio_upscale` | 2x upscale any generated image |
| `image_studio_batch` | Generate N variants with random seeds |
| `image_studio_presets` | List all available presets with descriptions |
| `image_studio_history` | Browse recent generations |

### Quick Examples

```text
# Generate a cinematic landscape
image_studio_generate(prompt="A lone cowboy riding through Monument Valley at sunrise, warm golden light, dust kicking up", preset="cinematic", aspect_ratio="landscape")

# List presets
image_studio_presets

# Batch 4 variants
image_studio_batch(prompt="A futuristic cityscape at night with neon lights", preset="fantasy", count=4)

# Upscale the result
image_studio_upscale(image_url="https://v3b.fal.media/...")

# Check history
image_studio_history(limit=5)
```

## Style Presets

| Preset | Description | Steps |
|--------|-------------|-------|
| `cinematic` | Movie-grade lighting, shallow DOF, film grain | 30 |
| `photorealistic` | True-to-life natural look, sharp focus | 28 |
| `vintage` | Warm faded tones, film grain, kodachrome palette | 30 |
| `fantasy` | Epic, magical lighting, rich colors, concept art | 32 |
| `minimalist` | Clean, soft lighting, muted palette, editorial | 26 |
| `illustration` | Bold artistic style, painterly textures | 28 |
| `noir` | High contrast, dramatic shadows, black and white | 30 |
| `studio` | Controlled lighting, clean background, product-ready | 28 |

## Output Location

Images are saved to `/Volumes/Spare Drive/Personal Stuff/Image Studio/`
by default. Filename pattern:

```
YYYYMMDD_HHMMSS_preset_seed_subject.png
```

## Skills

The repo includes 3 Hermes skills in the `skills/` directory:

- **generate-image.skill.md** — Guided single-image generation
- **batch-generate.skill.md** — Batch variant exploration
- **image-studio-workflow.skill.md** — End-to-end pipeline from prompt to publish

Copy these to `~/.hermes/skills/` to load them into Hermes sessions.

## How It Works

Image Studio is a standard Hermes plugin. The `plugin.yaml` and `__init__.py`
register 5 tools that wrap FAL.ai's REST API using only Python stdlib (no
extra dependencies). Each generation is:

1. Prompt enhanced with the chosen preset's style framing
2. Sent to FAL's FLUX Pro or Klein endpoint
3. Downloaded and saved with a descriptive filename
4. Recorded in a local SQLite history database
5. Ready for upscaling or re-generation with a different seed

## License

MIT
