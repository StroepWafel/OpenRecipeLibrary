#!/usr/bin/env python3
"""
Build the library branch layout from recipes/**/*.json (Open Recipe Standard).
Writes by-meal/<meal>/<slug>.json and library-list.json at OUTPUT_ROOT.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Must match schemas/open-recipe.schema.json MealType enum (order = primary-meal pick order)
MEAL_ORDER = [
    "breakfast",
    "brunch",
    "lunch",
    "dinner",
    "supper",
    "snack",
    "dessert",
    "tea",
    "appetizer",
    "side",
]
MEAL_SET = set(MEAL_ORDER)


def normalize_label(s: str) -> str:
    """Normalize for matching: lowercase, collapse internal whitespace."""
    if not s or not isinstance(s, str):
        return ""
    return " ".join(s.lower().split())


def slug_for_path(s: str) -> str:
    """Filesystem-safe slug (ASCII, underscores)."""
    n = normalize_label(s)
    n = re.sub(r"\s+", "_", n)
    n = re.sub(r"[^a-z0-9_]+", "", n)
    return n or "unknown"


def recipe_file_slug(name: str, unique: str) -> str:
    base = slug_for_path(name)
    if len(base) > 100:
        base = base[:100].rstrip("_")
    h = hashlib.sha256(unique.encode("utf-8")).hexdigest()[:8]
    return f"{base}__{h}.json"


def primary_meal_folder(meal_type: Any) -> str:
    if not meal_type or not isinstance(meal_type, list):
        return "uncategorized"
    raw = [normalize_label(str(x)) for x in meal_type if x]
    present = [m for m in MEAL_ORDER if m in raw]
    if present:
        return present[0]
    # Non-enum values: first after sort for stability
    extras = sorted({m for m in raw if m not in MEAL_SET})
    if extras:
        return slug_for_path(extras[0])
    return "uncategorized"


def load_recipe(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print(f"Warning: skip invalid JSON: {path}", file=sys.stderr)
        return None
    if not isinstance(data, dict) or "recipe_name" not in data:
        print(f"Warning: skip (missing recipe_name): {path}", file=sys.stderr)
        return None
    return data


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    recipes_root = repo_root / "recipes"
    out_root = repo_root / "library-out"

    if len(sys.argv) >= 2:
        out_root = Path(sys.argv[1]).resolve()

    out_root.mkdir(parents=True, exist_ok=True)
    by_meal = out_root / "by-meal"
    if by_meal.exists():
        for child in by_meal.iterdir():
            if child.is_dir():
                for f in child.glob("*.json"):
                    f.unlink()
    by_meal.mkdir(parents=True, exist_ok=True)

    # Index: normalized_key -> list of relative paths
    by_category: dict[str, list[str]] = defaultdict(list)
    by_cor: dict[str, list[str]] = defaultdict(list)
    by_cuisine: dict[str, list[str]] = defaultdict(list)
    by_tag: dict[str, list[str]] = defaultdict(list)
    by_dietary: dict[str, list[str]] = defaultdict(list)
    by_allergen: dict[str, list[str]] = defaultdict(list)
    by_meal_type: dict[str, list[str]] = defaultdict(list)
    by_skill_level: dict[str, list[str]] = defaultdict(list)

    recipes_seen: list[tuple[Path, dict[str, Any], str]] = []

    if not recipes_root.is_dir():
        print(f"No recipes directory at {recipes_root}", file=sys.stderr)
    else:
        for path in sorted(recipes_root.rglob("*.json")):
            if path.name.startswith("."):
                continue
            data = load_recipe(path)
            if data is None:
                continue
            uid = str(
                data.get("recipe_uuid")
                or hashlib.sha256(path.read_bytes()).hexdigest()
            )
            meal_key = primary_meal_folder(data.get("meal_type"))
            meal_dir = by_meal / meal_key
            meal_dir.mkdir(parents=True, exist_ok=True)
            name = str(data.get("recipe_name", "recipe"))
            dest_name = recipe_file_slug(name, uid)
            dest = meal_dir / dest_name
            # Avoid collision in same folder
            n = 0
            while dest.exists():
                n += 1
                dest = meal_dir / f"{dest_name[:-5]}_{n}.json"
            dest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            lib_rel = dest.relative_to(out_root).as_posix()
            recipes_seen.append((path, data, lib_rel))

    for _src, data, lib_rel in recipes_seen:
        def add_multi(
            field: str,
            bucket: dict[str, list[str]],
        ) -> None:
            vals = data.get(field)
            if not vals or not isinstance(vals, list):
                return
            for item in vals:
                if not item:
                    continue
                k = normalize_label(str(item))
                if k:
                    bucket[k].append(lib_rel)

        add_multi("categories", by_category)
        add_multi("cor", by_cor)
        add_multi("cuisine", by_cuisine)
        add_multi("tags", by_tag)
        add_multi("dietary", by_dietary)
        add_multi("allergens", by_allergen)

        mt = data.get("meal_type")
        if isinstance(mt, list):
            for m in mt:
                if not m:
                    continue
                k = normalize_label(str(m))
                if k:
                    by_meal_type[k].append(lib_rel)

        sk = data.get("skill_level")
        if isinstance(sk, str) and sk.strip():
            k = normalize_label(sk)
            by_skill_level[k].append(lib_rel)

    def sort_map(m: dict[str, list[str]]) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for key in sorted(m.keys()):
            out[key] = sorted(set(m[key]))
        return out

    catalog = {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "recipe_count": len(recipes_seen),
        "normalization": "Labels are matched after lowercasing and collapsing internal whitespace (e.g. 'SwEEt' and 'Swe et' both map to key 'sweet').",
        "by_category": sort_map(by_category),
        "by_cor": sort_map(by_cor),
        "by_cuisine": sort_map(by_cuisine),
        "by_tag": sort_map(by_tag),
        "by_dietary": sort_map(by_dietary),
        "by_allergen": sort_map(by_allergen),
        "by_meal_type": sort_map(by_meal_type),
        "by_skill_level": sort_map(by_skill_level),
    }

    (out_root / "library-list.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(recipes_seen)} recipe(s) to {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
