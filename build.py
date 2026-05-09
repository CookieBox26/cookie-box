# /// script
# requires-python = "==3.11.*"
# dependencies = [
#     "cookies_site_utils",
# ]
# [tool.uv.sources.cookies_site_utils]
# git = "https://github.com/CookieBox26/cookies-site-utils"
# rev = "802b7c4960132b4d9080dab0cd1a9a482a5c5389"
# ///
from cookies_site_utils.resources import sync_resource
from cookies_site_utils.builder \
    import build_index, IndexPage, find_disallowed, Sitemap, Page
from pathlib import Path
import argparse
import subprocess


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--force_keep_timestamp', action='store_true')
    args = parser.parse_args()

    work_root = Path(__file__).resolve().parent
    site_root = work_root / 'site'
    last_counts_path = work_root / '.last_counts.toml'
    domain = 'https://cookie-box.info/'

    sync_resource(site_root / 'css/style.css')
    sync_resource(site_root / 'funcs.js')

    with build_index(
        site_root, last_counts_path, domain=domain,
        force_keep_timestamp=args.force_keep_timestamp,
    ):
        subsite_root = site_root / 'cookiepad'
        index_cookiepad = IndexPage(
            subsite_root,
            work_root / 'templates/cookiepad',
            'Cookiepad',
        )
        find_disallowed(subsite_root, allowlist=[
            'index.html',
            'articles/*.html',
            'categories/*.html',
        ])

        find_disallowed(site_root, allowlist=[
            'robots.txt',
            'sitemap.xml',
            'index.html',
            'funcs.js',
            'css/style.css',
            'css/cookie-box.css',
            'css/cookiepad.css',
            'css/cookipedia.css',
            'css/jupyter.css',
            'cookiepad/*',
            'cookipedia/*',
        ])
        index_ = Page(site_root / 'index.html')
        index_.eval()
        Sitemap(
            [index_] + index_cookiepad.get_pages()
        )

        targets = set()
        for rel_path in Page.last_counts.keys():
            if not (site_root / rel_path).is_file():
                logging.info('Not exist: ' + rel_path)
                targets.add(rel_path)
        Page.last_counts = {
            k: v for k, v in Page.last_counts.items()
            if k not in targets
        }

    _run = lambda command: subprocess.run(command, capture_output=True, text=True, check=True)
    ret = _run(['git', 'status', '-s']).stdout.rstrip('\n')
    if ret != '':
        ret_diff = _run(['git', 'diff', '--name-only']).stdout.rstrip('\n')
        msg = 'Unstaged changes detected' if ret_diff != '' else 'No unstaged changes'
        raise ValueError(f'Differences between HEAD and working tree ({msg})\n{ret}')
