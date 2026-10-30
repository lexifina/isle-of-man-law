"""Isle of Man: build corpus.d parts from cached official revision PDFs of pre-1976 Acts of Tynwald (cache only).

Copyright: Crown copyright in an Act of Tynwald ends 50 years after the end of the year of Royal Assent (Copyright Act
1991 s 157(2)), so the words of an Act assented in 1975 or earlier are free. Words put in later by amending Acts that
are still in copyright are not. A section is therefore kept only when every endnote marked in it names Acts (or other
instruments) dated 1975 or earlier, and it shows no fine amounts (the general notes say those were raised by later
Acts). Everything else is left out and listed in the version note.
"""
import datetime, hashlib, json, os, re, sys, warnings
from pathlib import Path
warnings.simplefilter('ignore')
import fitz  # noqa: E402
HERE = Path(__file__).resolve().parent
from acts import ACTS  # noqa: E402

CACHE = HERE / '.cache'
LAST_FREE_YEAR = 1975
MONTHS = {m: i for i, m in enumerate('January February March April May June July August September October November December'.split(), 1)}
PARA = re.compile(r'^(\((?:\d+[A-Z]*|[a-z]{1,2}|[ivxl]+|[A-Z])\)|Provided\b|\d+\.\s)')


def norm(s):
    s = s.replace('\xa0', ' ').replace(' ', ' ').replace(' ', ' ').replace(' ', ' ')
    s = s.replace('–', '-').replace('—', '-').replace('‘', "'").replace('’', "'")
    s = s.replace('“', '"').replace('”', '"')
    return re.sub(r'\s+', ' ', s).strip()


def lines_of(doc):
    """Body lines as (page, x0, y0, text, size, bold, [markers]) with running heads, feet and markers split off."""
    out = []
    for pno, page in enumerate(doc):
        h = page.rect.height
        for b in page.get_text('dict')['blocks']:
            for l in b.get('lines', []):
                x0, y0, x1, y1 = l['bbox']
                if y0 < 75 or y0 > h - 70:
                    continue
                text, marks, size, bold, ital = '', [], 0, False, False
                for s in l['spans']:
                    if s['flags'] & 1 and s['text'].strip():  # superscript: an endnote marker
                        marks += re.findall(r'\d+', s['text'])
                        continue
                    if s['text'].strip():
                        size = max(size, round(s['size']))
                        bold = bold or bool(s['flags'] & 16)
                        ital = ital or bool(s['flags'] & 2)
                    text += s['text']
                t = norm(text)
                if t or marks:
                    out.append((pno, round(x0), round(y0), t, size, bold or ital, marks))
    return out


def endnote_table(lines):
    """{marker: endnote text} from the Table of Endnote References."""
    notes, cur = {}, None
    started = False
    for pno, x0, y0, t, size, bold, marks in lines:
        if t == 'Table of Endnote References':
            started = True; continue
        if not started:
            continue
        m = re.match(r'^(\d+)\s+(.*)$', t)
        if m and (int(m.group(1)) == (int(cur) + 1 if cur else 1) or (cur and int(m.group(1)) > int(cur))):
            cur = m.group(1); notes[cur] = m.group(2)
        elif cur:
            notes[cur] += ' ' + t
    return notes


def years_in(note):
    """Years of the instruments an endnote names (Act names end in a year; SD numbers carry one too)."""
    return [int(y) for y in re.findall(r'\b(1[5-9]\d\d|20\d\d)\b', note)]


def parse_pdf(raw):
    doc = fitz.open(stream=raw, filetype='pdf')
    lines = lines_of(doc)
    full = ' '.join(l[3] for l in lines)
    ra = re.search(r'Received Royal Assent:\s*(\d{1,2}) ([A-Z][a-z]+) (\d{4})', full)
    cm = re.search(r'Commenced:\s*(\d{1,2}) ([A-Z][a-z]+) (\d{4})', full)
    cit = re.search(r'\bAT (\d+) of (\d{4})', full)
    d = lambda m: datetime.date(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1))).isoformat() if m else None
    # body: from the first page holding "Received Royal Assent" to the ENDNOTES heading
    start = next(i for i, l in enumerate(lines) if l[3].startswith('Received Royal Assent'))
    end = next((i for i, l in enumerate(lines) if i > start and l[3] == 'ENDNOTES'), len(lines))
    notes = endnote_table(lines[end:])
    units, order, cur = {}, [], None
    in_general_notes = False
    for pno, x0, y0, t, size, bold, marks in lines[start:end]:
        if t.startswith('GENERAL NOTE'):
            in_general_notes = True; continue
        head_num = re.fullmatch(r'(\d+)([A-Z]{0,3})', t) if bold and size >= 12 else None
        sch = re.match(r'^SCHEDULE\s*(\d*)\b', t) if bold and size >= 12 else None
        if head_num:
            in_general_notes = False
            key = f's-{int(head_num.group(1)):03d}' + (f'-{head_num.group(2).lower()}' if head_num.group(2) else '')
            cur = {'key': key, 'label': f's {head_num.group(1)}{head_num.group(2)}', 'kind': 'section', 'head': None,
                   'paras': [], 'marks': list(marks), 'num': f'{head_num.group(1)}{head_num.group(2)}'}
            units[key] = cur; order.append(key); continue
        if sch:
            in_general_notes = False
            n = int(sch.group(1) or 1)
            key = f'sch-{n:02d}'
            cur = {'key': key, 'label': f'Schedule {sch.group(1)}'.strip(), 'kind': 'schedule', 'head': t, 'paras': [], 'marks': list(marks), 'num': None}
            units[key] = cur; order.append(key); continue
        if in_general_notes or cur is None:
            continue
        cur['marks'] += marks
        if bold and size >= 12 and cur['kind'] == 'section' and cur['head'] is not None and not cur['paras'] and not cur['head'].startswith('[') and not re.match(r'^(PART|[IVXL]+\b)', t):
            cur['head'] += ' ' + t  # a section heading that wraps onto a second line
            continue
        if bold and (size >= 14 or (size >= 12 and cur['head'] is not None)):
            continue  # cross heading: Part and group headings (bold or italic) are not law text files
        if bold and size >= 12 and cur['head'] is None and cur['kind'] == 'section':
            cur['head'] = t; continue
        if not t:
            continue
        if cur['kind'] == 'section' and cur['head'] is None:
            # "[Repealed]" or a heading-less line right after the number
            cur['head'] = t; continue
        if not cur['paras'] or PARA.match(t):
            cur['paras'].append(t)
        elif cur['paras'][-1].endswith('-') and not cur['paras'][-1].endswith(' -'):
            cur['paras'][-1] += t
        else:
            cur['paras'][-1] += ' ' + t
    kept, left_out = {}, {}
    for key in order:
        u = units[key]
        head = u['head'] or ''
        if head.startswith('[Repealed') or head.startswith('[Spent') or not u['paras']:
            continue
        cited = [notes.get(m, '') for m in u['marks']]
        late = sorted({y for c in cited for y in years_in(c) if y > LAST_FREE_YEAR})
        unknown = [m for m in u['marks'] if m not in notes or not years_in(notes[m])]
        body = '\n'.join(u['paras'])
        if late or unknown:
            left_out[key] = f'amended by an instrument of {late[0]}' if late else 'endnote without a date'
            continue
        if re.search(r'£|\bstandard scale\b|\blevel \d', body):
            left_out[key] = 'shows a fine amount'
            continue
        title = f"# {u['num']} {head}" if u['kind'] == 'section' else f'# {head}'
        kept[key] = {'label': u['label'], 'kind': u['kind'], 'text': title + '\n' + body + '\n'}
    return {'royal_assent': d(ra), 'commenced': d(cm), 'citation': cit.group(0) if cit else None,
            'units': kept, 'left_out': left_out, 'total': len([k for k in order if not (units[k]['head'] or '').startswith('[Repealed')])}


def main(only=None):
    idx = json.loads((CACHE / 'acts_index.json').read_text(encoding='utf8'))
    out_dir = Path(os.environ.get('IM_OUT', HERE)) / 'corpus.d'
    out_dir.mkdir(exist_ok=True)
    for n, (slug, (aid, short)) in enumerate(ACTS.items(), start=10):
        if slug not in idx or (only and slug not in only):
            continue
        r = idx[slug]
        raw = (CACHE / r['path']).read_bytes()
        p = parse_pdf(raw)
        y = int(aid[:4])
        if not p['royal_assent'] or int(p['royal_assent'][:4]) > LAST_FREE_YEAR or y > LAST_FREE_YEAR:
            print(slug, 'not free', p['royal_assent']); continue
        cap = r['timestamp']
        frm = f'{cap[:4]}-{cap[4:6]}-{cap[6:8]}'
        lk = f'at-{y:04d}-{int(aid[5:]):03d}'
        title = short
        url = r['url'].replace('http://', 'https://')
        omitted = ', '.join(f"{k.replace('s-', 's ').lstrip('0')}" for k in list(p['left_out'])[:400])
        law = {'label': f"{title} ({p['citation']})", 'title': title, 'kind': 'law', 'enacted': p['royal_assent'],
               'published': None, 'url': url, 'temporary_until': None, 'restores': None,
               'note': f"{p['citation']}; Royal Assent {p['royal_assent']}" + (f", commenced {p['commenced']}" if p['commenced'] else '') + '.'}
        reasons = {}
        for k, why in p['left_out'].items():
            reasons.setdefault(why, []).append(re.sub(r'^s-0*', 's ', k).replace('sch-0', 'Schedule ').replace('sch-', 'Schedule '))
        note = (f"Official revised edition (revision {r['revision']}) as published on legislation.gov.im on {frm}. "
                f"Holds the {len(p['units'])} provisions whose words are out of Crown copyright. Left out: "
                + '; '.join(f"{why}: {', '.join(ks)}" for why, ks in sorted(reasons.items())) + '.' if reasons else
                f"Official revised edition (revision {r['revision']}) as published on legislation.gov.im on {frm}.")
        part = {'laws': {lk: law}, 'acts': [{
            'slug': slug, 'short': short, 'title': title, 'url': url, 'first_law': None, 'earlier_laws': [lk],
            'publisher': {'name': "Isle of Man Government, Attorney General's Chambers (legislation.gov.im)", 'email': 'legislation@legislation.gov.im.invalid'},
            'versions': [{'from': frm, 'source_url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'units': p['units'],
                          'credits': {}, 'note': note}]}],
            'decisions': [f"{title}: one version, the official revised edition as published on {frm} (the PDF states no 'as at' date, so it is dated by the day that copy was published); only provisions out of Crown copyright (Copyright Act 1991 s 157(2)) and with no endnote naming an instrument after {LAST_FREE_YEAR} are kept ({len(p['units'])} kept, {len(p['left_out'])} left out)."]}
        f = out_dir / f'{n}-{slug}.json'
        tmp = f.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(part, ensure_ascii=False, indent=1) + '\n', encoding='utf8', newline='\n')
        tmp.replace(f)
        print(slug, p['citation'], p['royal_assent'], 'kept', len(p['units']), 'left out', len(p['left_out']), 'of', p['total'])


if __name__ == '__main__':
    main(set(sys.argv[1:]) or None)
