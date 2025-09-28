# Cookie Box

[https://cookie-box.info/](https://cookie-box.info/)

## Article Update Procedure

### Add or Edit Articles

Create or modify the file at `site/ja/articles/xxxxxx.html`.

### Build Index and Sitemap

Run the following command to update the index and sitemap based on the articles:
```bash
uv run build.py
```
If [uv](https://docs.astral.sh/uv/) is not available, install the required dependencies using another method.

If you ever need to remove the virtual environment created by uv, run:
```
uv sync --script build.py
```
It will print the environment path. Delete that path manually.
