"""Run gitlaw_common/append.py (unchanged), adding each law's (or act's) `extra_trailers` to its commits.

    python -X utf8 -I append_extra.py <scripts/isle-of-man-law> --repo <clone> --docs-date YYYY-MM-DD [--dry-run]

Used for the secondary-copy parts of 2026-11-26 (Source-status, Text-source, In-force-basis trailers). The builder
itself is not changed: its message functions are wrapped here.
"""
import sys
from pathlib import Path

repo = Path(sys.argv[sys.argv.index('--repo') + 1])
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'gitlaw_common'))  # read-only use
import build as B  # noqa: E402
import append as A  # noqa: E402

_start, _change = B.start_message, B.change_message


def _extra(c, act=None, law=None):
    out = []
    if law and c['laws'].get(law, {}).get('extra_trailers'):
        out += c['laws'][law]['extra_trailers']
    if act and act.get('extra_trailers'):
        keys = {t.split(':', 1)[0] for t in out}
        out += [t for t in act['extra_trailers'] if t.split(':', 1)[0] not in keys]
    return out


def _merge(trailers, extra):
    """One trailer per key: an extra Text-source keeps the builder's URL after its own description."""
    keys = {t.split(':', 1)[0] for t in extra}
    out = []
    for t in trailers:
        k, _, v = t.partition(': ')
        if k == 'Text-source' and 'Text-source' in keys:
            extra = [e + f', {v}' if e.startswith('Text-source:') else e for e in extra]
            continue
        if k in keys:
            continue
        out.append(t)
    return out + extra


def start_message(c, x):
    author, msg, trailers = _start(c, x)
    return author, msg, _merge(trailers, _extra(c, x['act'], x['act'].get('first_law')))


def change_message(c, x):
    author, msg, trailers = _change(c, x)
    extra = _extra(c, None, x.get('law') if x['kind'] == 'law' else None)
    keys = {t.split(':', 1)[0] for t in extra}
    for p in x['parts']:
        for t in _extra(c, p['act']):
            if t.split(':', 1)[0] not in keys:
                extra.append(t)
                keys.add(t.split(':', 1)[0])
    return author, msg, _merge(trailers, extra)


B.start_message, B.change_message = start_message, change_message

if __name__ == '__main__':
    A.main()
