# /// script
# requires-python = "==3.11.*"
# dependencies = [
#     "beautifulsoup4",
#     "jinja2",
#     "shirotsubaki",
#     "toml",
# ]
# ///

from shirotsubaki.element import Element as Elm
from jinja2 import Template
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import toml
import os


def _run(command):
    ret = subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()
    return ret[1:-1] if len(ret) >= 2 and ret[0] == ret[-1] == '"' else ret


def _write_text(path, text):
    if path.exists():
        current_text = path.read_text(encoding='utf8')
        if current_text == text:
            print(f'更新なし {path}')
            return
        print(f'更新あり {path}')
    else:
        print(f'新規作成 {path}')
    path.write_text(text, newline='\n', encoding='utf8')


def _validate_and_collect_page_paths(path, files_allowed, subdirs_allowed, collect_page=True):
    """
    無許可のファイルやサブディレクトリがないか確認しながら .html ファイルを収集します
    逆に allowed なファイルやサブディレクトリが存在するかは確認しません
    コミット漏れは git status -s で防いでください
    """
    page_paths = []
    for child in path.iterdir():
        if child.is_dir() and child.name not in subdirs_allowed:
            raise ValueError(f'不要なサブディレクトリがある {child}')
        if child.is_file() and child.name not in files_allowed:
            if collect_page and child.suffix.lower() == '.html':
                page_paths.append(child)
            else:
                raise ValueError(f'不要なファイルがある {child}')
    return page_paths


def _validate(path, files_allowed, subdirs_allowed):
    _validate_and_collect_page_paths(path, files_allowed, subdirs_allowed, collect_page=False)


class Page:
    site_root = None
    site_name = 'Cookie Box'
    css_timestamp = '2025-10-09'
    last_counts = None

    def eval(self):
        text = self.path.read_text(encoding='utf8')
        rel_path = Path(os.path.relpath(self.path, Page.site_root)).as_posix()
        soup = BeautifulSoup(text, 'html.parser')

        self.title = soup.find('h1').get_text()
        page_title = soup.title.get_text()
        if self.is_index:
            if page_title != f'{Page.site_name}':
                raise ValueError(f'title タグがサイト名になっていない {self.path}')
        else:
            if page_title != f'{self.title} - {Page.site_name}':
                raise ValueError(f'title タグが h1 タグ + サイト名になっていない {self.path}')

        for tag in soup.find_all(True):
            if tag.has_attr('style'):
                raise ValueError(f'インラインスタイルがある {self.path}')

        for a in soup.find_all('a'):
            if a.has_attr('target'):
                raise ValueError(f'a タグに target 属性がある {self.path}')

        links = soup.find_all('link', {'rel': 'stylesheet'})
        for link in links:
            css = link['href']
            if css.startswith('http'):
                continue
            # print(css)

        count = len(text)
        last_count = 0
        if rel_path in Page.last_counts:
            last_count = Page.last_counts[rel_path]['count']
        else:
            Page.last_counts[rel_path] = {'rel_path': rel_path}
        if count == last_count:  # 文字数が一致していれば文字数更新日
            self.timestamp = Page.last_counts[rel_path]['timestamp']
        else:  # そうでなければファイルの最終変更日
            # self.timestamp = (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d')
            self.timestamp = datetime.fromtimestamp(self.path.stat().st_mtime).strftime('%Y-%m-%d')
            Page.last_counts[rel_path]['timestamp'] = self.timestamp
            Page.last_counts[rel_path]['count'] = count
        print(self.timestamp, self.title, f'({last_count} --> {count})')
        return soup

    def __init__(self, path, is_index=False):
        self.path = path
        self.is_index = is_index

    def generate(self, template, context):
        rendered = template.render(context) + '\n'
        _write_text(self.path, rendered)
        self.eval()

    def as_anchor(self, source_path, with_ts=False):
        rel_path = Path(os.path.relpath(self.path, source_path.parent)).as_posix()
        elm_a = str(Elm('a', self.title).set_attr('href', rel_path)).replace('\n', '')
        if not with_ts:
            return elm_a
        elm_ts = str(Elm('span', self.timestamp).set_attr('class', 'index-ts')).replace('\n', '')
        return f'{elm_a} {elm_ts}'

    def as_xml_url(self, domain):
        url = domain + Path(os.path.relpath(self.path, Page.site_root)).as_posix()
        priority = 1.0 if self.is_index else 0.5
        lines = [
            '<url>',
            f'<loc>{url}</loc>',
            f'<lastmod>{self.timestamp}</lastmod>',
            '<changefreq>monthly</changefreq>',
            f'<priority>{priority}</priority>',
            '</url>',
        ]
        return '\n'.join(lines)

    @staticmethod
    def as_ul_of_links(pages, source_path, with_ts=False, n_max=None):
        ul = Elm('ul')
        for page in pages:
            ul.append(Elm('li', page.as_anchor(source_path, with_ts)))
            if (n_max is not None) and (len(ul.inner) >= n_max):
                break
        return str(ul)


class Category(Page):
    def __init__(self, cat_name, path):
        super().__init__(path)
        self.cat_name = cat_name
        self.articles = []

    def generate(self, template):
        self.articles.sort(key=lambda a: a.title)
        context = {
            'category_name': self.cat_name,
            'n_articles': len(self.articles),
            'list_article': Page.as_ul_of_links(self.articles, self.path, with_ts=True),
            'css_timestamp': Page.css_timestamp,
        }
        super().generate(template, context)


class Article(Page):
    def __init__(self, path, all_cats, all_cat_paths):
        super().__init__(path)
        soup = self.eval()
        elm_cats = soup.find(class_='categories')
        if elm_cats is not None:
            cats = elm_cats.find_all('a')
            for cat in cats:
                cat_name = cat.get_text()
                cat_path = (path.parent / Path(cat['href'])).resolve()
                if cat_name not in all_cats:
                    if cat_path in all_cat_paths:
                        raise ValueError(f'カテゴリ名のゆれ {path}')
                    all_cats[cat_name] = Category(cat_name, cat_path)
                    all_cat_paths.add(cat_path)
                elif cat_path != all_cats[cat_name].path:
                    raise ValueError(f'カテゴリページパスのゆれ {path}')
                all_cats[cat_name].articles.append(self)


class IndexPage(Page):
    def __init__(self, lang_root, lang_template_root):
        super().__init__(lang_root / 'index.html', is_index=True)
        all_cats = {}
        all_cat_paths = set()

        # 記事ページ収集
        print('[INFO] 記事ページ収集')
        self.articles = []
        article_dir = self.path.parent / 'articles'
        for article_path in _validate_and_collect_page_paths(article_dir, [], []):
            article = Article(article_path, all_cats, all_cat_paths)
            self.articles.append(article)
        self.articles.sort(key=lambda a: a.timestamp, reverse=True)
        list_article_recent = Page.as_ul_of_links(self.articles, self.path, with_ts=True, n_max=10)
        self.articles.sort(key=lambda a: a.title)
        list_article = Page.as_ul_of_links(self.articles, self.path, with_ts=True)

        # カテゴリページ生成
        print('[INFO] カテゴリページ生成')
        self.all_cats = list(all_cats.values())
        self.all_cats.sort(key=lambda c: c.cat_name)
        cat_template_path = lang_template_root / 'category_template.html'
        cat_template = Template(cat_template_path.read_text(encoding='utf8'))
        for cat in self.all_cats:
            cat.generate(cat_template)
        list_category = Page.as_ul_of_links(self.all_cats, self.path)

        # 廃れたカテゴリページがないことの確認
        cat_dir = self.path.parent / 'categories'
        for cat_path in _validate_and_collect_page_paths(cat_dir, [], []):
            if cat_path not in all_cat_paths:
                raise ValueError(f'廃れたカテゴリページ {cat_path}')

        # 目次ページ自身の生成
        print('[INFO] 目次ページ生成')
        template_path = lang_template_root / 'index_template.html'
        template = Template(template_path.read_text(encoding='utf8'))
        context = {
            'n_article': len(self.articles),
            'list_article': list_article,
            'list_article_recent': list_article_recent,
            'n_category': len(self.all_cats),
            'list_category': list_category,
            'css_timestamp': Page.css_timestamp,
        }
        self.generate(template, context)

        # 不要なファイルやサブディレクトリがないことの確認
        _validate(lang_root, ['index.html'], ['articles', 'categories'])

    def get_pages(self):
        return [self] + self.articles + self.all_cats


class Sitemap:
    def __init__(self, domain, site_root, pages):
        # 不要なファイルやサブディレクトリがないことの確認
        files_allowed = ['style.css', 'funcs.js', 'robots.txt', 'sitemap.xml']
        subdirs_allowed = ['css', 'ja']
        _validate(site_root, files_allowed, subdirs_allowed)
        _validate(site_root / 'css', ['jupyter.css'], [])

        # サイトマップ生成
        print('[INFO] サイトマップ生成')
        sitemap_path = site_root / 'sitemap.xml'
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            '\n'.join([page.as_xml_url(domain) for page in pages]),
            '</urlset>',
        ]
        _write_text(sitemap_path, '\n'.join(lines) + '\n')


if __name__ == '__main__':
    domain = 'https://cookie-box.info/'
    Page.site_root = Path(__file__).resolve().parent / 'site'
    last_counts_path = Path(__file__).resolve().parent / '.last_counts.toml'
    with open(last_counts_path, encoding='utf8') as f:
        pages = toml.load(f)['pages']
        Page.last_counts = {page['rel_path']: page for page in pages}

    lang_root = Path(__file__).resolve().parent / 'site/ja'
    lang_template_root = Path(__file__).resolve().parent / 'templates/ja'
    index_ja = IndexPage(lang_root, lang_template_root)

    with open(last_counts_path, mode='w', encoding='utf8', newline='\n') as f:
        toml.dump({'pages': [v[1] for v in sorted(Page.last_counts.items())]}, f)

    Sitemap(domain, Page.site_root, index_ja.get_pages())

    ret = _run(['git', 'status', '-s'])
    if ret != '':
        ret_diff = _run(['git', 'diff', '--name-only'])
        msg = 'Unstaged changes detected' if ret_diff != '' else 'No unstaged changes'
        raise ValueError(f'Differences between HEAD commit and working tree ({msg})\n{ret}')
