#!/usr/bin/env python3
"""Generate the inline EXERCISES constant for index.html from exercises.json."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "exercises.json"
HTML_PATH = ROOT / "index.html"


def main():
    print(f"Loading {DATA_PATH}...")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        exercises = json.load(f)
    print(f"Loaded {len(exercises)} exercises")

    # Transform: remove es/tr/it, ensure fa fields exist
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

    # Generate inline constant (compact JSON, no indentation)
    inline_json = json.dumps(exercises, ensure_ascii=False, separators=(",", ":"))
    inline_const = f"  const EXERCISES = {inline_json};"

    # Read index.html
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html_lines = f.readlines()

    # Find and replace the EXERCISES constant
    start_idx = None
    end_idx = None
    for i, line in enumerate(html_lines):
        if "const EXERCISES = [" in line:
            start_idx = i
            # Find the closing ]; - it might be on the same line or a subsequent line
            if "];" in line:
                end_idx = i
            else:
                for j in range(i + 1, len(html_lines)):
                    if "];" in html_lines[j]:
                        end_idx = j
                        break
            break

    if start_idx is None:
        print("Error: Could not find 'const EXERCISES' in index.html")
        sys.exit(1)

    print(f"Replacing lines {start_idx + 1} to {end_idx + 1} in index.html")

    # Replace the lines
    new_lines = html_lines[:start_idx] + [inline_const + "\n"] + html_lines[end_idx + 1:]

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"Done! Updated inline EXERCISES constant in {HTML_PATH}")
    print(f"Constant size: {len(inline_const):,} characters")


if __name__ == "__main__":
    main()
