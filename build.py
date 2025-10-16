# /// script
# requires-python = "==3.11.*"
# dependencies = [
#     "cookies_site_utils",
# ]
# [tool.uv.sources.cookies_site_utils]
# git = "https://github.com/CookieBox26/cookies-site-utils"
# rev = "e6ebe34079abee4b92b0c6758e4d297be04f63ee"
# ///
from pathlib import Path
import subprocess
from cookies_site_utils import File, Page, IndexPage, Sitemap, validate


def _run(command):
    ret = subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()
    return ret[1:-1] if len(ret) >= 2 and ret[0] == ret[-1] == '"' else ret


if __name__ == '__main__':
    work_root = Path(__file__).resolve().parent
    File.site_root = work_root / 'site'
    File.domain = 'https://cookie-box.info/'
    Page.site_name = 'Cookie Box'
    Page.css_timestamp = '2025-10-09'
    last_counts_path = work_root / '.last_counts.toml'
    Page.load_last_counts(last_counts_path)  # ページ文字数最終更新日をロード

    # 日本語インデックスページ生成
    lang_root = work_root / 'site/ja'
    lang_template_root = work_root / 'templates/ja'
    index_ja = IndexPage(lang_root, lang_template_root)
    validate(lang_root, ['index.html'], ['articles', 'categories'])  # 不要物チェック
    Page.dump_last_counts(last_counts_path)  # ページ文字数最終更新日をダンプ

    # サイトマップ生成
    Sitemap(index_ja.get_pages())
    files_allowed = ['style.css', 'funcs.js', 'robots.txt', 'sitemap.xml']
    subdirs_allowed = ['css', 'ja']
    validate(File.site_root, files_allowed, subdirs_allowed)  # 不要物チェック
    validate(File.site_root / 'css', ['jupyter.css'], [])  # 不要物チェック

    # ローカルと HEAD に差分がないことの確認
    ret = _run(['git', 'status', '-s'])
    if ret != '':
        ret_diff = _run(['git', 'diff', '--name-only'])
        msg = 'Unstaged changes detected' if ret_diff != '' else 'No unstaged changes'
        raise ValueError(f'Differences between HEAD and working tree ({msg})\n{ret}')
