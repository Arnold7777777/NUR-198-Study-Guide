"""Exam and module context for Look It Up (27 Oct).

    python3 tools/build-lookup-context.py            write both files
    python3 tools/build-lookup-context.py --check    exit 1 if either is out of date

Look It Up searched NUR 198 with no idea which exam or module a result belonged to. This
writes what it needs, from the same two sources of truth the rest of the course uses:
- assets/nur198-nav/page-context.json: every lesson page the Study Hub files under a
  module (via wire-context-bar.py's reading of the hub), plus each module's name and exam.
- quiz-bank.json: an "m" (module) on each Mega Quiz question, copied from the Mega Quiz,
  matched on the question text. Questions with no module (dosage, NGN, ATI) get none.
Re-run it after changing the hub's module lists or the Mega Quiz's tags.
"""
import json, os, re, sys

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CTX = os.path.join(R, 'assets', 'nur198-nav', 'page-context.json')
QB = os.path.join(R, 'quiz-bank.json')
QUIZ = os.path.join(R, 'NUR198 Mega Quiz.html')
SRC = 'NUR 198 Mega Quiz'


def course():
    p = os.path.join(R, 'tools', 'wire-context-bar.py')
    ns = {'__file__': p, '__name__': 'wcb'}
    exec(compile(open(p, encoding='utf-8').read().replace('\nmain()\n', '\n'), p, 'exec'), ns)
    return ns


def context():
    ns = course()
    exams, mods, _ = ns['course']()
    plain = lambda t: ns['html'].unescape(re.sub('<[^>]+>', '', t))
    out = {'mods': {}, 'pages': {}}
    for n, m in sorted(mods.items()):
        out['mods'][str(n)] = {'n': plain(m['name']), 'e': plain(m['exam'][1])}
        for p in m['pages']:
            out['pages'].setdefault(p, []).append(n)
    return json.dumps(out, ensure_ascii=False, indent=1) + '\n'


def bank():
    s = open(QUIZ, encoding='utf-8').read()
    i = s.find('const QUIZ=') + len('const QUIZ=')
    mod = {q['q']: q['mod'] for q in json.JSONDecoder().raw_decode(s, i)[0]}
    qb = json.load(open(QB, encoding='utf-8'))
    for x in qb:
        x.pop('m', None)
        if x.get('src') == SRC and mod.get(x['q'], 0) > 0:
            x['m'] = mod[x['q']]
    return json.dumps(qb, ensure_ascii=False, separators=(',', ':'))


def main():
    check = '--check' in sys.argv
    stale = []
    for path, new in ((CTX, context()), (QB, bank())):
        old = open(path, encoding='utf-8').read() if os.path.exists(path) else None
        if old != new:
            stale.append(os.path.relpath(path, R))
            if not check: open(path, 'w', encoding='utf-8').write(new)
    if check:
        print('%s out of date' % ', '.join(stale) if stale else 'look-it-up context current'); sys.exit(1 if stale else 0)
    print('wrote %s' % (', '.join(stale) or 'nothing (already current)'))


main()
