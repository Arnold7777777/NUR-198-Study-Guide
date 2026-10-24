"""Exam -> Module context on every NUR 198 lesson page (24 Oct).

    python3 tools/wire-context-bar.py            write / refresh the bars
    python3 tools/wire-context-bar.py --check    exit 1 if any page is out of date
    python3 tools/wire-context-bar.py --remove   take the bars off again

Everything comes from the Study Hub's "By exam -> module" section, so the hub stays the one
place the course is organized: edit a module's links there and re-run this.
- A page listed under one or more modules gets a breadcrumb (Study Hub > Exam > Module),
  a way back to its module, a "Change module" list, and previous/next lesson in course order.
- Any other active page is a shared tool: it gets the hub link, "Change module", and
  (from absn-context.js) a "Back to Module N" for the module she came from.
Never hand-edit between the <!-- n198ctx --> markers.
"""
import html, os, re, sys, urllib.parse

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUB = 'NUR198 Study Hub.html'
SKIP = {HUB, 'index.html', 'Visual Index.html', 'NUR198 ATI Visual Reference.html',     # hub, redirect, retired
        'NUR198 Study Video Playlist.html'}                                               # a 'this playlist was removed' notice
APP = re.compile(r'body\{[^}]*display:flex;flex-direction:column;height:100vh')            # full-screen tabbed guides
FRAMED = '<script>if(window.top!==window.self)document.currentScript.previousElementSibling.remove()</script>'
CSS = 'assets/nur198-nav/context.css'
JS = 'assets/nur198-nav/context.js'
TOP = re.compile(r'\n<!-- n198ctx -->.*?<!-- /n198ctx -->', re.S)
BOT = re.compile(r'<!-- n198ctx-end -->.*?<!-- /n198ctx-end -->\n?', re.S)
q = lambda p: urllib.parse.quote(p)
esc = lambda t: html.escape(html.unescape(t), quote=False)

def course():
    s = open(os.path.join(R, HUB), encoding='utf-8').read()
    exams, mods, order = [], {}, []
    for e in re.finditer(r'<div class="exsec" id="(e\w+)">\s*<div class="exhead"><span class="en">(.*?)</span><span class="et">(.*?)</span>', s):
        exams.append((e.group(1), re.sub('<[^>]+>', '', e.group(2)), re.sub(r'\s*&mdash;.*', '', e.group(3))))
    for m in re.finditer(r'<details class="modblk" id="m(\d+)">.*?<span class="mt">(.*?)</span>.*?</summary><div class="inner">(.*?)</div></details>', s, re.S):
        n = int(m.group(1))
        ex = [e for e in exams if e[0] == s[:m.start()].rsplit('<div class="exsec" id="', 1)[1].split('"')[0]][0]
        pages = []
        for a in re.finditer(r'<a href="([^"#]+)">', m.group(3)):      # lesson links only: recordings and pictures carry a class
            p = urllib.parse.unquote(a.group(1))
            if '/' not in p and os.path.exists(os.path.join(R, p)) and p not in pages: pages.append(p)
        mods[n] = {'name': m.group(2), 'exam': ex, 'pages': pages}
        for p in pages:
            if p not in order: order.append(p)
    return exams, mods, order

def title(p):
    s = open(os.path.join(R, p), encoding='utf-8').read()
    t = re.search(r'<title>(.*?)</title>', s, re.S)
    t = re.sub(r'\s+', ' ', html.unescape(t.group(1))).strip() if t else p[:-5]
    t = t.split(' | ')[0]
    return re.sub(r'^NUR ?198[\s:·—-]*', '', t) or p[:-5]

def switcher(exams, mods):
    out = ['<details class="n198-switch"><summary>Change module</summary><div class="n198-mods">']
    for eid, en, et in exams:
        out.append('<p class="n198-ex"><a href="%s#%s">%s &middot; %s</a></p>' % (q(HUB), eid, esc(en), esc(et)))
        for n, m in sorted(mods.items()):
            if m['exam'][0] == eid:
                out.append('<a href="%s#m%d"><b>M%d</b> %s</a>' % (q(HUB), n, n, esc(m['name'])))
    out.append('</div></details>')
    return ''.join(out)

def bars(p, exams, mods, order, app=False):
    mine = [n for n, m in sorted(mods.items()) if p in m['pages']]
    hub = '<a class="n198-hub" href="%s">NUR 198 Study Hub</a>' % q(HUB)
    sw = switcher(exams, mods)
    if not mine:
        top = ('<div class="n198ctx" role="navigation" aria-label="Course navigation" data-shared="1">'
               '<p class="n198-crumb">%s <span aria-hidden="true">&rsaquo;</span> <span>Shared across all modules</span></p>'
               '<div class="n198-row"><a class="n198-back" href="%s#byexam" hidden>&larr; Back to your module</a>%s</div></div>') % (hub, q(HUB), sw)
        return top, ''
    exs = []
    for n in mine:
        if mods[n]['exam'] not in exs: exs.append(mods[n]['exam'])
    crumb_ex = ' / '.join('<a href="%s#%s">%s &middot; %s</a>' % (q(HUB), e[0], esc(e[1]), esc(e[2])) for e in exs)
    crumb_m = ' / '.join('<a href="%s#m%d">Module %d</a>' % (q(HUB), n, n) for n in mine)
    m0 = mine[0]
    # one module: back to it; a guide spanning a whole exam: back to that exam
    up, upname = ('m%d' % m0, 'Module %d' % m0) if len(mine) == 1 or len(exs) > 1 else (exs[0][0], esc(exs[0][1]))
    top = ('<div class="n198ctx" role="navigation" aria-label="Course navigation" data-module="%d">'
           '<p class="n198-crumb">%s <span aria-hidden="true">&rsaquo;</span> %s <span aria-hidden="true">&rsaquo;</span> %s</p>'
           '%s'
           '<div class="n198-row"><a class="n198-back" href="%s#%s">&larr; All of %s</a>%s</div></div>'
           ) % (m0 if len(mine) == 1 else 0, hub, crumb_ex, crumb_m,
                '<p class="n198-mname">%s</p>' % esc(mods[m0]['name']) if len(mine) == 1 else '', q(HUB), up, upname, sw)
    if app:      # the page is a full-screen tab layout: one folded line, no footer to eat the screen
        label = '%s &middot; %s' % (esc(exs[0][1]), crumb_m.replace('</a> / <a', '</a>, <a')) if len(exs) == 1 else crumb_ex
        top = top.replace('<div class="n198ctx" role="navigation" aria-label="Course navigation"',
                          '<details class="n198ctx n198-fold"><summary>Course navigation: %s</summary><div role="navigation" aria-label="Course navigation"' % re.sub('<[^>]+>', '', label), 1) \
                 .rsplit('</div>', 1)[0] + '</div></details>'
        return top, ''
    i = order.index(p)
    pv = order[i - 1] if i else None
    nx = order[i + 1] if i + 1 < len(order) else None
    links = []
    if pv: links.append('<a class="n198-prev" href="%s"><span>&larr; Previous lesson</span>%s</a>' % (q(pv), esc(title(pv))))
    links.append('<a class="n198-up" href="%s#%s"><span>Back to</span>%s on the Study Hub</a>' % (q(HUB), up, upname))
    if nx: links.append('<a class="n198-next" href="%s"><span>Next lesson &rarr;</span>%s</a>' % (q(nx), esc(title(nx))))
    bot = '<div class="n198ctx n198-foot" role="navigation" aria-label="Previous and next lesson">%s</div>' % ''.join(links)
    return top, bot

def pages():
    return sorted(f for f in os.listdir(R) if f.endswith('.html') and f not in SKIP
                  and 'http-equiv="refresh"' not in open(os.path.join(R, f), encoding='utf-8').read()[:4000])

def build(s, top, bot):
    s = TOP.sub('', s); s = BOT.sub('', s)
    s = s.replace('<link rel="stylesheet" href="%s">\n' % CSS, '').replace('<script src="%s"></script>\n' % JS, '')
    if top is None: return s
    s = s.replace('</head>', '<link rel="stylesheet" href="%s">\n</head>' % CSS, 1)
    b = re.search(r'<body\b[^>]*>', s).end()
    s = s[:b] + '\n<!-- n198ctx -->' + top + FRAMED + '<!-- /n198ctx -->' + s[b:]
    if bot:
        e = s.rindex('</body>')
        s = s[:e] + '<!-- n198ctx-end -->' + bot + FRAMED + '<!-- /n198ctx-end -->\n' + s[e:]
    e = s.rindex('</body>')
    return s[:e] + '<script src="%s"></script>\n' % JS + s[e:]

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    exams, mods, order = course()
    stale = []
    for p in pages():
        path = os.path.join(R, p); s = open(path, encoding='utf-8').read()
        new = build(s, None, None) if mode == '--remove' else build(s, *bars(p, exams, mods, order, bool(APP.search(s))))
        if new != s:
            stale.append(p)
            if mode != '--check': open(path, 'w', encoding='utf-8').write(new)
    if mode == '--check':
        print('%d page(s) out of date' % len(stale) if stale else 'all context bars current'); sys.exit(1 if stale else 0)
    print('%s %d page(s); %d modules, %d lessons in course order' % ('removed from' if mode else 'wrote', len(stale), len(mods), len(order)))

main()
