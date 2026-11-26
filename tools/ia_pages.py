"""Archive.org djvu.xml -> pages with word boxes, in leaf order.

    python -I ia_pages.py <djvu.xml> <out.json>

Each page: {"w": width, "h": height, "lines": [[[l, t, r, b, word], ...], ...]}.
"""
import json
import sys
import xml.etree.ElementTree as ET


def pages(path):
    out = []
    for ev, el in ET.iterparse(path, events=('end',)):
        if el.tag == 'OBJECT':
            w = int(el.get('width') or 0)
            h = int(el.get('height') or 0)
            lines = []
            for ln in el.iter('LINE'):
                ws = []
                for wd in ln.iter('WORD'):
                    t = (wd.text or '').strip()
                    if not t:
                        continue
                    c = [int(x) for x in (wd.get('coords') or '0,0,0,0').split(',')[:4]]
                    l, b, r, tp = c  # djvu coords: left, bottom, right, top
                    ws.append([l, tp, r, b, t])
                if ws:
                    lines.append(ws)
            out.append({'w': w, 'h': h, 'lines': lines})
            el.clear()
    return out


if __name__ == '__main__':
    p = pages(sys.argv[1])
    with open(sys.argv[2], 'w', encoding='utf-8') as f:
        json.dump(p, f, ensure_ascii=False)
    print(len(p), 'pages')
