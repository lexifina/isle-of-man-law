"""Split a Gill volume of the Statutes of the Isle of Man (archive.org text layer) into Acts of Tynwald.

    python -I parse_gill.py <pages.json> <first leaf> <last leaf> <out.json>

Each Act in these volumes is printed as: "Isle of Man, to Wit." / the caption of the Tynwald Court that passed it /
the title ("An Act ...") / the text / the signatures / the Order in Council (Royal Assent) / the promulgation
certificate ("At a Tynwald Court holden at ..., the <day>. The before-written Act ... was this day promulgated").

Kept as the Act's text: caption, title and text, up to the first signature line. The day the Act took effect is
the promulgation day read from the certificate; the Royal Assent day is read from the same certificate. An Act whose
promulgation day cannot be read with certainty (OCR damage) is held (no date guessed).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gill_lines  # noqa: E402

TOWIT = re.compile(r'(?i)(to\s*W[il1]t\.?\s*$)')
TITLE = re.compile(r'^(An|AN|Au|Ail|A n)\s*(Act|Aot|Ad|Acfc|act|ACT)\b')
BODY = re.compile(r'^(Whereas|WHEREAS|Wbereas|Wliereas|WhereaB|We[,.]?\s|We,|Be\s+it|BE\s+IT|Forasmuch|1\.\s)')
SIG = re.compile(r'(?i)L[il1][eoa]?[un]?[ta]?t?\.?\s*-?\s*[-.*(]?\s*-?\s*(Go|Gk|G\(|Gtov|Gov|GoT|Gr|6o|\(jk)')
TAILSIG = re.compile(r'(?i)(L[il1][eoa]?[un]?[ta]?t?\.?\s*-?\s*[-.*(]?\s*-?\s*(Go|Gk|G\(|Gtov|Gov|GoT|Gr|6o|\(jk)'
                     r'|Atty\.?\s*-?\s*Gen|Clerk of the [BR]oll|Archd|Vicar-Gen|Deemster\.?$|Speaker\.?$|^The Keys\.?$)')
CERT = re.compile(r'(?i)(before-written Act|this day promulgated|promulgated and published|this day read at the Board)')
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october',
          'november', 'december']
ORD = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5, 'sixth': 6, 'seventh': 7, 'eighth': 8,
       'ninth': 9, 'tenth': 10, 'eleventh': 11, 'twelfth': 12, 'thirteenth': 13, 'fourteenth': 14, 'fifteenth': 15,
       'sixteenth': 16, 'seventeenth': 17, 'eighteenth': 18, 'nineteenth': 19, 'twentieth': 20,
       'twenty-first': 21, 'twenty-second': 22, 'twenty-third': 23, 'twenty-fourth': 24, 'twenty-fifth': 25,
       'twenty-sixth': 26, 'twenty-seventh': 27, 'twenty-eighth': 28, 'twenty-ninth': 29, 'thirtieth': 30,
       'thirty-first': 31}


def lev1(a, b):
    """True when a and b differ by at most one edit."""
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) <= 1
    if len(a) > len(b):
        a, b = b, a
    for i in range(len(b)):
        if a == b[:i] + b[i + 1:]:
            return True
    return False


def month_of(w):
    w = re.sub(r'[^a-z]', '', w.lower())
    hits = [i for i, m in enumerate(MONTHS) if lev1(w, m)]
    return hits[0] + 1 if len(hits) == 1 else None


def dates_in(text):
    """Every certain '<day> [day of] <Month>[,] <year>' in text: (y, m, d, span)."""
    out = []
    for m in re.finditer(r"(?i)\b([0-9]{1,2})(st|nd|rd|th|d)?\s+(d[a-z]{1,3}\s+[a-z<^(]{1,2}\s+)?([A-Za-z]{3,10})[.,^]?\s*[.,^]?\s+([0-9]{4})\b", text):
        d, mon, y = int(m.group(1)), month_of(m.group(4)), int(m.group(5))
        if mon and 1 <= d <= 31 and 1400 <= y <= 1975:
            out.append((y, mon, d, m.span()))
    for m in re.finditer(r"(?i)\b(" + '|'.join(sorted(ORD, key=len, reverse=True)) + r")\s+day\s+of\s+([A-Za-z]{3,10})[.,]?\s+([0-9]{4})\b", text):
        d, mon, y = ORD[m.group(1).lower()], month_of(m.group(2)), int(m.group(3))
        if mon:
            out.append((y, mon, d, m.span()))
    return sorted(out, key=lambda x: x[3])


def valid(y, m, d):
    import datetime
    try:
        datetime.date(y, m, d)
        return True
    except ValueError:
        return False


def main():
    pages = json.load(open(sys.argv[1], encoding='utf-8'))
    first, last = int(sys.argv[2]), int(sys.argv[3])
    seq = []  # (leaf, Line, L, R)
    import statistics
    ref = {}
    for par in (0, 1):
        es = [gill_lines.edges(pages[k]) for k in range(first, last + 1) if k % 2 == par]
        es = [e for e in es if e]
        ref[par] = (statistics.median(e[0] for e in es), statistics.median(e[1] for e in es))
    for leaf in range(first, last + 1):
        ls, L, R = gill_lines.lines(pages[leaf], ref[leaf % 2])
        for x in ls:
            seq.append((leaf, x, L, R))
    starts = [k for k, (_, x, _, _) in enumerate(seq) if TOWIT.search(x.text) and len(x.text) < 40]
    acts = []
    for n, s in enumerate(starts):
        e = starts[n + 1] if n + 1 < len(starts) else len(seq)
        block = seq[s + 1:e]
        # title and body
        t0 = next((k for k, it in enumerate(block[:20]) if TITLE.match(it[1].text)), None)
        if t0 is None:
            acts.append({'leaf': seq[s][0], 'error': 'no title line', 'head': [it[1].text for it in block[:8]]})
            continue
        b0 = next((k for k in range(t0 + 1, min(len(block), t0 + 8)) if BODY.match(block[k][1].text)), None)
        if b0 is None:
            b0 = t0 + 1
            while b0 < len(block) and block[b0][1].height >= 80 and b0 < t0 + 5:
                b0 += 1
        title = ' '.join(it[1].text for it in block[t0:b0])
        caption = ' '.join(it[1].text for it in block[:t0])
        # end of the text: the first signature line (and any right-placed short lines just before it), or the
        # first certificate line
        end = len(block)
        for k in range(b0, len(block)):
            leaf, x, L, R = block[k]
            right_placed = x.left > L + (R - L) * 0.25 and x.right - x.left < (R - L) * 0.7
            # the signature block: the Governor's line, or a right-placed name line with "The Keys." soon after
            keys_soon = right_placed and ',' in x.text and len(x.text) < 70 and any(
                re.match(r'(?i)^\W{0,3}The\s+Key', block[j][1].text) for j in range(k + 1, min(len(block), k + 14)))
            if (SIG.search(x.text) and (right_placed or len(x.text) < 90)) or keys_soon or CERT.search(x.text) \
                    or re.match(r'(?i)^\W{0,3}The\s+Key[as]\W{0,2}$', x.text):
                end = k
                while end > b0:
                    _, px, pL, pR = block[end - 1]
                    if px.left > pL + (pR - pL) * 0.25 and px.right - px.left < (pR - pL) * 0.6 and \
                            re.search(r'[A-Z][a-z]*\.?\s*[A-Z]', px.text) and ',' in px.text:
                        end -= 1
                    else:
                        break
                break
        body = block[b0:end]
        # schedules are printed after the signatures: from a SCHEDULE heading to the Order in Council / certificate
        sched = []
        k0 = next((k for k in range(end, len(block)) if CERT.search(block[k][1].text)
                   or re.search(r'(?i)At\s+the\s+C[a-z]{2,3}[a-zA-Z]?\s+at\b|^P[RSB][EB]+[SN]+[EB]*[NH]+T|Q[una][e]+n.{0,4}s\s+most\s+[EeKk]x', block[k][1].text)), len(block))
        ks = next((k for k in range(end, k0) if re.match(r'(?i)^\W{0,3}SCHEDULES?\b', block[k][1].text)), None)
        if ks is not None:
            sched = block[ks:k0]
        tail = ' '.join(it[1].text for it in block[end:])
        # promulgation certificate
        prom = assent = None
        # the certificate: "At a Tynwald Court holden at <place>, the <day>. The before-written Act ... having
        # received the Royal Assent ... the <day> ... was this day promulgated"
        cm = re.search(r'(?i)(be\s*fore|fore)\s*-?\s*(written|going)\s+A|fore[gf]+o[il1]ng\s+A[ce]t', tail)
        cert_ok = bool(re.search(r'(?i)this\s+d[a-z]{1,3}\s+promulgat', tail))
        if cm and cert_ok:
            win = tail[max(0, cm.start() - 200):cm.start()]
            if re.search(r'(?i)(holden|hold[eo]n|hoUUn|kolden|holdm|hdden|kdden|hotden|Court)', win):
                ds = dates_in(win)
                if ds:
                    y, mo, d, _ = ds[-1]
                    if valid(y, mo, d):
                        prom = f'{y:04d}-{mo:02d}-{d:02d}'
        # Royal Assent: the certificate's "having received the Royal Assent, at the Court at X, the <day>" and the
        # Order in Council's own heading "At the Court at X, the <day>"; both read where legible, and they must agree
        seen = set()
        for am in re.finditer(r'(?i)(R[oua]yal\s+A[a-z ]{2,5}nt|At\s+the\s+C[a-z]{2,3}[a-zA-Z]?\s+at)(.{0,110})', tail):
            ds = dates_in(am.group(2))
            if ds:
                y, mo, d, _ = ds[0]
                if valid(y, mo, d):
                    seen.add(f'{y:04d}-{mo:02d}-{d:02d}')
        cap_year = re.findall(r'\b(1[78]\d\d)\b', title + ' ' + caption)
        if len(seen) == 1:
            assent = seen.pop()
        elif len(seen) > 1:
            assent = None
        paras = paragraphs([caption] if caption else [], title, body)
        if sched:
            paras += paragraphs([], None, sched)
        held = None
        basis = 'promulgation'
        if prom and assent and assent > prom:
            prom = None
        if not prom:
            if assent:
                basis = 'assent'
            else:
                held = ('Royal Assent days read disagree: ' + ', '.join(sorted(seen))) if len(seen) > 1 else \
                    'neither the promulgation day nor the Royal Assent day is legible in the text layer'
        day = prom or assent
        lo, hi = int(sys.argv[5]), int(sys.argv[6])  # the volume's span of years
        if day and not lo <= int(day[:4]) <= hi:
            held, day = f'day read ({day}) outside the volume ({lo}-{hi}): a misread year', None
        # signature lines that ran into the text's last paragraphs
        while len(paras) > 2 and len(paras[-1]) < 160 and (TAILSIG.search(paras[-1]) or re.search(
                r'(?i)(\bL[il1]?[eiao]{0,3}n?[ut]?\.?\W{0,3}(G|O|6|\()|\bMr\.|\bEarl\b|\bDuke\b|\bLord\b|\bKarl\b|^A[ti] a T|W\.\s*B\.|Majest|^P\w{4,6}\s*:|At the C|^[A-Z][a-z]{0,4}\.\s+[A-Z]\.?\s*[A-Z]?\w*\.?$|The Keys)', paras[-1])):
            paras.pop()
        if day and not re.search(r'''[.:;"'*)\]]\W{0,4}$''', paras[-1]):
            held, day = 'the text read ends mid-sentence (its end was not found)', None
        # the text must end close to its certificate: signatures and the Order in Council take a page or two
        text_end_leaf = (sched[-1][0] if sched else (block[end - 1][0] if end else seq[s][0]))
        cert_leaf = next((it[0] for it in block[end:] if CERT.search(it[1].text)), None)
        if day and (cert_leaf is None or cert_leaf - text_end_leaf > 3):
            held, day = 'the text read may stop short of the Act\'s end (more than 3 pages before its certificate)', None
        ncert = len(re.findall(r'(?i)this\s+d[a-z]{1,3}\s+promulgat', tail))
        if day and ncert > 1:
            held, day = f'{ncert} promulgation certificates in one block: an Act start was missed', None
        acts.append({'leaf': seq[s][0], 'end_leaf': block[end - 1][0] if end else seq[s][0],
                     'title': clean(title), 'promulgated': prom, 'assent': assent, 'held': held,
                     'day': day, 'basis': basis if day else None,
                     'schedule': bool(sched), 'paragraphs': paras, 'tail': tail})
    json.dump({'acts': acts}, open(sys.argv[4], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(acts), 'acts;', sum(1 for a in acts if a.get('promulgated')), 'with a promulgation day')


def clean(s):
    s = re.sub(r'\s*\((\d{1,2}|l|I|\*|i)\)', '', s)  # footnote reference markers
    s = re.sub(r'\s+([,.;:])', r'\1', s)
    s = re.sub(r'\s{2,}', ' ', s)
    return s.strip()


def paragraphs(caption, title, body):
    out = [clean(c) for c in caption] + (['# ' + clean(title)] if title else [])
    cur = ''
    prev = None
    for leaf, x, L, R in body:
        width = R - L
        indented = x.left > L + 55
        centered = x.left > L + width * 0.2 and x.right < R - width * 0.15
        new = cur == '' or centered or (indented and not (prev is not None and prev_continues(prev)))
        if prev is not None and (prev[1].right < prev[3] - width * 0.08):
            new = True  # the previous line ended short of the column: its paragraph ended
        if new and cur:
            out.append(clean(cur))
            cur = ''
        t = x.text
        if cur.endswith('-') and t[:1].islower():
            cur = cur[:-1] + t
        else:
            cur = (cur + ' ' + t) if cur else t
        if centered:
            out.append(clean(cur))
            cur = ''
            prev = None
            continue
        prev = (leaf, x, L, R)
    if cur:
        out.append(clean(cur))
    return [p for p in out if p]


def prev_continues(prev):
    return prev[1].text.endswith('-')


if __name__ == '__main__':
    main()
