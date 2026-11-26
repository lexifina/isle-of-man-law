"""Check every kept unit of a pre-1976 part against a second, independent extraction (pypdf) of the same PDF, letters
only (as verify_acts.py does for the first five Acts: running heads and feet dropped).

    python -I verify_pre1976.py <part file> [--drop]

--drop removes from the part every unit with a paragraph the second extraction does not confirm (noted in the
version note) and drops acts left empty.
"""
import io
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
CACHE = HERE / '.cache'
idx = json.loads((CACHE / 'acts_index_all.json').read_text(encoding='utf8'))
L = lambda s: re.sub(r'[^A-Za-z]', '', s.replace('’', "'"))  # noqa: E731
path = Path(sys.argv[1])
drop = '--drop' in sys.argv
part = json.load(open(path, encoding='utf8'))
bad = units = 0
keep_acts = []
for a in part['acts']:
    lk = a['earlier_laws'][0]
    y, n = lk.split('-')[1:3]
    aid = f'{y}-{int(n):04d}'
    raw = (CACHE / idx[aid]['path']).read_bytes()
    title = a['title']
    keep = []
    for pg in PdfReader(io.BytesIO(raw)).pages:
        for ln in (pg.extract_text() or '').splitlines():
            t = ln.strip()
            if re.search(r'\bAT \d+ of \d{4}\b', t) or re.fullmatch(r'(Section|Schedule|Page)\s*\d*\w*', t) \
                    or re.match(r'(Section|Schedule)\s+\d+\w*\s+\S', t) or re.search(r'\b(Section|Schedule)\s+\d+\w*$', t) \
                    or t.replace('THE ', '').lower().startswith(title.lower()[:20]) or t == 'c':
                continue
            keep.append(t)
    ref = L(' '.join(keep))
    v = a['versions'][0]
    missed = []
    for k, u in list(v['units'].items()):
        head, body = u['text'].split('\n', 1)
        head = re.sub(r'^#\s+\d+[A-Z]*\s+', '', head).lstrip('# ')
        miss = [p for p in [head] + body.splitlines() if L(p) not in ref]
        units += 1
        if miss:
            bad += 1
            missed.append(k)
            print('MISS', a['slug'], k, miss[0][:90])
    if drop and missed:
        for k in missed:
            del v['units'][k]
        v['note'] += (' Also left out, as a second text extraction of the PDF did not confirm every word: '
                      + ', '.join(re.sub(r'^s-0*', 's ', k) for k in missed) + '.')
    if v['units']:
        keep_acts.append(a)
print(len(part['acts']), 'acts,', units, 'units checked; units with a miss', bad)
if drop:
    gone = {a['earlier_laws'][0] for a in part['acts']} - {a['earlier_laws'][0] for a in keep_acts}
    part['acts'] = keep_acts
    for g in gone:
        part['laws'].pop(g, None)
    path.write_text(json.dumps(part, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    print('written', path, len(keep_acts), 'acts')
