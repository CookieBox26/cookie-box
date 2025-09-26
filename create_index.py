"""
記事ファイル群をもとに各カテゴリページとインデクスページを作成します。
作成した各カテゴリページとインデクスページはステージします。
"""
from shirotsubaki.element import Element as Elm
from jinja2 import Template
from bs4 import BeautifulSoup
import dataclasses
from pathlib import Path
import datetime
import subprocess


utf8 = {'encoding': 'utf8'}


@dataclasses.dataclass
class Article:
    title: str
    path: str
    timestamp: str


@dataclasses.dataclass
class Category:
    name: str
    path: str
    articles: list

    def render(self, lang):
        self.articles.sort(key=lambda a: a.title)
        template = Template(Path(f'templates/{lang}/category_template.html').read_text(**utf8))
        rendered = template.render({
            'category_name': self.name,
            'n_articles': len(self.articles),
            'list_article': _render_articles(self.articles, rel_path_to_lang_root='../'),
        }) + '\n'
        Path(f'site/{lang}/{self.path}').write_text(rendered, newline='\n', **utf8)


def _render_articles(articles, n_max=None, rel_path_to_lang_root=''):
    list_article = Elm('ul')
    for article in articles:
        elm = Elm('li')
        elm.append(Elm('a', article.title).set_attr('href', rel_path_to_lang_root + article.path))
        elm.append(Elm('span', article.timestamp).set_attr('class', 'index-ts'))
        list_article.append(elm)
        if (n_max is not None) and (len(list_article.inner) >= n_max):
            break
    return str(list_article)


def _validate_and_get_title(soup):
    for tag in soup.find_all(True):
        if tag.has_attr('style'):
            print(f'[WARNING] インラインスタイルがある {article_path.as_posix()}')
    for a in soup.find_all('a'):
        if a.has_attr('target'):
            print(f'[WARNING] target 属性がある {article_path.as_posix()}')
    title = soup.find('h1').get_text()
    page_title = soup.title.get_text()
    if page_title != f'{title} - Cookie Box':
        print(f'[WARNING] ページタイトルと記事見出しが不一致 {article_path.as_posix()}')
    return title


def _get_info(lang):
    # 記事の収集
    d_cat = {}
    articles = []
    article_paths = Path(f'site/{lang}/articles').glob('*.html')
    for article_path in article_paths:
        rc = subprocess.run(['git', 'diff', '--quiet', '--', article_path.as_posix()])
        if rc == 1:
            print(f'[WARNING] 未ステージの変更 {article_path.as_posix()}')
        soup = BeautifulSoup(article_path.read_text(**utf8), 'html.parser')
        title = _validate_and_get_title(soup)
        article = Article(
            title=title,
            path=article_path.as_posix().replace(f'site/{lang}/', ''),
            timestamp=datetime.datetime.fromtimestamp(
                article_path.stat().st_mtime
            ).strftime('%Y-%m-%d'),
        )
        articles.append(article)

        elm_cats = soup.find(class_='categories')
        if elm_cats is not None:
            cats = elm_cats.find_all('a')
            for cat in cats:
                cat_name = cat.get_text()
                cat_path = cat['href'].replace('../', '')
                if cat_name not in d_cat:
                    d_cat[cat_name] = Category(
                        name=cat_name,
                        path=cat_path,
                        articles=[],
                    )
                else:
                    assert d_cat[cat_name].path == cat_path, 'カテゴリページパスのゆれ'
                d_cat[cat_name].articles.append(article)

    # プレースホルダ挿入文字列作成
    articles.sort(key=lambda a: a.title)
    list_article = _render_articles(articles, n_max=None)
    articles.sort(key=lambda a: a.timestamp)
    list_article_recent = _render_articles(articles, n_max=10)
    d_cat = dict(sorted(d_cat.items()))
    set_cat_path = set()
    list_category = Elm('ul')
    for cat in d_cat.values():
        cat.render(lang)  # カテゴリページ作成
        set_cat_path.add(cat.path)
        subprocess.run(['git', 'add', f'site/{lang}/{cat.path}'])
        elm = Elm('li', Elm('a', f'Category:{cat.name}').set_attr('href', cat.path))
        list_category.append(elm)

    # カテゴリページのクリーンアップ
    category_paths = Path(f'site/{lang}/categories').glob('*.html')
    for category_path in category_paths:
        if category_path.as_posix().replace(f'site/{lang}/', '') not in set_cat_path:
            print(f'[WARNING] {lang}/{cat.path} をアンステージ＆削除してください')

    return {
        'n_article': len(articles),
        'list_article': list_article,
        'list_article_recent': list_article_recent,
        'n_category': len(d_cat),
        'list_category': str(list_category),
    }


def create_index(lang='ja'):
    template = Template(Path(f'templates/{lang}/index_template.html').read_text(**utf8))
    rendered = template.render(_get_info(lang)) + '\n'
    Path(f'site/{lang}/index.html').write_text(rendered, newline='\n', **utf8)
    subprocess.run(['git', 'add', f'site/{lang}/index.html'])


if __name__ == '__main__':
    create_index()
