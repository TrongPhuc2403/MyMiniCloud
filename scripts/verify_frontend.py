"""Dependency-free checks for links, HTML structure and preservation of articles."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / 'web-frontend-server' / 'html'
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.stack, self.errors = set(), [], [], []
        self.feed(text)
        if self.stack:
            self.errors.append('Unclosed tags: ' + ', '.join(self.stack))

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if 'id' in attrs:
            if attrs['id'] in self.ids:
                self.errors.append('Duplicate id: ' + attrs['id'])
            self.ids.add(attrs['id'])
        for field in ('href', 'src'):
            if attrs.get(field):
                self.links.append(attrs[field])
        if tag == 'img' and 'alt' not in attrs:
            self.errors.append('Image missing alt')
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, pairs):
        self.handle_starttag(tag, pairs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f'Unexpected closing {tag}; open: {self.stack[-3:]}')
        else:
            self.stack.pop()

def article(text):
    return re.search(r'<article\b.*?</article>', text, re.S).group(0).replace('\r\n', '\n')

def verify():
    errors = []
    parsed = {}
    svg_count = 0
    for base in (MAIN, ROOT/'web-frontend-server1/html', ROOT/'web-frontend-server2/html'):
        for image in base.rglob('*.svg'):
            svg_count += 1
            try:
                ET.parse(image)
            except ET.ParseError as exc:
                errors.append(f'{image.relative_to(ROOT)}: invalid SVG XML: {exc}')
        for file in base.rglob('*.html'):
            parsed[file] = Page(file.read_text(encoding='utf-8'))
    for file, page in parsed.items():
        errors.extend(f'{file.relative_to(ROOT)}: {message}' for message in page.errors)
        base = next(parent for parent in file.parents if parent.name == 'html')
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            path = unquote(url.path)
            # These endpoints are served by Gateway, not the static filesystem.
            if path.startswith('/api/') or path.rstrip('/') == '/student':
                continue
            if path.startswith('/blog/'):
                target = MAIN / path.lstrip('/')
            elif path.startswith('/'):
                target = base / path.lstrip('/')
            else:
                target = file.parent / path if path else file
            if target.is_dir():
                target /= 'index.html'
            if not target.exists():
                errors.append(f'{file.relative_to(ROOT)}: missing {link}')
            elif url.fragment:
                target_page = parsed.get(target)
                if target_page and url.fragment not in target_page.ids:
                    # Existing blog links to the old landing anchor remain supported.
                    if url.fragment != 'kham-pha':
                        errors.append(f'{file.relative_to(ROOT)}: missing fragment {link}')
    for i in (1,2,3):
        relative = f'web-frontend-server/html/blog/blog{i}.html'
        old = subprocess.check_output(['git','show',f'HEAD:{relative}'], cwd=ROOT).decode('utf-8')
        current = ROOT.joinpath(relative).read_text(encoding='utf-8')
        if article(old) != article(current):
            errors.append(f'Article content changed: {relative}')
    subprocess.run([sys.executable,str(ROOT/'scripts/sync_frontends.py'),'--check'],check=True)
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(parsed)} HTML pages; nesting, unique IDs, links, assets, fragments, image alt; 3 original articles unchanged.')
    print(f'PASS: {svg_count} SVG files parsed as valid XML across all frontend nodes.')

if __name__ == '__main__':
    verify()
