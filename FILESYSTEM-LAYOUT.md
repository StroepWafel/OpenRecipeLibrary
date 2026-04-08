# Filesystem layout (Open Recipe Library)

This repository uses two branches with different roles.

## Default branch (`main` / `master`): source recipes

Contributors add **Open Recipe Standard** JSON files under:

| Path | Purpose |
|------|---------|
| `recipes/` | Any depth; any `*.json` file is picked up recursively. |

Each file must be a JSON object with at least `recipe_name` (see [Open Recipe Standard](https://github.com/OpenRecipeStandard) schema). Optional arrays such as `categories`, `cor`, `cuisine`, `tags`, `dietary`, `allergens`, and `meal_type` drive indexing on the library branch.

## `library` branch: generated, browsable tree

A GitHub Actions workflow rebuilds this branch from `recipes/` on push to the default branch, nightly (UTC), or manual run.

| Path | Purpose |
|------|---------|
| `library-list.json` | Machine-readable index: recipe counts and paths grouped by **normalized** category, cor, cuisine, tag, dietary, allergen, meal type, and skill level. |
| `by-meal/<meal>/` | One copy of each recipe, filed under a **primary meal folder** (see below). |

### Primary meal folder

- If `meal_type` contains values from the schema enum, the folder is the **first** of those values in this fixed order: `breakfast`, `brunch`, `lunch`, `dinner`, `supper`, `snack`, `dessert`, `tea`, `appetizer`, `side`.
- If only non-enum strings appear, the folder name is a slug derived from the first such value (sorted alphabetically).
- If `meal_type` is missing or empty, recipes go under `uncategorized/`.

Recipe filenames are `slugified_recipe_name__<hash>.json` to stay unique and filesystem-safe.

### Normalization in `library-list.json`

String keys used for grouping are **normalized** the same way everywhere: lowercase, trim, and internal whitespace collapsed to a single space. Examples: `SwEEt` and `Swe et` both become the key `sweet`.

### Local preview

From the repo root:

```bash
python scripts/organize_library.py
```

Output defaults to `library-out/` (gitignored if you add it to `.gitignore`).
