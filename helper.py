"""
サンプル1 (すべての記事の CSS タイムスタンプを更新する)
```toml
[[job_groups]]
path = "site/ja/articles/pandas-styler.html"
jobs = [{ job_type = "UPDATE_CSS_TIMESTAMP", css = "../../css/jupyter.css", timestamp = "2025-10-18" }]

[[job_groups]]
path = "site/ja/articles/*.html"
jobs = [
  { job_type = "UPDATE_CSS_TIMESTAMP", css = "../../css/style.css", timestamp = "2025-10-18" },
  { job_type = "UPDATE_CSS_TIMESTAMP", css = "../../css/cookie-box.css", timestamp = "2025-10-18" },
]
```
"""
# /// script
# requires-python = "==3.11.*"
# dependencies = [
#     "beautifulsoup4",
#     "toml",
# ]
# ///

from bs4 import BeautifulSoup
from pathlib import Path
import datetime
import toml
import subprocess


class ArticleHelper:
    site_name = 'Cookie Box'

    @classmethod
    def eq(cls, element, element_class_selector):
        tag, clazz = element_class_selector.split('.')
        return element.name == tag and clazz in element.get('class', [])

    @classmethod
    def _clear_children(cls, element, replace_to=''):
        for child in element.children:
            child.replace_with(replace_to)

    def generate(self):
        self.path.write_text(str(self.soup), encoding='utf8', newline='\n')
        print(self.path.as_posix())

    def __init__(self, path):
        self.path = path
        self.soup = None

    def copy_from(self, base_path, new_title, categories):
        if self.path.exists():
            raise ValueError(f'{self.path} exists.')
        self.soup = BeautifulSoup(Path(base_path).read_text(encoding='utf8'), 'html.parser')
        self.soup.title.string = f'{new_title} - {ArticleHelper.site_name}'
        self.soup.find('h1').string = new_title
        item = self.soup.select_one('div.item')
        cleared_last = False
        for child in item.children:
             clear = False
             if child.name == 'h1':
                 pass
             elif ArticleHelper.eq(child, 'div.categories'):
                 ArticleHelper._clear_children(child)
                 for cat in categories:
                     cat_ = '-'.join(cat.lower().split())
                     a_tag = self.soup.new_tag('a', href=f'../categories/{cat_}.html')
                     a_tag.string = cat
                     child.append(a_tag)
             elif ArticleHelper.eq(child, 'div.summary'):
                 ul_tag = child.select_one('ul')
                 ArticleHelper._clear_children(ul_tag)
                 ul_tag.extend(['\n', self.soup.new_tag('li'), '\n'])
             elif child.name == 'h2' and child.string == '参考文献':
                 pass
             elif ArticleHelper.eq(child, 'ol.ref'):
                 ArticleHelper._clear_children(child)
             else:
                 clear = True
             if clear:
                 child.replace_with('' if cleared_last else '\n')
                 cleared_last = True
             else:
                 cleared_last = False

    def update_css_timestamp(self, css, timestamp):
        if self.soup is None:
            self.soup = BeautifulSoup(self.path.read_text(encoding='utf8'), 'html.parser')
        links = self.soup.find_all('link', {'rel': 'stylesheet'})
        for link in links:
            if link['href'].startswith(css):
                link['href'] = f'{css}?v={timestamp}'

    def add_reference(self, references):
        if self.soup is None:
            self.soup = BeautifulSoup(self.path.read_text(encoding='utf8'), 'html.parser')
        today = datetime.datetime.now().strftime('%Y年%#m月%#d日')
        ol_tag = self.soup.select_one('ol.ref')
        for ref in references:
            li_tag = self.soup.new_tag('li')
            a_tag = self.soup.new_tag('a', href=ref[1])
            a_tag['class'] = 'asis'
            li_tag.append(BeautifulSoup(ref[0], 'html.parser'))
            li_tag.extend([', ', a_tag, f', {today}参照.'])
            ol_tag.append(li_tag)

    @classmethod
    def run_jobs(cls, path, jobs):
        ah = cls(path)
        for job in jobs:
            print(job['job_type'])
            if job['job_type'] == 'COPY_FROM':
                ah.copy_from(
                    base_path=job['base_path'],
                    new_title=job['new_title'],
                    categories=job['categories'],
                )
            if job['job_type'] == 'UPDATE_CSS_TIMESTAMP':
                ah.update_css_timestamp(job['css'], job['timestamp'])
            if job['job_type'] == 'ADD_REFERENCE':
                ah.add_reference(job['references'])
        ah.generate()
        return ah


if __name__ == '__main__':
    with open('.helper.toml', encoding='utf8') as f:
        conf = toml.load(f)

    ah = None
    for job_group in conf['job_groups']:
        path = Path(job_group['path'])
        if '*' in path.name:
            for path in path.parent.glob(path.name):
                ah = ArticleHelper.run_jobs(path, job_group['jobs'])
        else:
            ah = ArticleHelper.run_jobs(path, job_group['jobs'])

    if 'text_editor' in conf:
        subprocess.Popen([conf['text_editor'], ah.path.resolve()])
    if 'web_browser' in conf:
        subprocess.Popen([conf['web_browser'], ah.path.resolve()])
