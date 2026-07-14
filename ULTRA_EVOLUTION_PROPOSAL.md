# Ultra Evolved Forms Proposal

## Status and current limitation

This document proposes an upstream Codex custom-pet capability. It is not implemented by this repository or by the current Codex custom-pet loader.

Today, one custom pet manifest resolves to one PNG or WebP spritesheet through `spritesheetPath`. The renderer receives that single atlas and chooses animation rows from task status such as idle, running, waiting, failed, and review. It does not expose the active task's reasoning effort to custom pets, and it has no evolved-form event or alternate-form field.

The Ultra images on the showcase site are therefore visual studies. They cannot activate automatically when a user selects Ultra reasoning mode.

## Backwards-compatible v3 shape

Keep `spriteVersionNumber` focused on the animated default atlas. Add a separate `manifestVersion` and an explicitly static variant so existing v2 pets remain valid and older clients can continue reading `spritesheetPath` as the default form.

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
      "renderMode": "static",
      "imagePath": "frostbyte-ultra.png"
    }
  },
  "events": [
    {
      "on": "reasoning.effort.changed",
      "when": { "effort": "ultra" },
      "setVariant": "ultra"
    },
    {
      "on": "reasoning.effort.changed",
      "when": { "effort": { "not": "ultra" } },
      "setVariant": "default"
    }
  ]
}
```

### Compatibility rules

- `spritesheetPath` remains required and is always the default fallback.
- Clients that do not understand `manifestVersion: 3` ignore the new fields and display the default atlas.
- A v3-aware client validates a static variant as a transparent PNG or WebP image with bounded dimensions, safe paths, and the same file-size ceiling as other pet assets.
- Variant paths remain local to the installed pet directory. Runtime remote fetching is not allowed.
- An unknown event, condition, or variant is ignored without preventing the default pet from loading.
- While the static variant is selected, task-state rows and pointer look directions do not animate or alter the displayed evolved image.
- Variant changes are immediate and non-animated. The evolved-form feature defines no transition or ambient-effect field.

## Event and privacy behavior

`reasoning.effort.changed` should expose only a small enum for the active task, not prompt content, model internals, hidden reasoning, or tokens. The event should be delivered only to the selected local renderer and should not be persisted in the pet manifest or sent to external code.

When a task changes away from Ultra, closes, or loses active status, the pet returns to `default`. Errors while loading a variant also return to `default`.

## Form-swap behavior

- Selecting Ultra immediately replaces the animated default pet with its static evolved-form image.
- Switching away from Ultra immediately restores the default atlas.
- The form change has no transformation sequence, crossfade, rotation, contraction, translation, flash, or ambient effect.
- Task state may continue updating internally while the static form is visible; returning to the default form resumes at the current state.

## Acceptance criteria

- Existing v1 and v2 custom pets install and render unchanged.
- An older client can install a v3 manifest and reliably show `spritesheetPath` as the default form.
- A v3 client rejects a malformed static variant without rejecting a valid default atlas.
- Every static variant is independently validated as a supported transparent PNG or WebP image with a safe local path.
- Selecting Ultra for the active task changes only the selected pet to the `ultra` variant.
- Switching reasoning effort, active task, or selected pet restores the correct form without stale cached art.
- The evolved image remains visually unchanged when task state or pointer direction changes.
- Variant changes are immediate and non-animated for every user.
- The evolved-form feature exposes no transition, ambient-effect, playback, or timing controls.
- No event exposes prompts, hidden reasoning, task text, or other user content.
- Missing files and unknown events always fall back to the default pet without crashing the overlay.
