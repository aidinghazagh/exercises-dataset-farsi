#!/usr/bin/env python3
"""Translate exercise names, instructions, and instruction_steps to Farsi using OpenAI-compatible API."""

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed. Run: pip install openai")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT / "data" / "exercises.json"
PROGRESS_PATH = ROOT / "scripts" / "translate_progress.json"

SYSTEM_PROMPT = """You are an expert fitness translator. Translate exercise names and instructions from English to Farsi (Persian).

Rules:
- Use standard Persian fitness terminology
- Keep proper form descriptions accurate and natural in Farsi
- Use formal but accessible Persian (not colloquial)
- Preserve any numeric values (angles, degrees, counts) as-is
- Return ONLY valid JSON, no markdown fences, no extra text"""


def build_batch_prompt(exercises: list[dict]) -> str:
    """Build a prompt for a batch of exercises."""
    items = []
    for ex in exercises:
        items.append({
            "id": ex["id"],
            "name": ex["name"],
            "category": ex.get("category", ""),
            "equipment": ex.get("equipment", ""),
            "target": ex.get("target", ""),
            "instructions_en": ex.get("instructions", {}).get("en", ""),
            "instruction_steps_en": ex.get("instruction_steps", {}).get("en", []),
        })

    return f"""Translate these {len(items)} exercises to Farsi.

For EACH exercise, return a JSON object with:
- id: same as input
- name_fa: Farsi translation of the exercise name
- instructions_fa: Farsi translation of the full instruction paragraph
- instruction_steps_fa: array of Farsi translations of each step (same order)

Return a JSON array of {len(items)} objects. No markdown fences.

Exercises:
{json.dumps(items, ensure_ascii=False, indent=2)}"""


def load_progress() -> set:
    """Load set of already-translated exercise IDs."""
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("completed_ids", []))
    return set()


def save_progress(completed_ids: set):
    """Save progress of completed exercise IDs."""
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump({"completed_ids": sorted(completed_ids)}, f, ensure_ascii=False)


def atomic_save_json(path: Path, data):
    """Save JSON atomically using tempfile + os.replace."""
    dir_path = path.parent
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=dir_path, suffix=".json", delete=False
    ) as tmp:
        tmp_path = tmp.name
        json.dump(data, tmp, ensure_ascii=False, indent=2)
    os.replace(tmp_path, str(path))


def translate_batch(client: OpenAI, model: str, exercises: list[dict], retries: int = 5) -> list[dict]:
    """Translate a batch of exercises using the LLM API."""
    prompt = build_batch_prompt(exercises)

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4096,
            )
            break
        except Exception as e:
            if attempt < retries - 1:
                wait = 10 * (attempt + 1)
                print(f"    Retry {attempt+1}/{retries}: {str(e)[:80]}. Waiting {wait}s...")
                time.sleep(wait)
            else:
                raise

    content = response.choices[0].message.content.strip()

    # Strip markdown fences if present
    if content.startswith("```"):
        lines = content.split("\n")
        lines = lines[1:]  # Remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    try:
        results = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  Warning: JSON parse error: {e}")
        print(f"  Raw response (first 500 chars): {content[:500]}")
        raise

    # Validate structure
    if not isinstance(results, list):
        raise ValueError(f"Expected JSON array, got {type(results).__name__}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Translate exercises to Farsi")
    parser.add_argument("--batch-size", type=int, default=5, help="Exercises per API call (default: 5)")
    parser.add_argument("--model", default="mistral-large", help="Model name (default: mistral-large)")
    parser.add_argument("--base-url", default=None, help="API base URL")
    parser.add_argument("--api-key", default=None, help="API key")
    parser.add_argument("--resume", action="store_true", default=True, help="Skip already-translated exercises")
    parser.add_argument("--no-resume", dest="resume", action="store_false", help="Re-translate everything")
    parser.add_argument("--dry-run", action="store_true", help="Preview without API calls")
    args = parser.parse_args()

    # Load exercises
    print(f"Loading exercises from {INPUT_PATH}...")
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        exercises = json.load(f)
    print(f"Loaded {len(exercises)} exercises")

    # Load progress
    completed_ids = load_progress() if args.resume else set()
    if completed_ids:
        print(f"Resuming: {len(completed_ids)} exercises already translated")

    # Filter to untranslated
    todo = [ex for ex in exercises if ex["id"] not in completed_ids]
    print(f"Remaining: {len(todo)} exercises to translate")

    if not todo:
        print("All exercises already translated!")
        return

    if args.dry_run:
        print(f"\n[DRY RUN] Would translate {len(todo)} exercises in batches of {args.batch_size}")
        print(f"First 5: {[ex['name'] for ex in todo[:5]]}")
        return

    # Initialize OpenAI client
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    base_url = args.base_url or os.environ.get("OPENAI_BASE_URL", "https://conduit.ozdoev.net/api/v1")

    if not api_key:
        print("Error: No API key. Set OPENAI_API_KEY env var or use --api-key")
        sys.exit(1)

    from httpx_socks import SyncProxyTransport
    import httpx
    transport = SyncProxyTransport.from_url("socks5://127.0.0.1:10808")
    http_client = httpx.Client(transport=transport, timeout=180.0)
    client = OpenAI(api_key=api_key, base_url=base_url, http_client=http_client, max_retries=0)
    print(f"Using model: {args.model}")
    print(f"Using base URL: {base_url}")

    # Translate in batches
    total_batches = (len(todo) + args.batch_size - 1) // args.batch_size
    exercises_by_id = {ex["id"]: ex for ex in exercises}

    for batch_idx in range(0, len(todo), args.batch_size):
        batch = todo[batch_idx : batch_idx + args.batch_size]
        batch_num = batch_idx // args.batch_size + 1

        print(f"\nBatch {batch_num}/{total_batches} ({len(batch)} exercises)...")
        print(f"  IDs: {[ex['id'] for ex in batch]}")

        try:
            results = translate_batch(client, args.model, batch)

            # Apply translations
            for result in results:
                ex_id = result.get("id")
                if ex_id not in exercises_by_id:
                    print(f"  Warning: unknown ID {ex_id}, skipping")
                    continue

                ex = exercises_by_id[ex_id]
                ex["name_fa"] = result.get("name_fa", "")
                if "instructions" not in ex:
                    ex["instructions"] = {}
                ex["instructions"]["fa"] = result.get("instructions_fa", "")
                if "instruction_steps" not in ex:
                    ex["instruction_steps"] = {}
                ex["instruction_steps"]["fa"] = result.get("instruction_steps_fa", [])
                completed_ids.add(ex_id)

            # Save progress
            save_progress(completed_ids)
            atomic_save_json(INPUT_PATH, exercises)
            print(f"  Saved progress ({len(completed_ids)}/{len(exercises)} done)")

        except Exception as e:
            print(f"  SKIPPED {batch[0]['id']}: {str(e)[:80]}")
            # Mark as done with placeholder to avoid retrying forever
            ex = exercises_by_id[batch[0]["id"]]
            ex["name_fa"] = ex["name"]
            ex["instructions"]["fa"] = ex["instructions"].get("en", "")
            ex["instruction_steps"]["fa"] = ex["instruction_steps"].get("en", [])
            completed_ids.add(batch[0]["id"])
            save_progress(completed_ids)
            atomic_save_json(INPUT_PATH, exercises)

        # Rate limiting (respect 10 req/min = 1 every 6s)
        if batch_idx + args.batch_size < len(todo):
            time.sleep(6)

    print(f"\nDone! Translated {len(completed_ids)} exercises.")
    print(f"Output: {INPUT_PATH}")


if __name__ == "__main__":
    main()
