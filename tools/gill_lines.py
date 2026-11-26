"""Gill, Statutes of the Isle of Man (archive.org scans): page word boxes -> main-column lines.

Drops what is not the statute text as printed in the main column: the running head (first line, with the page
number and A.D. year), side notes in the outer margin (word groups set apart by a wide gap outside the main
column), Google's "Digitized by Google" stamp, and footnotes (the block below the widest gap at the foot of the page
that begins with a note marker).

    lines(page) -> [Line(left, top, height, text, right)], L, R
"""
import re
import statistics
from collections import namedtuple

Line = namedtuple('Line', 'left top height text right')
STAMP = re.compile(r'(?i)^(digitized|google|izid\s+by|ized\s+by|vjooq|lc\b)')
NOTE = re.compile('^[*\u2020\u2021\u00a7\u00b6]|^\\(?\\d{1,2}\\)?\\s|^[lI]\\s+[A-Z]')


def mode(xs, b=18):
    """Densest 3-bin window of positions (bin b px): the left of its densest bin's lowest member."""
    from collections import Counter
    c = Counter(int(x // b) for x in xs)
    best = max(c, key=lambda k: (c[k] + 0.5 * (c.get(k - 1, 0) + c.get(k + 1, 0)), -k))
    lo = [x for x in xs if best - 1 <= x // b <= best + 1]
    return statistics.median(lo)


def chunks(ln, gap):
    out, cur = [], [ln[0]]
    for w in ln[1:]:
        if w[0] - cur[-1][2] > gap:
            out.append(cur)
            cur = [w]
        else:
            cur.append(w)
    out.append(cur)
    return out


def edges(pg):
    ls = [ln for ln in pg['lines'] if ln]
    if not ls:
        return None
    W = pg['w'] or 3500
    R = mode([ln[-1][2] for ln in ls if len(ln) >= 4] or [ln[-1][2] for ln in ls])
    starts = [w[0] for ln in ls for w in ln[:1]] + [w[0] for ln in ls for k, w in enumerate(ln) if k and w[0] - ln[k - 1][2] > 45]
    cand = [x for x in starts if R - x >= W * 0.42]
    L = mode(cand) if cand else min(starts)
    return L, R


def lines(pg, ref=None):
    """ref: the (L, R) typical of pages of this parity, used when this page's own edges stray from it."""
    ls = [ln for ln in pg['lines'] if ln]
    if not ls:
        return [], 0, 0
    W = pg['w'] or 3500
    # justified body lines share their right edge and (continuation lines) their left edge: take the modes
    R = mode([ln[-1][2] for ln in ls if len(ln) >= 4] or [ln[-1][2] for ln in ls])
    # every word start is a candidate left edge (a side note glued to a line hides the body start inside it)
    starts = [w[0] for ln in ls for w in ln[:1]] + [w[0] for ln in ls for k, w in enumerate(ln) if k and w[0] - ln[k - 1][2] > 45]
    cand = [x for x in starts if R - x >= W * 0.42]
    L = mode(cand) if cand else min(starts)
    if ref and (abs(L - ref[0]) > 150 or abs(R - ref[1]) > 150):
        L, R = ref
    out = []
    for ln in ls:
        keep = [w for w in ln if w[0] >= L - 45 and w[0] < R + 10]
        if not keep:
            continue
        text = ' '.join(w[4] for w in keep).strip()
        if not text or STAMP.match(text):
            continue
        hts = [w[3] - w[1] for w in keep]
        out.append(Line(keep[0][0], keep[0][1], statistics.median(hts), text, keep[-1][2]))
    out.sort(key=lambda x: x.top)
    # running head: first line near the top carrying a page number or A.D. year
    while out and out[0].top < pg['h'] * 0.075 and len(out[0].text) < 70 and not out[0].text.rstrip().endswith('-') \
            and not re.search(r'(?i)to\s*W[il1]t', out[0].text):
        out = out[1:]
    # signature marks at the foot ("NN 2", "B")
    while out and out[-1].top > pg['h'] * 0.88 and len(out[-1].text) <= 8:
        out = out[:-1]
    # footnotes: below the widest vertical gap in the lower part of the page, if that block starts with a marker
    if len(out) > 4:
        gaps = []
        for k in range(1, len(out)):
            if out[k].top > pg['h'] * 0.45:
                gaps.append((out[k].top - out[k - 1].top, k))
        spacing = statistics.median([out[k].top - out[k - 1].top for k in range(1, len(out))])
        if gaps:
            g, k = max(gaps)
            if g > spacing * 1.6 and NOTE.match(out[k].text):
                out = out[:k]
    return out, L, R
