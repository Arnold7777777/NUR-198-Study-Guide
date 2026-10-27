"""Module tags and a module filter on NUR198 Medications.html (27 Oct).

    python3 tools/wire-med-modules.py            write / refresh the tags, the bar and its script
    python3 tools/wire-med-modules.py --check    exit 1 if the page is out of date
    python3 tools/wire-med-modules.py --remove   take it all off again
    python3 tools/wire-med-modules.py --list     print the evidence behind every tag

The Medications page is shared by every module, and nothing on it said which module a drug
belongs to. The tags come from evidence, not from memory:
- the lesson pages the Study Hub lists under exactly one module (a guide shared by a whole
  exam can't say which of its modules a drug came from, so those are left out), and
- the Mega Quiz questions, which carry a real module since 27 Oct.
A module is tagged when its lessons mention the drug twice, its questions twice, or once
each. A drug with no evidence gets no tag; it still shows under "All".
Never hand-edit the data-mods attributes, the medmods spans, or the marked blocks.
"""
import collections, html, json, os, re, sys

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(R, 'NUR198 Medications.html')
QUIZ = os.path.join(R, 'NUR198 Mega Quiz.html')

# the same short names the Mega Quiz's module chips use
LABEL = {1: 'Older Adult', 2: 'Fluid/Lyte', 3: 'Periop/Pain/Skin', 4: 'Upper Resp', 5: 'Lower Resp & Chest',
         6: 'Chronic Pulm', 7: 'Coronary/HTN', 8: 'HF/Valves/Vascular', 9: 'Renal', 10: 'Hepatobiliary',
         11: 'Upper GI', 12: 'Lower GI', 13: 'MSK'}

# what to look for when a card's title is not just drug names
ALIAS = {
    'Regular (SHORT)': ['regular insulin'], 'NPH (INTERMEDIATE)': ['NPH'],
    'Lispro/Aspart (RAPID)': ['lispro', 'aspart', 'rapid-acting insulin'], 'Glargine/Detemir (LONG)': ['glargine', 'detemir'],
    'Aluminum/Magnesium antacids': ['antacid', 'aluminum hydroxide', 'magnesium hydroxide'],
    'Potassium chloride (IV/PO)': ['potassium chloride', 'KCl'],
    'Azathioprine / 6-MP & Biologics (infliximab)': ['azathioprine', '6-MP', 'mercaptopurine', 'infliximab', 'adalimumab'],
    'Pancrelipase (pancreatic enzymes)': ['pancrelipase', 'pancreatic enzyme'],
    'Apixaban / Rivaroxaban (DOAC)': ['apixaban', 'rivaroxaban', 'DOAC'],
    'Isoniazid (INH)': ['isoniazid', 'INH'], 'Heparin (IV/SC)': ['heparin'], 'Enoxaparin (LMWH)': ['enoxaparin', 'LMWH'],
    'Docusate, Polyethylene glycol, Bisacodyl': ['docusate', 'polyethylene glycol', 'bisacodyl'],
    'Mesalamine / Sulfasalazine (5-ASA)': ['mesalamine', 'sulfasalazine'],
    'Fluticasone (ICS), Prednisone (oral)': ['fluticasone', 'prednisone', 'budesonide', 'beclomethasone', 'inhaled corticosteroid'],
    'Morphine (opioid)': ['morphine'], 'Ibuprofen/Ketorolac (NSAID)': ['ibuprofen', 'ketorolac', 'NSAID'],
    'Amlodipine (-dipine), Diltiazem, Verapamil': ['amlodipine', 'nifedipine', 'diltiazem', 'verapamil', 'calcium channel blocker'],
    'Albuterol (SABA)': ['albuterol'], 'Salmeterol (LABA)': ['salmeterol', 'formoterol'], 'Ipratropium': ['ipratropium', 'tiotropium'],
}

MED = re.compile(r'<details class="med"(?: data-mods="[^"]*")?><summary>(.*?)</summary>', re.S)
SPAN = re.compile(r'<span class="medmods"[^>]*>.*?</span>')
BAR = re.compile(r'<!-- medmods-bar -->.*?<!-- /medmods-bar -->\n?', re.S)
CSSB = re.compile(r'<style id="medmods-css">.*?</style>\n?', re.S)
CTX_CSS = '<link rel="stylesheet" href="assets/nur198-nav/context.css">'
CTX_JS = '<script src="assets/nur198-nav/context.js"></script>'
JSB = re.compile(r'<script id="medmods-js">.*?</script>\n?', re.S)


def course():
    src = open(os.path.join(R, 'tools', 'wire-context-bar.py'), encoding='utf-8').read()
    ns = {'__file__': os.path.join(R, 'tools', 'wire-context-bar.py'), '__name__': 'wcb'}
    exec(compile(src.replace('\nmain()\n', '\n'), 'wire-context-bar.py', 'exec'), ns)
    return ns['course']()[1]


def text(p):
    s = open(os.path.join(R, p), encoding='utf-8').read()
    s = re.sub(r'<!-- n198ctx -->.*?<!-- /n198ctx -->|<!-- n198ctx-end -->.*?<!-- /n198ctx-end -->', '', s, flags=re.S)
    s = re.sub(r'<(style|script)\b.*?</\1>', '', s, flags=re.S)
    return html.unescape(re.sub('<[^>]+>', ' ', s))


def terms(name):
    if name in ALIAS: return ALIAS[name]
    return [t.strip() for t in re.split(r'[,/]', re.sub(r'\([^)]*\)', '', name)) if t.strip()]


def finder(name):
    T = terms(name)
    abbr = [re.escape(t) for t in T if re.fullmatch(r'[A-Z0-9-]{2,6}', t)]       # INH, NPH: whole word, exact case
    word = [re.escape(t) for t in T if not re.fullmatch(r'[A-Z0-9-]{2,6}', t)]
    parts = ([r'(?i:\b(?:%s))' % '|'.join(word)] if word else []) + ([r'\b(?:%s)\b' % '|'.join(abbr)] if abbr else [])
    return re.compile('|'.join(parts))


def card_name(summary):
    return html.unescape(re.sub(r'<span class="(?:habadge|medmods)"[^>]*>.*?</span>', '', summary)).strip()


def evidence(s):
    mods = course()
    once = collections.Counter(p for m in mods.values() for p in m['pages'])
    lessons = {n: ' '.join(text(p) for p in m['pages'] if once[p] == 1) for n, m in mods.items()}
    q = open(QUIZ, encoding='utf-8').read()
    i = q.find('const QUIZ=') + len('const QUIZ=')
    quiz = collections.defaultdict(list)
    for x in json.JSONDecoder().raw_decode(q, i)[0]:
        if x['mod'] > 0:
            quiz[x['mod']].append(' '.join([x['q']] + [str(o) for o in x.get('o', [])] + [str(x.get('r', ''))]))
    out = {}
    for m in MED.finditer(s):
        name = card_name(m.group(1)); rx = finder(name); row = {}
        for n in sorted(mods):
            a = len(rx.findall(lessons[n])); b = sum(1 for t in quiz[n] if rx.search(t))
            if a or b: row[n] = (a, b)
        keep = [n for n, (a, b) in row.items() if a >= 2 or b >= 2 or (a and b)]
        out[name] = (keep, row)
    return out


def strip(s):
    s = re.sub(r'<details class="med" data-mods="[^"]*">', '<details class="med">', s)
    s = SPAN.sub('', s)
    return JSB.sub('', CSSB.sub('', BAR.sub('', s)))


def build(s, ev):
    def tag(m):
        keep = ev[card_name(m.group(1))][0]
        if not keep: return '<details class="med" data-mods=""><summary>%s</summary>' % m.group(1)
        span = '<span class="medmods" title="Comes up in %s">%s</span>' % (
            ', '.join('Module %d' % n for n in keep), ' &middot; '.join('M%d' % n for n in keep))
        return '<details class="med" data-mods="%s"><summary>%s%s</summary>' % (' '.join(map(str, keep)), m.group(1), span)
    s = MED.sub(tag, s)
    used = sorted({n for k, _ in ev.values() for n in k})
    btns = ['<button type="button" class="mmbtn" data-m="" aria-pressed="true">All drugs</button>'] + [
        '<button type="button" class="mmbtn" data-m="%d" aria-pressed="false"><b>M%d</b> %s</button>' % (n, n, html.escape(LABEL[n]))
        for n in used]
    bar = ('<!-- medmods-bar --><div class="medmods-bar" id="medmods" role="group" aria-label="Show the drugs for one module">'
           '<p class="mmhead">Show the drugs for one module</p><div class="mmrow">%s</div>'
           '<p class="mmnote" id="medmodsNote" aria-live="polite">Each card shows the modules it comes up in, from that '
           'module&rsquo;s lessons and quiz questions.</p></div><!-- /medmods-bar -->\n') % ''.join(btns)
    s = s.replace(' <div class="jump">', bar + ' <div class="jump">', 1)
    # ahead of the context bar's own link and script, which wire-context-bar.py keeps last
    css_at = CTX_CSS if CTX_CSS in s else '</head>'
    js_at = CTX_JS if CTX_JS in s else '</body>'
    s = s.replace(css_at, CSS + css_at, 1)
    return s.replace(js_at, JS + js_at, 1)


CSS = '''<style id="medmods-css">
.medmods{font-size:.8rem;font-weight:800;color:#cfe0ff;background:#2c3566;border:1px solid #5b6cc0;border-radius:20px;padding:2px 9px}
.medmods-bar{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin:0 0 14px}
.mmhead{margin:0 0 8px;font-weight:800;color:var(--gold)}
.mmrow{display:flex;flex-wrap:wrap;gap:8px}
.mmbtn{min-height:44px;padding:6px 13px;border-radius:22px;border:1px solid var(--line);background:#2b2050;color:var(--ink);
  font-size:.9rem;font-family:inherit;cursor:pointer;text-align:left}
.mmbtn b{color:var(--gold)}
.mmbtn[aria-pressed="true"]{background:var(--gold);color:#2a1f00;border-color:var(--gold)}
.mmbtn[aria-pressed="true"] b{color:#2a1f00}
.mmbtn:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
.mmnote{margin:10px 0 0;font-size:.9rem;color:var(--soft)}
.modhide{display:none!important}
</style>
'''

JS = '''<script id="medmods-js">
/* One module at a time; "All drugs" is the plain reference again. A class heading and a
   body-system heading go too when nothing under them is left. The search box keeps its own
   'hide' class, so the two never undo each other. Nothing is saved. */
(function(){
  var bar=document.getElementById('medmods'); if(!bar) return;
  var note=document.getElementById('medmodsNote'), first=note.innerHTML;
  var meds=[].slice.call(document.querySelectorAll('details.med[data-mods]'));
  function pick(m){
    [].forEach.call(bar.querySelectorAll('.mmbtn'),function(b){ b.setAttribute('aria-pressed', b.dataset.m===m?'true':'false'); });
    var shown=0;
    meds.forEach(function(d){
      var on=!m || (' '+d.dataset.mods+' ').indexOf(' '+m+' ')>-1;
      d.classList.toggle('modhide',!on); if(on) shown++;
    });
    [].forEach.call(document.querySelectorAll('.grp'),function(g){
      var ds=g.querySelectorAll('details.med[data-mods]');
      g.classList.toggle('modhide', !!m && ds.length>0 && g.querySelectorAll('details.med[data-mods]:not(.modhide)').length===0);
    });
    [].forEach.call(document.querySelectorAll('h2.sys'),function(h){
      var any=false, n=h.nextElementSibling;
      while(n && !(n.tagName==='H2')){ if(n.classList.contains('grp') && !n.classList.contains('modhide')) any=true; n=n.nextElementSibling; }
      h.classList.toggle('modhide', !!m && !any);
    });
    var b=bar.querySelector('.mmbtn[data-m="'+m+'"]');
    note.innerHTML = m ? 'Showing <b>'+shown+'</b> of '+meds.length+' drug cards for <b>'+b.innerHTML.replace(/<[^>]+>/g,'')+
      '</b>. The rest are only hidden &mdash; tap <b>All drugs</b> to see every card.' : first;
  }
  bar.addEventListener('click',function(e){ var b=e.target.closest('.mmbtn'); if(b) pick(b.dataset.m); });
})();
</script>
'''


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    s = open(PAGE, encoding='utf-8').read()
    base = strip(s)
    if mode == '--remove':
        new = base
    else:
        ev = evidence(base)
        if mode == '--list':
            for name, (keep, row) in ev.items():
                print('%-44s %-22s %s' % (name[:44], ' '.join('M%d' % n for n in keep),
                                          '  '.join('M%d:%d/%d' % (n, a, b) for n, (a, b) in row.items())))
            print('(lesson mentions / quiz questions)'); return
        new = build(base, ev)
    if mode == '--check':
        print('medications page current' if new == s else 'medications page out of date'); sys.exit(0 if new == s else 1)
    if new != s: open(PAGE, 'w', encoding='utf-8').write(new)
    print('%s; %d drug cards' % ('removed' if mode == '--remove' else 'wrote', len(MED.findall(new))))


main()
