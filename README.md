# Hermes Image Studio

![Hero](hero.png)

**AI image generation plugin for [Hermes Agent](https://hermes-agent.nousresearch.com).**
10 style presets across 6 FLUX and GPT Image models. Auto-upscaling, batch generation, and SQLite history tracking, all through FAL.ai.

Generate publish-ready images for social media, articles, and creative projects
directly from your Hermes conversations. No running to another tool.

## Features

- **8 Style Presets** — Cinematic, photorealistic, vintage, fantasy, illustration,
  minimalist, noir, and studio for FLUX models. Each preset tunes prompt phrasing,
  inference steps, and model selection for consistent visual results.
- **2 GPT Presets** — `gpt-photo` for text rendering and complex multi-subject
  scenes (GPT Image 1.5), and `gpt-art` for creative and stylized interpretation
  (GPT Image 2).
- **6 Models** — FLUX Pro, FLUX Klein, FLUX 2 Pro, GPT Image 1.5, GPT Image 2,
  and Clarity Upscaler. Choose the right tool for the job.
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

| Preset | Description | Steps | Model |
|--------|-------------|-------|-------|
| `cinematic` | Movie-grade lighting, shallow DOF, film grain | 30 | FLUX Pro |
| `photorealistic` | True-to-life natural look, sharp focus | 28 | FLUX Pro |
| `vintage` | Warm faded tones, film grain, kodachrome palette | 30 | FLUX Pro |
| `fantasy` | Epic, magical lighting, rich colors, concept art | 32 | FLUX Pro |
| `minimalist` | Clean, soft lighting, muted palette, editorial | 26 | FLUX Pro |
| `illustration` | Bold artistic style, painterly textures | 28 | FLUX Pro |
| `noir` | High contrast, dramatic shadows, black and white | 30 | FLUX Pro |
| `studio` | Controlled lighting, clean background, product-ready | 28 | FLUX Pro |
| `gpt-photo` | Text rendering, complex scenes, specific constraints | 8 | GPT Image 1.5 |
| `gpt-art` | Artistic styles, creative interpretation, stylized | 8 | GPT Image 2 |

## Output Location

Images are saved to `/Volumes/Spare Drive/Personal Stuff/Image Studio/`
by default. You can change this by setting the `HERMES_IMAGE_STUDIO_OUTPUT`
environment variable in `~/.hermes/.env`:

```
HERMES_IMAGE_STUDIO_OUTPUT=/path/to/your/images
```

Filename pattern:

```
YYYYMMDD_HHMMSS_preset_seed_subject.png
```

## Skills

The repo includes 3 Hermes skills in the `skills/` directory:

- **generate-image.skill.md** — Guided single-image generation
- **batch-generate.skill.md** — Batch variant exploration
- **image-studio-workflow.skill.md** — End-to-end pipeline from prompt to publish

Copy these to `~/.hermes/skills/` to load them into Hermes sessions.

## Design

**Zero dependencies.** The plugin uses only Python's built-in libraries —
urllib, sqlite3, json, os, re. No pip installs, no requirements.txt, no
dependency hell. Clone it and it works.

**Safe by design.** If FAL_KEY is not set, the tools simply don't register.
No crashes, no stack traces, no error spam. Set the key when you're ready.

**Standard Hermes architecture.** Follows the same plugin pattern as the
official Spotify and disk-cleanup plugins. Uses `plugin.yaml` + `register(ctx)`
to wire 5 tools into the `image-studio` toolset. Predictable, maintainable,
and compatible with every Hermes version.

### Generation Pipeline

Each image goes through a clean pipeline:

1. Prompt enhanced with the chosen preset's style framing and model selection
2. Sent to the appropriate model endpoint (FLUX or GPT Image via FAL)
3. Downloaded and saved with a descriptive filename
4. Recorded in a local SQLite history database
5. Ready for upscaling or re-generation with a different seed

## License

MIT
