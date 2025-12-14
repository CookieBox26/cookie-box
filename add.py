import subprocess


if __name__ == '__main__':
    _run = lambda command: subprocess.run(command, capture_output=True, text=True, check=True)
    _run(['git', 'add', '.last_counts.toml'])
    _run(['git', 'add', 'add.py'])
    _run(['git', 'add', 'build.py'])
    _run(['git', 'add', 'site/funcs.js'])
    _run(['git', 'add', 'site/css/style.css'])
    _run(['git', 'add', 'site/css/cookie-box.css'])
    _run(['git', 'add', 'site/index.html'])

    _run(['git', 'add', 'templates/cookiepad/index_template.html'])
    _run(['git', 'add', 'templates/cookiepad/category_template.html'])
    _run(['git', 'add', 'site/css/cookiepad.css'])
    _run(['git', 'add', 'site/cookiepad/articles/*'])
    _run(['git', 'add', 'site/cookiepad/categories/*'])
    _run(['git', 'add', 'site/cookiepad/index.html'])

    _run(['git', 'add', 'site/sitemap.xml'])
    print(_run(['git', 'status', '-s']).stdout.rstrip('\n'))
