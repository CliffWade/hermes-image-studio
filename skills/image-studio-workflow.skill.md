---
name: image-studio-workflow
description: "Full image creation workflow using Hermes Image Studio. Guides the agent through prompt engineering, preset selection, generation, upscaling, and batch exploration."
---

# Image Studio: Full Workflow

End-to-end skill for producing publish-ready images using the Hermes
Image Studio plugin (tools: `image_studio_presets`,
`image_studio_generate`, `image_studio_batch`, `image_studio_upscale`,
`image_studio_history`).

## The Pipeline

### Phase 1: Discovery

Start with `image_studio_presets` if the user hasn't picked a style.
Discuss:
- What is the image for? (Twitter, article header, personal project)
- What mood or era fits the subject?
- Would a specific preset serve the purpose?

### Phase 2: Generate

Write a specific, detailed prompt. Generic prompts produce generic
results. Include:
- Subject and action
- Setting and environment
- Lighting and time of day
- Colors and mood
- Composition (wide shot, close-up, portrait)

Call `image_studio_generate` with the prompt and chosen preset.

### Phase 3: Evaluate (Optional)

If the result needs refinement:
- Change the preset for a different visual style
- Add more detail to the prompt for specificity
- Use a specific seed to lock composition while changing the prompt

### Phase 4: Batch (Optional)

If the user wants options, run `image_studio_batch` with count=4.
Present all variants and pick the strongest direction.

### Phase 5: Upscale (Final Step)

For the final selected image, run `image_studio_upscale` with the
image URL from the generation. This produces a 2x higher resolution
version suitable for Twitter, printing, or publication.

### Phase 6: Deliver

Confirm the final file path and seed so the user can reference or
re-generate later. The image is already saved to the configured output
directory.

## Quick Reference

```
Step                  Tool                          When
-----                ----                          ----
Pick a preset        image_studio_presets           Always start here
Generate             image_studio_generate          One shot
Explore variants     image_studio_batch count=4     User wants options
Upscale final        image_studio_upscale           Before publishing
Browse history       image_studio_history           Re-find or tweak past work
```

## Output Location

All images are saved to `/Volumes/Spare Drive/Personal Stuff/Image Studio/`
by default, organized by date in the filename:
`YYYYMMDD_HHMMSS_preset_seed_subject.png`
