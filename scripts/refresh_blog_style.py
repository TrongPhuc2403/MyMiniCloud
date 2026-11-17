"""Add shared theme and original vector covers without rewriting article content."""
from pathlib import Path
from html import escape
import re

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web-frontend-server' / 'html'
assets = WEB / 'assets'
assets.mkdir(exist_ok=True)
for i, title, subtitle, accent in [(1,'THE CLOUD, EXPLAINED','01 / CLOUD COMPUTING','#60a5fa'),(2,'BUILD. SHIP. REPEAT.','02 / DOCKER & CONTAINERS','#22d3ee'),(3,'YOUR NEXT CLOUD SERVER','03 / AWS EC2','#fbbf24')]:
    # SVG is XML: literal ampersands in labels invalidate the entire image.
    title, subtitle = escape(title), escape(subtitle)
    if i == 1:
        art = '<path d="M340 125h127a34 34 0 0 0 0-68 54 54 0 0 0-102-13 42 42 0 0 0-25 81Z"/><path d="M390 77h34m-17-17v34"/>'
    elif i == 2:
        art = '<path d="m410 32 60 34v70l-60 34-60-34V66Z M350 66l60 35 60-35 M410 101v69 M380 49l60 35v35"/><path d="M320 156h32m120-109h30"/>'
    else:
        art = '<rect x="350" y="35" width="120" height="51" rx="9"/><rect x="350" y="106" width="120" height="51" rx="9"/><path d="M369 61h3m26 0h48m-77 71h3m26 0h48M410 86v20"/>'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="220" viewBox="0 0 600 220"><defs><pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r=".7" fill="#6a8ac2" opacity=".25"/></pattern><radialGradient id="glow"><stop stop-color="{accent}" stop-opacity=".18"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient></defs><path fill="#0f1e38" d="M0 0h600v220H0z"/><path fill="url(#dots)" d="M0 0h600v220H0z"/><ellipse cx="410" cy="105" rx="175" ry="155" fill="url(#glow)"/><g stroke="{accent}" stroke-width="2" fill="none" stroke-linejoin="round" stroke-linecap="round">{art}</g><text x="28" y="39" fill="{accent}" font-family="Arial,sans-serif" font-size="10" letter-spacing="1.8">MYMINICLOUD JOURNAL</text><text x="28" y="113" fill="#edf4ff" font-family="Arial,sans-serif" font-size="18" font-weight="bold">{title}</text><text x="28" y="183" fill="#97accb" font-family="Arial,sans-serif" font-size="10" letter-spacing="1.5">{subtitle}</text></svg>'''
    (assets / f'cover-{i}.svg').write_text(svg, encoding='utf-8')
(assets / 'favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="10" fill="#2563eb"/><path d="M11 29h19a7 7 0 0 0 0-14 10 10 0 0 0-19-3 9 9 0 0 0 0 17Z" fill="none" stroke="white" stroke-width="2"/></svg>', encoding='utf-8')

for path in WEB.joinpath('blog').glob('*.html'):
    text = path.read_text(encoding='utf-8')
    if '/assets/blog.css' not in text:
        text = text.replace('</head>', '<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">\n<script src="/assets/theme.js"></script>\n<link rel="stylesheet" href="/assets/blog.css">\n</head>')
        text = text.replace('</header>', '<button class="blog-theme-toggle" data-theme-toggle type="button" aria-label="Chuyển giao diện">☼</button>\n</header>', 1)
    if path.name == 'index.html':
        count = [0]
        def cover(match):
            count[0] += 1
            return f'<div class="{match.group(1)}" aria-hidden="true"><img class="cover-image" src="/assets/cover-{count[0]}.svg" alt="" loading="lazy"></div>'
        text = re.sub(r'<div class="(card-art[^\"]*)" aria-hidden="true">.*?</div>', cover, text, flags=re.S)
    path.write_text(text, encoding='utf-8')
print('Blog theme updated; all three articles and inline illustrations preserved.')
