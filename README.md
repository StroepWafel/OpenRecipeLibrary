# Open Recipe Library

A community-maintained collection of recipes in **[Open Recipe Standard](https://github.com/OpenRecipeStandard)** JSON. The default branch holds source files; the **`library`** branch is a generated, browsable tree with a machine-readable index.

## Contributing

1. Add one recipe per file under [`recipes/`](recipes/) (nested folders are fine). Files must be valid JSON with at least `recipe_name`. See the [Open Recipe Standard schema](https://github.com/OpenRecipeStandard) for optional fields such as `categories`, `cor`, `cuisine`, `tags`, `dietary`, `allergens`, and `meal_type`.
2. Open a **pull request** against the default branch (`main` or `master`).

You can author or edit Open Recipe Standard JSON in the browser with **[edit.food-for-eating.com](https://edit.food-for-eating.com)**.

For folder layout on the generated branch, normalization rules, and how recipes are filed by meal type, read **[FILESYSTEM-LAYOUT.md](FILESYSTEM-LAYOUT.md)**.

## Generated `library` branch

GitHub Actions rebuilds the **`library`** branch from `recipes/` when:

- someone pushes to **`main`** or **`master`**, or  
- the **nightly** schedule runs (UTC midnight), or  
- you run the workflow **manually** (Actions → *Organize library branch* → *Run workflow*).

The branch contains `library-list.json` (paths grouped by normalized category, country of recipe, cuisine, tags, and other metadata) and `by-meal/<meal>/` for each recipe file. If the branch does not exist yet, the workflow creates it.

## Local preview

From the repository root, with Python 3 installed:

```bash
python scripts/organize_library.py
```

Output is written to `library-out/` by default (ignored by git). Pass a path to use a different output directory:

```bash
python scripts/organize_library.py /path/to/output
```
