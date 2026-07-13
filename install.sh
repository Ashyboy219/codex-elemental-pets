#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CODEX_PETS_DIR="${CODEX_HOME:-$HOME/.codex}/pets"

for pet in frostbyte bolt; do
  source_dir="$ROOT/pets/$pet"
  destination="$CODEX_PETS_DIR/$pet"
  test -f "$source_dir/pet.json"
  test -f "$source_dir/spritesheet.webp"
  mkdir -p "$destination"
  cp "$source_dir/pet.json" "$source_dir/spritesheet.webp" "$destination/"
  echo "Installed $pet → $destination"
done

echo "Restart Codex if the new pets do not appear immediately."
