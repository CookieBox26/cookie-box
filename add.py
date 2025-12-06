import subprocess


if __name__ == '__main__':
    _run = lambda command: subprocess.run(command, capture_output=True, text=True, check=True)
    _run(['git', 'add', '.last_counts.toml'])
    _run(['git', 'add', 'add.py'])
    _run(['git', 'add', 'build.py'])
    _run(['git', 'add', 'site/css/cookie-box.css'])
    _run(['git', 'add', 'site/ja/articles/*'])
    _run(['git', 'add', 'site/ja/categories/*'])
    _run(['git', 'add', 'site/ja/index.html'])
    _run(['git', 'add', 'site/sitemap.xml'])
    _run(['git', 'add', 'templates/ja/category_template.html'])
    _run(['git', 'add', 'templates/ja/index_template.html'])
    print(_run(['git', 'status', '-s']).stdout.rstrip('\n'))
