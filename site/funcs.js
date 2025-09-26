function createSidebar(mainPage = false, lang = 'ja') {
    let content = '';
    let indexUrl = mainPage ? 'index.html' : '../index.html';
    let back = `<a class="logo" href="${indexUrl}">&#x1f36a;Cookie Box</a>`;
    let gitHub = '<a href="https://github.com/CookieBox26/cookie-box/issues">Issues</a>';
    content += `<h2 class="logo">${back}</h2>`;
    if (!mainPage) {
        content += `<p>ご指摘等は ${gitHub} までご連絡ください</p>`;
        document.getElementById('smartphone-header').innerHTML += back;
    }
    content += '<p><a href="#">ページの一番上に戻る</a></p>';
    let index = '<h5>ページ内の小見出し一覧</h5>';
    const allHeaders = document.querySelectorAll('h2, h3');
    for (var i=0; i<allHeaders.length; ++i) {
        index += '<p class="';
        if (allHeaders[i].tagName == 'H3') {
            index += 'indent';
        }
        index += '">';
        index += '<a href="#head' + String(i) + '">';
        index += allHeaders[i].textContent + '</a></p>';
        allHeaders[i].innerHTML += '<a id="head' + String(i) + '"></a>';
    }
    content += `<div id="headers">${index}</div>`;
    if (mainPage) {
        let div = document.createElement('div');
        div.innerHTML = content;
        let ref = document.getElementById('header-externallink');
        document.getElementById('sidebar').insertBefore(div, ref);
    } else {
        document.getElementById('sidebar').innerHTML += content;
    }
}

function setButton(id, handle) {
    let button = document.getElementById(id);
    button.addEventListener("click", handle);
    button.addEventListener("touchstart", handle);
}

function setButtonOpenClose(id0, id1) {
    let target = document.getElementById(id1);
    target.style.display = "none";
    setButton(id0, () => {
        target.style.display = (target.style.display == "none") ? "block" : "none";
    });
}

function secureExternalLinks(root = document) {
    const originHost = location.host;
    root.querySelectorAll('a[href]').forEach((a) => {
        const href = a.getAttribute('href');
        if (!href) return;
        if (href.startsWith('#') || href.startsWith('mailto:')) return;
        const url = new URL(href, location.href);
        if (url.host === originHost) return;
        a.setAttribute('target', '_blank');
        const rel = (a.getAttribute('rel') || '').split(/\s+/);
        ['noopener', 'noreferrer'].forEach(v => {
            if (!rel.includes(v)) rel.push(v);
        });
        a.setAttribute('rel', rel.filter(Boolean).join(' '));
    });
}

function init(mainPage = false, lang = 'ja') {
    createSidebar(mainPage, lang);
    secureExternalLinks();
}

document.addEventListener('DOMContentLoaded', () => {
    const s = document.getElementById('app');
    init(s?.dataset.mainpage === 'true', s?.dataset.lang || 'ja');
});

(function () {
    if (typeof Prism === 'undefined' || typeof document === 'undefined') return;
    Prism.hooks.add('before-sanity-check', function (env) {
        env.code = env.code.replace(/^(?:\r?\n|\r)/, '');
    });
})();
