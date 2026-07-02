#!/usr/bin/env python3
"""Prepare exercises.json structure: remove es/tr/it, add empty fa fields."""

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "exercises.json"
BACKUP_PATH = ROOT / "data" / "exercises_backup.json"


def main():
    print(f"Loading {DATA_PATH}...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        exercises = json.load(f)
    print(f"Loaded {len(exercises)} exercises")

    # Create backup
    print(f"Creating backup at {BACKUP_PATH}...")
    shutil.copy2(str(DATA_PATH), str(BACKUP_PATH))

    # Transform
    for ex in exercises:
        # Remove unwanted languages from instructions
        if "instructions" in ex:
            for lang in ("es", "tr", "it"):
                ex["instructions"].pop(lang, None)
            if "fa" not in ex["instructions"]:
                ex["instructions"]["fa"] = ""

        # Remove unwanted languages from instruction_steps
        if "instruction_steps" in ex:
            for lang in ("es", "tr", "it"):
                ex["instruction_steps"].pop(lang, None)
            if "fa" not in ex["instruction_steps"]:
                ex["instruction_steps"]["fa"] = []

        # Ensure name_fa exists
        if "name_fa" not in ex:
            ex["name_fa"] = ""

    # Save
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(exercises, f, ensure_ascii=False, indent=2)

    print(f"Done! Updated {len(exercises)} exercises")
    print(f"Removed: es, tr, it")
    print(f"Added: empty fa fields, name_fa")
    print(f"Backup saved at: {BACKUP_PATH}")


if __name__ == "__main__":
    main()
