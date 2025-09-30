# Cookie Box

[https://cookie-box.info/ja/index.html](https://cookie-box.info/ja/index.html)

## Article Update Procedure

### Add or Edit Articles

Create or modify the file at `site/ja/articles/xxxxxx.html`.

### Build Index and Sitemap

Run the following command to update the index and sitemap based on the articles:
```bash
uv run build.py
```
- If [uv](https://docs.astral.sh/uv/) is not available, install dependencies manually.
- `build.py` synchronizes the index and sitemap with articles and verifies the following; correct any errors before committing:
  - HTML files have no rule violations
  - No unnecessary files exist under `site/`
  - Working tree matches the HEAD commit
    - Before committing, there will always be differences, so it is sufficient as long as there are no unstaged changes.
- `build.py` also runs on push. If it fails, fix the errors.

### Note

If you ever need to remove the virtual environment created by uv, run:
```
uv sync --script build.py
```
It will print the environment path. Delete that path manually.
