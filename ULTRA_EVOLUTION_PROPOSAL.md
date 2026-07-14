# Ultra Evolution Proposal

## Status and current limitation

This document proposes an upstream Codex custom-pet capability. It is not implemented by this repository or by the current Codex custom-pet loader.

Today, one custom pet manifest resolves to one PNG or WebP spritesheet through `spritesheetPath`. The renderer receives that single atlas and chooses animation rows from task status such as idle, running, waiting, failed, and review. It does not expose the active task's reasoning effort to custom pets, and it has no evolution event or alternate-atlas field.

The Ultra images on the showcase site are therefore visual studies. They cannot activate automatically when a user selects Ultra reasoning mode.

## Backwards-compatible v3 shape

Keep `spriteVersionNumber` focused on atlas geometry. Add a separate `manifestVersion` so existing v2 atlases remain valid and older clients can continue reading `spritesheetPath` as the default form.

```json
{
  "id": "frostbyte",
  "displayName": "Frostbyte",
  "description": "A cool-headed crystal companion for precise, patient work.",
  "manifestVersion": 3,
  "spriteVersionNumber": 2,
  "spritesheetPath": "spritesheet.webp",
  "variants": {
    "ultra": {
      "spriteVersionNumber": 2,
      "spritesheetPath": "spritesheet-ultra.webp"
    }
  },
  "events": [
    {
      "on": "reasoning.effort.changed",
      "when": { "effort": "ultra" },
      "setVariant": "ultra",
      "transition": "evolve"
    },
    {
      "on": "reasoning.effort.changed",
      "when": { "effort": { "not": "ultra" } },
      "setVariant": "default",
      "transition": "settle"
    }
  ],
  "motion": {
    "evolve": {
      "durationMs": 760,
      "reducedMotion": "crossfade"
    },
    "ambient": {
      "playOn": "variant.enter",
      "userControllable": true,
      "maxDurationMs": 11000
    }
  }
}
```

### Compatibility rules

- `spritesheetPath` remains required and is always the default fallback.
- Clients that do not understand `manifestVersion: 3` ignore the new fields and display the default atlas.
- A v3-aware client validates every declared variant with the same MIME, dimensions, path-safety, and file-size rules as the default atlas.
- Variant paths remain local to the installed pet directory. Runtime remote fetching is not allowed.
- An unknown event, condition, transition, or variant is ignored without preventing the default pet from loading.
- The renderer switches assets without changing the current semantic animation row or v2 look-direction behavior.

## Event and privacy behavior

`reasoning.effort.changed` should expose only a small enum for the active task, not prompt content, model internals, hidden reasoning, or tokens. The event should be delivered only to the selected local renderer and should not be persisted in the pet manifest or sent to external code.

When a task changes away from Ultra, closes, or loses active status, the pet returns to `default`. Errors while loading a variant also return to `default`.

## Motion behavior

- Evolution is a short, bounded transition that preserves the current animation state.
- Ambient effects play once when Ultra appears, have a visible stop/replay control, and settle after at most 12 seconds unless the user explicitly replays them.
- Ambient playback stops when the task becomes inactive, the pet changes form, or the page/app loses the relevant pet surface.
- With `prefers-reduced-motion`, form changes use an immediate swap or brief crossfade. No rotation, scale contraction, rapid translation, strobe, or repeated flash runs.
- Flash luminance and frequency must satisfy WCAG guidance and avoid rapid repeated full-screen flashes.

## Acceptance criteria

- Existing v1 and v2 custom pets install and render unchanged.
- An older client can install a v3 manifest and reliably show `spritesheetPath` as the default form.
- A v3 client rejects a malformed variant without rejecting a valid default atlas.
- Every variant is independently validated as a supported PNG or WebP atlas with safe local paths.
- Selecting Ultra for the active task changes only the selected pet to the `ultra` variant.
- Switching reasoning effort, active task, or selected pet restores the correct form without stale cached art.
- Variant changes preserve the current semantic row and pointer look direction.
- Reduced-motion users receive no rotational, vanish, contraction, or strobe sequence.
- Ambient playback has a clear on/off control and stops automatically within 12 seconds.
- No event exposes prompts, hidden reasoning, task text, or other user content.
- Missing files, unknown events, and interrupted transitions always fall back to the default pet without crashing the overlay.
