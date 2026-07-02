#!/usr/bin/env python3
"""Translate remaining exercises using Google Translate (fallback)."""

import json
import sys
import time
from pathlib import Path

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("Error: pip install deep-translator")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT / "data" / "exercises.json"
PROGRESS_PATH = ROOT / "scripts" / "translate_progress.json"


def load_progress():
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            return set(json.load(f).get("completed_ids", []))
    return set()


def save_progress(ids):
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump({"completed_ids": sorted(ids)}, f, ensure_ascii=False)


def translate_text(translator, text, retries=3):
    if not text or not text.strip():
        return ""
    for attempt in range(retries):
        try:
            result = translator.translate(text)
            return result if result else ""
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return "[ترجمه ناموفق]"
    return ""


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        exercises = json.load(f)

    completed = load_progress()
    todo = [ex for ex in exercises if ex["id"] not in completed]
    print(f"Total: {len(exercises)}, Done: {len(completed)}, Remaining: {len(todo)}")

    if not todo:
        print("All done!")
        return

    translator = GoogleTranslator(source='en', target='fa')
    exercises_by_id = {ex["id"]: ex for ex in exercises}

    for i, ex in enumerate(todo):
        ex_id = ex["id"]
        print(f"[{i+1}/{len(todo)}] {ex_id}: {ex['name']}...")

        ex["name_fa"] = translate_text(translator, ex["name"])
        ex["instructions"]["fa"] = translate_text(translator, ex["instructions"].get("en", ""))

        steps = ex["instruction_steps"].get("en", [])
        if steps:
            ex["instruction_steps"]["fa"] = [translate_text(translator, s) for s in steps]
        else:
            ex["instruction_steps"]["fa"] = []

        completed.add(ex_id)

        if (i + 1) % 10 == 0 or i == len(todo) - 1:
            save_progress(completed)
            with open(INPUT_PATH, "w", encoding="utf-8") as f:
                json.dump(exercises, f, ensure_ascii=False, indent=2)
            print(f"  Saved ({len(completed)}/{len(exercises)})")

        time.sleep(0.5)

    print(f"\nDone! {len(completed)}/{len(exercises)} translated.")


if __name__ == "__main__":
    main()
