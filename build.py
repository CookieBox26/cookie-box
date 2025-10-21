# /// script
# requires-python = "==3.11.*"
# dependencies = [
#     "cookies_site_utils",
# ]
# [tool.uv.sources.cookies_site_utils]
# git = "https://github.com/CookieBox26/cookies-site-utils"
# rev = "9c7b6b822e9f6eea26de0f9209de0062d5457113"
# ///
from pathlib import Path
import subprocess
from cookies_site_utils import index_generation, IndexPage, Sitemap, validate


if __name__ == '__main__':
    site_name = 'Cookie Box'
    work_root = Path(__file__).resolve().parent
    site_root = work_root / 'site'
    style_css = site_root / 'css/style.css'
    funcs_js = site_root / 'funcs.js'
    lang_root = site_root / 'ja'
    lang_template_root = work_root / 'templates/ja'
    last_counts_path = work_root / '.last_counts.toml'
    domain = 'https://cookie-box.info/'

    with index_generation(
        site_name, site_root, style_css, funcs_js, last_counts_path, domain,
        force_keep_timestamp=False,  # CSS, JS のメンテナンスだけで記事内容の更新がない時 True に
    ):
        # 日本語インデックスページ生成
        index_ja = IndexPage(lang_root, lang_template_root)
        # サイトマップ生成
        Sitemap(index_ja.get_pages())

    # 不要物チェック
    validate(lang_root, ['index.html'], ['articles', 'categories'])
    validate(site_root, ['funcs.js', 'robots.txt', 'sitemap.xml'], ['css', 'ja'])
    validate(site_root / 'css', ['style.css', 'cookie-box.css', 'jupyter.css'], [])

    # ローカルと HEAD に差分がないことの確認
    _run = lambda command: subprocess.run(command, capture_output=True, text=True, check=True)
    ret = _run(['git', 'status', '-s']).stdout.rstrip('\n')
    if ret != '':
        ret_diff = _run(['git', 'diff', '--name-only']).stdout.rstrip('\n')
        msg = 'Unstaged changes detected' if ret_diff != '' else 'No unstaged changes'
        raise ValueError(f'Differences between HEAD and working tree ({msg})\n{ret}')
