#!/usr/bin/env python3
"""main v250 + Book Session v102 - from the 9 Oct 11:39-11:43 Slack round on main v249 / Book Session v101 / RA v22.

  - "book 11-1 instead" (11:39): right time, room and card, but the details question was the model's own: "I need the session
    details before I can prepare this: what kind of session is it, and who's the client? The engineer is Howard Luistro, so
    I'll use that." - v247 rewrites only a reply ending in "?", so no restatement, and the project was never asked.
  - "book studio f for me tomorrow" (11:41), Studio F part-booked: the heads-up came first (right), then the model repeated it
    ("The room check says Studio F is already booked ...") and asked "what time do you need (and for how long)?" - v247
    skips any reply that starts with the heads-up.
  - "book salin on monday 12-1pm for a management meeting with sir vic" (11:41): "SALIN - Sir Vic" - the honorific kept,
    the name not the staff list's (Bookers: Vic Icasas, "Goes by Vic").

main v250 (on v249), Guard Probe:
  1. A statement after the details question about a known engineer ("The engineer is X, so I'll use that.") is dropped, so
     the question is read and rewritten; "(and for how long)" is dropped from a question.
  2. A session type asked with no project known (Booked For) asks for the project too.
  3. The early room check's heads-up is put on top AFTER the reply is shortened, and the model's own sentences restating it
     ("The room check says ...", "is already booked ...", "free 8:00 AM - ...") are dropped first.
Book Session v102 (on v101), Check Conflicts: a conference-room title segment that is a person - an honorific (sir, ma'am,
  miss, mr, ...) dropped, and a staff member's first name or "Goes by" alias written as their full Bookers name, when it is
  one person: "SALIN - Sir Vic" -> "SALIN - Vic Icasas".

  scripts/build-v250.py <main-v249> <main-out> <book-v101> <book-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

ER_TRY_OLD = "try {\n  const _er = (($('Early Room Result').first() || {}).json || {}).earlyRoom;"
ER_TRY_NEW = ("let _erPre = '';   // v250: the part-day heads-up, put on top after the reply is shortened\n" + ER_TRY_OLD)
ER_PRE_OLD = "    else if (_er.mode === 'prepend' && !/^\\s*(?:❌\\s*)?heads up:[^\\n]*already (?:booked|have)/i.test(text)) text = String(_er.text) + '\\n\\n' + text;"
ER_PRE_NEW = "    else if (_er.mode === 'prepend' && !/^\\s*(?:❌\\s*)?heads up:[^\\n]*already (?:booked|have)/i.test(text)) _erPre = String(_er.text);   // v250: added below"

V247_OLD = "    const _FILL = /^\\s*(?:(?:got it|understood|sure(?: thing)?|alright|all right|great|perfect|noted|of course|absolutely|certainly)\\b[,.!:]*\\s*(?:[-–—]\\s*)?)+/i;\n"
V247_NEW = r"""    // v250 (live 9 Oct 11:41): under the heads-up the model said it again - "The room check says Studio F is already booked
    // 3:00 PM - 6:00 PM tomorrow ..., and free 8:00 AM - 3:00 PM ..." - its sentences about what is booked or free go
    if (_erPre) text = text.split('\n').map(l => l.split(/(?<=[.!?])\s+/).filter(x => /\?\s*$/.test(x) || !/\broom check\b|\balready (?:booked|have)\b|\b(?:is|are) booked\b|\bbooked\s+(?:from\s+)?\d|\bfree\s+(?:from\s+)?\d|\bfree (?:all day|the rest)\b/i.test(x)).join(' ')).join('\n').replace(/\n{3,}/g, '\n\n').trim();
    // v250 (live 9 Oct 11:41): "what time do you need (and for how long)?" - a time range gives the length
    text = text.replace(/\s*\((?:and\s+)?(?:for\s+)?how long(?: for)?\)/gi, '');
""" + V247_OLD

TAIL_ANCHOR = "    // v249 (PENDING 103): \"Studio 7 is free then.\" before the details question"
TAIL = r"""    // v250 (live 9 Oct 11:39): "... and who's the client? The engineer is Howard Luistro, so I'll use that." - a statement
    // after the question about a known engineer (or what will be used) goes, so the question is the end of the reply
    { const _lq = text.lastIndexOf('?'), _tl = _lq > 0 ? text.slice(_lq + 1).trim() : '';
      if (_tl && _tl.length <= 160 && !/\?/.test(_tl)
          && _tl.split(/(?<=[.!])\s+/).every(x => /^(?:the engineer (?:is|will be)\b|engineer:|I(?:'|’)ll (?:use|put|set|go with)\b|I will (?:use|put|set|go with)\b|(?:so )?I(?:'|’)ll (?:use|keep) (?:that|them|him|her)\b)/i.test(x.trim())))
        text = text.slice(0, _lq + 1).trim(); }
"""
PROJ_OLD = "      if (_it.indexOf('time') !== -1 && _it.indexOf('length') !== -1) _it.splice(_it.indexOf('length'), 1);\n"
PROJ_NEW = PROJ_OLD + r"""      // v250 (live 9 Oct 11:39): a details question asking the session type, with no project known, asks for the project too
      try { const _bp = (($('Booked For').first() || {}).json) || {};
        if (_it.length >= 2 && _it.indexOf('session type') !== -1 && _it.indexOf('project') === -1 && !String(_bp.project || _bp.projectCode || '').trim())
          _it.splice(_it.indexOf('session type') + 1, 0, 'project'); } catch (e) {}
"""
FREE2_OLD = "    if (_freeSaid && !/^✅/.test(text)) text = '✅ ' + _freeSaid + ' is free\\n' + text;   // v249: not rewritten - still said by code\n  }\n} catch (e) {}\n"
FREE2_NEW = FREE2_OLD + "// v250: the early room check's part-day heads-up goes on top of the shortened reply\nif (_erPre) text = _erPre + (String(text || '').trim() ? '\\n\\n' + text : '');\n"

BS_ANCHOR = "// v51: the project segment of a studio title is in capitals (the title convention)"
BS_PERSON = r"""// v102 (live 9 Oct 11:41): "with sir vic" became "SALIN - Sir Vic". In a conference-room title a person is written as Bookers
// has them - an honorific dropped, and a first name or "Goes by" alias that is one staff member written as the full name.
try {
  let _R1 = {}; try { _R1 = JSON.parse(String(REQ.reference_data || '{}')); } catch (e) {}
  const _cf1 = ['salin', 'katha', 'likha'].concat((_R1.rooms || []).filter(r => r.common && !/lobby/i.test(String(r.name))).map(r => String(r.name).toLowerCase()));
  const _m1 = finalSummary.match(/^\s*([^-/]+?)\s+-\s+(.+?)\s*$/);
  if (_m1 && _cf1.indexOf(_m1[1].trim().toLowerCase()) !== -1) {
    let _bk1 = []; try { _bk1 = $('All Bookers').all().map(i => (i.json && i.json.fields) || {}).filter(f => f.Name); } catch (e) {}
    const _n1 = s => String(s || '').toLowerCase().replace(/[^a-z0-9 ]+/g, ' ').replace(/\s+/g, ' ').trim();
    const _who = s => {
      const k = _n1(s); if (!k) return '';
      const hit = _bk1.filter(f => _n1(f.Name) === k);
      if (hit.length === 1) return String(hit[0].Name).trim();
      const al = _bk1.filter(f => _n1(String(f.Name).split(/\s+/)[0]) === k
        || ((String(f.Info || '').match(/goes by\s+([^\n]*)/i) || [])[1] || '').split(/,|\bor\b/).map(_n1).indexOf(k) !== -1);
      return al.length === 1 ? String(al[0].Name).trim() : '';
    };
    const _sg1 = _m1[2].split(/\s+-\s+/).map(seg => {
      const bare = seg.replace(/^(?:sir|ma['’]?am|mam|miss|ms\.?|mr\.?|mrs\.?|madam|dr\.?|doc|kuya|ate)\s+/i, '').trim();
      if (bare === seg.trim()) return seg.trim();
      return _who(bare) || bare;
    });
    finalSummary = _m1[1].trim().toUpperCase() + ' - ' + _sg1.join(' - ');
  }
} catch (e) {}
"""

def main(w):
    w["name"] = "Project Jessie — v250 (v249 details + heads-up fixed)"
    gp = node(w, "Guard Probe")["parameters"]
    c = gp["jsCode"]
    for old, new, what in [(ER_TRY_OLD, ER_TRY_NEW, "erPre decl"), (ER_PRE_OLD, ER_PRE_NEW, "erPre set"), (V247_OLD, V247_NEW, "restated room check"),
                           (TAIL_ANCHOR, TAIL + TAIL_ANCHOR, "tail statements"), (PROJ_OLD, PROJ_NEW, "project"), (FREE2_OLD, FREE2_NEW, "erPre add")]:
        c = once(c, old, new, what)
    gp["jsCode"] = c
    return w

def book(w):
    w["name"] = "Jessie — Book Session — v102 (names in meeting titles)"
    cc = node(w, "Check Conflicts")["parameters"]
    cc["jsCode"] = once(cc["jsCode"], BS_ANCHOR, BS_PERSON + BS_ANCHOR, "person in title")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 4: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(book(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
