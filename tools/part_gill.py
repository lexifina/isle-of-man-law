"""Isle of Man: corpus.d part for the Acts of Tynwald read from Gill's Statutes of the Isle of Man (archive.org text
layer of a Google Books scan), approved by Alan 2026-11-26.

    python -I part_gill.py <acts.json from parse_gill.py> <identifier> <volume label> <slug> <part file>

One act per volume; each Act of Tynwald is one file (unit) in it, added on its in-force day and credited to itself.
In force: the promulgation day where the certificate's day is legible, else the Royal Assent day
(In-force-basis says which). Acts with neither legible day are held and listed in the part's decisions.
"""
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path


def slugify(s, n=60):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:n].rstrip('-') or 'act'


def cut_title(title):
    """A title ends where a preamble printed on its last line begins."""
    return re.split(r'(?<=[.^])\s+(?=(Wherea|WHEREA|It being|Whereas))', title)[0]


def short_of(title):
    title = cut_title(title)
    m = re.search(r'''["'*^ ]{0,4}The\s+(.{3,80}?\bAct\b),?\s*(1[78]\d\d)''', title)
    if m and re.search(r'(?i)(in|en)tituled', title[:m.start() + 5]):
        return f'{m.group(1)} {m.group(2)}'.replace('  ', ' ')
    t = re.sub(r'^(An|Au|AN)\s+(Act|Aot|ACT)[,.]?\s*(intituled|entituled)?\s*', '', title)
    t = re.sub(r'[.^/\\"\'*]+$', '', t).strip().lstrip('"\'* ')
    return ('Act ' + t) if t[:1].islower() else t


def norm(s):
    s = s.replace('\xa0', ' ').replace('—', '-').replace('–', '-').replace('‘', "'").replace('’', "'")
    s = s.replace('“', '"').replace('”', '"')
    return re.sub(r'[ \t]+', ' ', s).strip()


def main():
    src, ident, vol, slug, out, act_short = sys.argv[1:7]
    acts = json.load(open(src, encoding='utf-8'))['acts']
    raw = Path(src).read_bytes()
    url = f'https://archive.org/details/{ident}'
    laws, units_by_day, credits_by_day, held = {}, {}, {}, []
    used = set()
    for a in acts:
        if not a.get('day'):
            held.append(f"leaf {a['leaf']}: {(a.get('title') or a.get('error') or '')[:80]} ({a.get('held') or a.get('error')})")
            continue
        day = a['day']
        short = norm(short_of(a['title']))
        key = f"{day[:4]}-{slugify(short, 50)}"
        k, i = key, 2
        while k in used:
            k, i = f'{key}-{i}', i + 1
        used.add(k)
        lk = f'gill-{k}'
        basis = ('promulgation day, read from the promulgation certificate printed after the Act'
                 if a['basis'] == 'promulgation' else 'Royal Assent (promulgation day illegible in source OCR)')
        laws[lk] = {
            'label': (short if re.search(r'\d{4}$', short) else f'{short} ({day[:4]})')[:110],
            'title': norm(cut_title(a['title']))[:300], 'kind': 'law', 'enacted': a.get('assent'), 'published': None,
            'url': f"{url}/page/n{a['leaf']}", 'temporary_until': None, 'restores': None, 'note': None,
            'extra_trailers': [
                f'In-force-basis: {basis}',
                f'Source-status: secondary copy (Internet Archive, Google Books scan of {vol}, {url})',
                'Text-source: publisher OCR (the scan\'s uncorrected text layer; no OCR of our own)',
                'Approved: Alan 2026-11-26 (Gill text; Royal Assent day where the promulgation day is illegible)',
            ]}
        paras = []
        for p in a['paragraphs']:
            p = norm(p)
            if p.startswith('# '):
                head = cut_title(p)
                paras += [head, p[len(head):].strip()]
            else:
                paras.append(p)
        text = '\n'.join(p for p in paras if p) + '\n'
        units_by_day.setdefault(day, {})[k] = {'label': short[:80], 'kind': 'act', 'text': text}
        credits_by_day.setdefault(day, {})[k] = [lk]
    versions, cur = [], {}
    for day in sorted(units_by_day):
        cur = {**cur, **units_by_day[day]}
        versions.append({'from': day, 'source_url': url, 'sha256': hashlib.sha256(raw).hexdigest(),
                         'units': dict(sorted(cur.items())), 'credits': credits_by_day[day],
                         'note': None})
    first_day = min(units_by_day)
    first_law = credits_by_day[first_day][sorted(credits_by_day[first_day])[0]][0]
    if len(units_by_day[first_day]) > 1:
        first_law = None
    part = {
        'sources': [{'name': f'{vol} (Internet Archive {ident}, Google Books scan, text layer)', 'url': url,
                     'retrieved': '2026-11-26',
                     'licence': 'Public domain (printed 1883-1888; Acts of 1871 and earlier are out of copyright). '
                                "Google's usage guidelines on the scan ask for non-commercial use and attribution; "
                                'they are requests, not licence terms.',
                     'notes': 'Secondary copy, uncorrected OCR text layer. Approved by Alan 2026-11-26.'}],
        'laws': laws,
        'acts': [{'slug': slug, 'short': act_short,
                  'title': vol, 'url': url, 'first_law': first_law, 'earlier_laws': [],
                  'publisher': {'name': f'{vol} (archive.org text layer)', 'email': 'statutes-gill@archive.org.invalid'},
                  'extra_trailers': [
                      f'Source-status: secondary copy (Internet Archive, Google Books scan of {vol}, {url})',
                      'Text-source: publisher OCR (the scan\'s uncorrected text layer; no OCR of our own)'],
                  'versions': versions}],
        'decisions': [
            f'{vol}: each Act of Tynwald is one file, its caption, title and text as printed (side notes, running heads '
            'and footnotes dropped by position; signatures, Order in Council and promulgation certificate left out; '
            'schedules printed after the signatures kept). The text is the uncorrected OCR layer of the archive.org scan: '
            'it has misread letters, and is a secondary copy (approved by Alan 2026-11-26).',
            f'{vol}: an Act is in force from its promulgation day where the certificate printed after it gives a legible day; '
            'otherwise, as Alan approved on 2026-11-26, from its Royal Assent day (In-force-basis: Royal Assent '
            '(promulgation day illegible in source OCR)). An Act whose two Royal Assent readings disagree, or whose day '
            'cannot be read at all, is held.',
            f'{vol}: held ({len(held)}): ' + '; '.join(held) if held else f'{vol}: nothing held.',
        ],
    }
    Path(out).write_text(json.dumps(part, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(out, len(laws), 'Acts in', len(versions), 'days;', len(held), 'held')


if __name__ == '__main__':
    main()
