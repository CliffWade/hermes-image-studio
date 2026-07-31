# Hermes Image Studio

![Hero](hero.png)

**AI image generation plugin for [Hermes Agent](https://hermes-agent.nousresearch.com).**
11 style presets across 9 FLUX, GPT Image, and Nano Banana models. Negative prompts, social-ready sizes, prompt library, web gallery, cost tracking, auto-upscaling, and editing, all through FAL.ai.

Generate publish-ready images for social media, articles, and creative projects
directly from your Hermes conversations. No running to another tool.

## Features

- **8 FLUX Presets** — Cinematic, photorealistic, vintage, fantasy, illustration,
  minimalist, noir, and studio for FLUX models. Each preset tunes prompt phrasing,
  inference steps, and model selection for consistent visual results.
- **2 GPT Presets** — `gpt-photo` for text rendering and complex multi-subject
  scenes (GPT Image 1.5), and `gpt-art` for creative and stylized interpretation
  (GPT Image 2).
- **1 Nano Banana Preset** — `banana-photo` for photorealistic detail, accurate
  text rendering, and natural-language edits (Nano Banana 2).
- **9 Models** — FLUX Pro, FLUX 2 Klein 9B, FLUX 2 Pro, GPT Image 1.5, GPT Image 2,
  Nano Banana 2, Nano Banana Pro, Clarity Upscaler, and the legacy FLUX Klein v1 for compatibility.
- **Negative Prompts** — Tell the model what to avoid: "no people, no text, no watermark."
- **Social-Ready Sizes** — Generate directly at Twitter post/header, Instagram story/post,
  and YouTube thumbnail dimensions.
- **Auto-Upscaling** — Every image can be 2x upscaled with a single command.
- **Image-to-Image Editing** — Transform any generated image with a new prompt using GPT Image 1.5. "Turn this photo into a watercolor painting" or "Add a dirt path leading to the door."
- **Prompt Library** — Save your best prompts by name and regenerate them anytime.
- **Web Gallery** — Generate a self-contained HTML gallery of everything you've created,
  filterable by preset and model.
- **Cost Tracking** — Every generation records its estimated FAL cost. See spend per batch
  and in total.
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

The plugin registers 11 tools into the `image-studio` toolset:

| Tool | What it does |
|------|-------------|
| `image_studio_generate` | Generate an image with a style preset, negative prompt, and social size |
| `image_studio_edit` | Edit an existing image with a new prompt (img2img) |
| `image_studio_upscale` | 2x upscale any generated image |
| `image_studio_batch` | Generate N variants with random seeds |
| `image_studio_presets` | List all available presets with descriptions |
| `image_studio_gallery` | Generate a self-contained HTML gallery of all your images |
| `image_studio_save_prompt` | Save a prompt to the library by name |
| `image_studio_load_prompt` | Generate from a saved prompt by name |
| `image_studio_prompts` | List the prompt library |
| `image_studio_delete_prompt` | Remove a saved prompt |
| `image_studio_history` | Browse recent generations with cost tracking |

### Quick Examples

```text
# Generate a cinematic landscape
image_studio_generate(prompt="A lone cowboy riding through Monument Valley at sunrise, warm golden light, dust kicking up", preset="cinematic", aspect_ratio="landscape")

# Generate with a negative prompt (FLUX models)
image_studio_generate(prompt="A sunset over the ocean", negative_prompt="no people, no boats, no text")

# Generate at Twitter-post size (1200x675)
image_studio_generate(prompt="A product shot for a launch tweet", preset="studio", aspect_ratio="twitter-post")

# Edit that image (transform it with a new prompt)
image_studio_edit(image_url="https://...from-above-generation...", prompt="Add a herd of wild horses in the distance, thunderstorm brewing on the horizon")

# Save a prompt for reuse
image_studio_save_prompt(name="desert-sunrise", prompt="A lone cowboy riding through Monument Valley at sunrise", preset="vintage")

# Generate from a saved prompt
image_studio_load_prompt(name="desert-sunrise")

# List saved prompts
image_studio_prompts

# Batch 4 variants
image_studio_batch(prompt="A futuristic cityscape at night with neon lights", preset="fantasy", count=4)

# Upscale the result
image_studio_upscale(image_url="https://...")

# Build the web gallery
image_studio_gallery

# Check history with cost
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
| `banana-photo` | Photorealism, text rendering, natural-language edits | auto | Nano Banana 2 |

## Social Aspect Ratios

Use these aliases for platform-ready output sizes (FLUX models render exact dimensions):

| Alias | Size | For |
|-------|------|-----|
| `twitter-post` (or `x-post`, `social`) | 1200x675 | Standard tweet image |
| `twitter-header` (or `x-header`, `banner`) | 1500x500 | Profile banner |
| `instagram-post` (or `ig-post`) | 1080x1080 | Feed square |
| `instagram-story` (or `story`) | 1080x1920 | Story / Reels cover |
| `youtube-thumb` (or `yt`) | 1280x720 | Video thumbnail |

Non-FLUX models (GPT Image, Nano Banana) fall back to the closest standard ratio.

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
2. Sent to the appropriate model endpoint (FLUX, GPT Image, or GPT Image edit via FAL)
3. Downloaded and saved with a descriptive filename
4. Recorded in a local SQLite history database
5. Ready for editing, upscaling, or re-generation with a different seed

## License

MIT
