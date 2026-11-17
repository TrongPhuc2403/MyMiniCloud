"""Keep independent Docker build contexts identical, except the HTML node label."""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'web-frontend-server' / 'html'

def sync(check=False):
    errors = []
    for node in (1, 2):
        target = ROOT / f'web-frontend-server{node}' / 'html'
        for source in [SOURCE / 'index.html', *SOURCE.joinpath('assets').glob('*')]:
            relative = source.relative_to(SOURCE)
            expected = source.read_bytes()
            if relative.name == 'index.html':
                expected = expected.replace(b'data-node="Main"', f'data-node="Node {node}"'.encode())
                expected = expected.replace(b'id="serving-node">Main', f'id="serving-node">Node {node}'.encode())
            destination = target / relative
            if check:
                if not destination.exists() or destination.read_bytes() != expected:
                    errors.append(str(destination.relative_to(ROOT)))
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(expected)
    if errors:
        raise SystemExit('Frontend drift: ' + ', '.join(errors))
    print('Frontend sync verified.' if check else 'Synced dashboard/assets to Node 1 and Node 2.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    sync(parser.parse_args().check)
