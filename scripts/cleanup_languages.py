#!/usr/bin/env python3
"""Remove es/tr/it language keys from exercises.json, keeping only en and fa."""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "exercises.json"
BACKUP_PATH = ROOT / "data" / "exercises_backup.json"

REMOVE_LANGS = {"es", "tr", "it"}


def main():
    print(f"Loading {DATA_PATH}...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        exercises = json.load(f)
    print(f"Loaded {len(exercises)} exercises")

    # Create backup
    print(f"Creating backup at {BACKUP_PATH}...")
    shutil.copy2(str(DATA_PATH), str(BACKUP_PATH))

    # Clean up languages
    modified = 0
    for ex in exercises:
        changed = False
        for field in ("instructions", "instruction_steps"):
            if field in ex:
                for lang in REMOVE_LANGS:
                    if lang in ex[field]:
                        del ex[field][lang]
                        changed = True
        if changed:
            modified += 1

    # Validate
    for ex in exercises:
        instr_keys = set(ex.get("instructions", {}).keys())
        steps_keys = set(ex.get("instruction_steps", {}).keys())
        assert instr_keys <= {"en", "fa"}, f"Exercise {ex['id']} has unexpected instruction keys: {instr_keys}"
        assert steps_keys <= {"en", "fa"}, f"Exercise {ex['id']} has unexpected step keys: {steps_keys}"

    # Save
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(exercises, f, ensure_ascii=False, indent=2)

    print(f"Done! Modified {modified} exercises.")
    print(f"Removed languages: {', '.join(sorted(REMOVE_LANGS))}")
    print(f"Backup saved at: {BACKUP_PATH}")


if __name__ == "__main__":
    main()
