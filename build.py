# /// script
# requires-python = "==3.11.*"
# dependencies = [
#     "beautifulsoup4",
#     "jinja2",
#     "shirotsubaki",
# ]
# ///

from shirotsubaki.element import Element as Elm
from jinja2 import Template
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import os


def _run(command):
    ret = subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()
    return ret[1:-1] if len(ret) >= 2 and ret[0] == ret[-1] == '"' else ret


class Page:
    site_name = 'Cookie Box'

    def eval(self):
        soup = BeautifulSoup(self.path.read_text(encoding='utf8'), 'html.parser')
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

        # self.timestamp = datetime.fromtimestamp(self.path.stat().st_mtime).strftime('%Y-%m-%d')
        status = _run(['git', 'status', '-s', self.path])
        if status == '':
            self.timestamp = _run(['git', 'log', '-1', '--format="%ad"', '--date=short', self.path])
        else:
            now = datetime.utcnow() + timedelta(hours=9)
            self.timestamp = now.strftime('%Y-%m-%d')
        print(self.timestamp, self.title)

        return soup

    def __init__(self, path, is_index=False):
        self.path = path
        self.is_index = is_index

    def generate(self, template, context):
        rendered = template.render(context) + '\n'
        self.path.write_text(rendered, newline='\n', encoding='utf8')
        self.eval()
        print(f'生成済み {self.path}')

    def as_anchor(self, source_path, with_ts=False):
        rel_path = Path(os.path.relpath(self.path, source_path.parent)).as_posix()
        elm_a = str(Elm('a', self.title).set_attr('href', rel_path)).replace('\n', '')
        if not with_ts:
            return elm_a
        elm_ts = str(Elm('span', self.timestamp).set_attr('class', 'index-ts')).replace('\n', '')
        return f'{elm_a} {elm_ts}'

    def as_xml_url(self, domain, site_root):
        url = domain + Path(os.path.relpath(self.path, site_root)).as_posix()
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
                        ValueError(f'カテゴリ名のゆれ {path}')
                    all_cats[cat_name] = Category(cat_name, cat_path)
                    all_cat_paths.add(cat_path)
                elif cat_path != all_cats[cat_name].path:
                    ValueError(f'カテゴリページパスのゆれ {path}')
                all_cats[cat_name].articles.append(self)


class IndexPage(Page):
    def __init__(self, lang_root, lang_template_root):
        super().__init__(lang_root / 'index.html', is_index=True)
        all_cats = {}
        all_cat_paths = set()

        # 記事ページ収集
        self.articles = []
        article_dir = self.path.parent / 'articles'
        for article_path in article_dir.glob('*.html'):
            article = Article(article_path, all_cats, all_cat_paths)
            self.articles.append(article)
        self.articles.sort(key=lambda a: a.timestamp, reverse=True)
        list_article_recent = Page.as_ul_of_links(self.articles, self.path, with_ts=True, n_max=10)
        self.articles.sort(key=lambda a: a.title)
        list_article = Page.as_ul_of_links(self.articles, self.path, with_ts=True)

        # カテゴリページ生成
        self.all_cats = list(all_cats.values())
        self.all_cats.sort(key=lambda c: c.cat_name)
        cat_template_path = lang_template_root / 'category_template.html'
        cat_template = Template(cat_template_path.read_text(encoding='utf8'))
        for cat in self.all_cats:
            cat.generate(cat_template)
        list_category = Page.as_ul_of_links(self.all_cats, self.path)

        # カテゴリページのクリーンアップ
        cat_dir = self.path.parent / 'categories'
        for cat_path in cat_dir.glob('*.html'):
            if cat_path not in all_cat_paths:
                print(f'[WARNING] {cat_path} をアンステージ＆削除してください')

        # 目次ページ自身の生成
        template_path = lang_template_root / 'index_template.html'
        template = Template(template_path.read_text(encoding='utf8'))
        context = {
            'n_article': len(self.articles),
            'list_article': list_article,
            'list_article_recent': list_article_recent,
            'n_category': len(self.all_cats),
            'list_category': list_category,
        }
        self.generate(template, context)

    def get_pages(self):
        return [self] + self.articles + self.all_cats


class Sitemap:
    def __init__(self, domain, site_root, pages):
        sitemap_path = site_root / 'sitemap.xml'
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            '\n'.join([page.as_xml_url(domain, site_root) for page in pages]),
            '</urlset>',
        ]
        sitemap_path.write_text('\n'.join(lines) + '\n', newline='\n', encoding='utf8')


if __name__ == '__main__':
    lang_root = Path(__file__).resolve().parent / 'site/ja'
    lang_template_root = Path(__file__).resolve().parent / 'templates/ja'
    index_ja = IndexPage(lang_root, lang_template_root)

    domain = 'https://cookie-box.info/'
    site_root = Path(__file__).resolve().parent / 'site'
    Sitemap(domain, site_root, index_ja.get_pages())

    print(_run(['git', 'status']))
