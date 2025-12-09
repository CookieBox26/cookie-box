# /// script
# requires-python = "==3.11.*"
# dependencies = [
#     "cookies_site_utils",
# ]
# [tool.uv.sources.cookies_site_utils]
# git = "https://github.com/CookieBox26/cookies-site-utils"
# rev = "2a8229580bc1c7192925c0dd88166a8633a24d52"
# ///
from pathlib import Path
import subprocess
from cookies_site_utils import index_generation, IndexPage, Sitemap, validate


if __name__ == '__main__':
    work_root = Path(__file__).resolve().parent
    site_root = work_root / 'site'
    style_css = site_root / 'css/style.css'
    funcs_js = site_root / 'funcs.js'
    last_counts_path = work_root / '.last_counts.toml'
    domain = 'https://cookie-box.info/'

    with index_generation(
        site_root, style_css, funcs_js, last_counts_path, domain,
        force_keep_timestamp=True,  # CSS, JS のメンテナンスだけで記事内容の更新がない時 True に
    ):
        # クッキパッドインデックスページ生成
        subsite_root = site_root / 'cookiepad'
        subsite_template_root = work_root / 'templates/cookiepad'
        subsite_name = 'Cookiepad'
        index_cookiepad = IndexPage(subsite_root)
        index_cookiepad.build(subsite_template_root, subsite_name)
        validate(subsite_root, ['index.html'], ['articles', 'categories'])

        # 総合インデックスページ作成
        site_name = 'Cookie Box'
        index_ = IndexPage(site_root)
        index_.eval(site_name)
        validate(site_root, ['index.html', 'funcs.js', 'robots.txt', 'sitemap.xml'], ['css', 'cookiepad'])
        validate(site_root / 'css', ['style.css', 'cookie-box.css', 'cookiepad.css', 'jupyter.css'], [])

        # サイトマップ生成
        Sitemap([index_] + index_cookiepad.get_pages())

    # ローカルと HEAD に差分がないことの確認
    _run = lambda command: subprocess.run(command, capture_output=True, text=True, check=True)
    ret = _run(['git', 'status', '-s']).stdout.rstrip('\n')
    if ret != '':
        ret_diff = _run(['git', 'diff', '--name-only']).stdout.rstrip('\n')
        msg = 'Unstaged changes detected' if ret_diff != '' else 'No unstaged changes'
        raise ValueError(f'Differences between HEAD and working tree ({msg})\n{ret}')
