"""Isle of Man: check every kept unit against a second, independent text extraction (pypdf) of the same official PDF.
Letters only on both sides, so line breaks, hyphenation and endnote markers do not matter."""
import glob, io, json, re, sys, os
from pathlib import Path
from pypdf import PdfReader
HERE = Path(__file__).resolve().parent
CACHE = HERE / '.cache'
idx = json.loads((CACHE / 'acts_index.json').read_text(encoding='utf8'))
src = Path(os.environ.get('IM_OUT', HERE)) / 'corpus.d'
L = lambda s: re.sub(r'[^A-Za-z]', '', s.replace('’', "'"))
bad = 0
for f in sorted(glob.glob(str(src / '*.json'))):
    part = json.load(open(f, encoding='utf8'))
    for a in part['acts']:
        raw = (CACHE / idx[a['slug']]['path']).read_bytes()
        title = a['title']
        keep = []
        for pg in PdfReader(io.BytesIO(raw)).pages:  # drop the running heads and feet of each page
            for ln in (pg.extract_text() or '').splitlines():
                t = ln.strip()
                if re.search(r'\bAT \d+ of \d{4}\b', t) or re.fullmatch(r'(Section|Schedule|Page)\s*\d*\w*', t) or re.match(r'(Section|Schedule)\s+\d+\w*\s+\S', t) or re.search(r'\b(Section|Schedule)\s+\d+\w*$', t) or t.replace('THE ', '').lower().startswith(title.lower()[:20]) or t == 'c':
                    continue
                keep.append(t)
        ref = L(' '.join(keep))
        n = 0
        for k, u in a['versions'][0]['units'].items():
            head, body = u['text'].split('\n', 1)
            head = re.sub(r'^#\s+\d+[A-Z]*\s+', '', head).lstrip('# ')
            for para in [head] + body.splitlines():
                if L(para) not in ref:
                    bad += 1; print('MISS', a['slug'], k, para[:90])
            n += 1
        print(a['slug'], n, 'units checked')
print('misses', bad)
