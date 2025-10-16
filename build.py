# /// script
# requires-python = "==3.11.*"
# dependencies = [
#     "cookies_site_utils",
# ]
# [tool.uv.sources.cookies_site_utils]
# git = "https://github.com/CookieBox26/cookies-site-utils"
# rev = "a916109b8eaf66aaa47323e94fe6dac6283feddf"
# ///
from pathlib import Path
import subprocess
from cookies_site_utils import IndexPage, CategoryPage, Sitemap, validate, index_generation_context


def _run(command):
    ret = subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()
    return ret[1:-1] if len(ret) >= 2 and ret[0] == ret[-1] == '"' else ret


if __name__ == '__main__':
    site_name = 'Cookie Box'
    domain = 'https://cookie-box.info/'
    work_root = Path(__file__).resolve().parent
    site_root = work_root / 'site'
    lang_root = work_root / 'site/ja'
    lang_template_root = work_root / 'templates/ja'
    last_counts_path = work_root / '.last_counts.toml'
    IndexPage.additional_context = CategoryPage.additional_context = {'css_timestamp': '2025-10-09'}

    with index_generation_context(site_root, site_name, last_counts_path, domain):
        # 日本語インデックスページ生成
        index_ja = IndexPage(lang_root, lang_template_root)
        # サイトマップ生成
        Sitemap(index_ja.get_pages())

    # 不要物チェック
    validate(lang_root, ['index.html'], ['articles', 'categories'])
    validate(site_root, ['style.css', 'funcs.js', 'robots.txt', 'sitemap.xml'], ['css', 'ja'])
    validate(site_root / 'css', ['jupyter.css'], [])

    # ローカルと HEAD に差分がないことの確認
    ret = _run(['git', 'status', '-s'])
    if ret != '':
        ret_diff = _run(['git', 'diff', '--name-only'])
        msg = 'Unstaged changes detected' if ret_diff != '' else 'No unstaged changes'
        raise ValueError(f'Differences between HEAD and working tree ({msg})\n{ret}')
