#!/usr/bin/env python3
"""Decode HTML entities left raw in search-index.json.

The bug it fixes
----------------
This index was built without unescaping, so entities reached the search results
as literal text: a hit for a range rendered as "1&ndash;6" rather than "1-6",
and &rarr; &bull; &times; &deg; showed as source. 1,557 of them across the file.

DO NOT "fix" this by regenerating the index from this repo.
------------------------------------------------------------
This one file indexes FIVE of her sites, not just NUR 198:

    198  NUR 198      46 pages   2,428 entries
    lab  Labs & Dx    12 pages     262 entries
    drug Drug Guide    6 pages     121 entries
    125  NUR 125      16 pages     127 entries
    175  NUR 175       4 pages     637 entries

ABSN-Study-Hub's index.html merges this file with its own, so regenerating it
from any single repo silently drops the other four sites from the hub search -
38 pages and 1,147 entries. Repair the file in place, which is what this does.

Idempotent: running it on an already-clean index changes nothing.

    python3 tools/fix-index-entities.py            # repair
    python3 tools/fix-index-entities.py --check    # exit 1 if any remain
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'search-index.json')
ENTITY = re.compile(r'&[A-Za-z][A-Za-z0-9]{1,31};|&#[0-9]{1,7};|&#[xX][0-9A-Fa-f]{1,6};')


def clean(node):
    if isinstance(node, str):
        # unescape repeatedly: "&amp;ndash;" is one pass away from "&ndash;"
        prev, cur = None, node
        for _ in range(4):
            if cur == prev:
                break
            prev, cur = cur, html.unescape(cur)
        return cur
    if isinstance(node, list):
        return [clean(x) for x in node]
    if isinstance(node, dict):
        return {k: clean(v) for k, v in node.items()}
    return node


def main():
    with open(PATH, encoding='utf-8') as fh:
        data = json.load(fh)
    before = len(ENTITY.findall(json.dumps(data, ensure_ascii=False)))
    fixed = clean(data)
    blob = json.dumps(fixed, ensure_ascii=False, separators=(',', ':'))
    after = len(ENTITY.findall(blob))

    # the repair must not change the shape of the index
    assert len(fixed['sites']) == len(data['sites']), 'lost a site'
    assert len(fixed['pages']) == len(data['pages']), 'lost a page'
    assert len(fixed['entries']) == len(data['entries']), 'lost an entry'

    if '--check' in sys.argv:
        print('%d entities remain' % after)
        return 1 if after else 0
    with open(PATH, 'w', encoding='utf-8') as fh:
        fh.write(blob)
    print('%d sites, %d pages, %d entries | entities %d -> %d'
          % (len(fixed['sites']), len(fixed['pages']), len(fixed['entries']), before, after))
    return 0


if __name__ == '__main__':
    sys.exit(main())
