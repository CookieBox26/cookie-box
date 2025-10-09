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

    def _clear_optional_stylesheet(self):
        links = self.soup.find_all('link', {'rel': 'stylesheet'})
        for link in links:
            if link['href'].startswith('https') and link['href'].endswith('prism-coy.min.css'):
                continue
            if link['href'].startswith('../../style.css'):
                continue
            link.replace_with('')

    def generate(self):
        self.path.write_text(str(self.soup), encoding='utf8', newline='\n')
        print(self.path.as_posix())

    def __init__(self, path):
        self.path = Path(path)
        self.soup = None

    def duplicate(self, base_path, new_title, categories):
        self.soup = BeautifulSoup(Path(base_path).read_text(encoding='utf8'), 'html.parser')
        self._clear_optional_stylesheet()
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

    def update_css_timestamp(self, css_timestamp):
        if self.soup is None:
            self.soup = BeautifulSoup(self.path.read_text(encoding='utf8'), 'html.parser')
        links = self.soup.find_all('link', {'rel': 'stylesheet'})
        for link in links:
            if link['href'].startswith('../../style.css'):
                link['href'] = f'../../style.css?v={css_timestamp}'

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


if __name__ == '__main__':
    with open('helper.conf', encoding='utf8') as f:
        conf = toml.load(f)
    print(conf['path'])
    ah = ArticleHelper(conf['path'])
    for job in conf['jobs']:
        print(job['job_type'])
        if job['job_type'] == 'DUPLICATE':
            ah.duplicate(
                base_path=job['base_path'],
                new_title=job['new_title'],
                categories=job['categories'],
            )
        if job['job_type'] == 'UPDATE_CSS_TIMESTAMP':
            ah.update_css_timestamp(job['css_timestamp'])
        if job['job_type'] == 'ADD_REFERENCE':
            ah.add_reference(job['references'])
    ah.generate()
    if 'text_editor' in conf:
        subprocess.Popen([conf['text_editor'], ah.path.resolve()])
    if 'web_browser' in conf:
        subprocess.Popen([conf['web_browser'], ah.path.resolve()])
