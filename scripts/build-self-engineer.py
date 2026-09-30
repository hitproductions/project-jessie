#!/usr/bin/env python3
"""Book Session v71 (self-engineer default) - decided 30 Sep 14:16 PHT (the QAANJ test).
  scripts/build-self-engineer.py <book-live> <book-out>

"book qaanj studio 7 tomorrow 2pm to 4pm, vo recording, for anj" -> "angela" -> the summary had *Engineer:* Howard
Luistro: no engineer was named, and the model put the requester in, who is an engineer. Decided: that is right - but it
was the model's choice, so it is now code. In prepare mode, a studio booking with no engineer named, not booked for a
colleague, where the requester did not say "no engineer" and is an engineer by role (Bookers Info): the requester is
the engineer, resolved like any other engineer (name, role, title initials), and the summary says so - "No engineer
was named, so you're down as the engineer. If someone else is engineering, tell me who." A requester who is not an
engineer is left as before.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label, n=1):
    if s.count(old) != n: raise SystemExit(f"{label}: expected {n} match(es), found {s.count(old)}")
    return s.replace(old, new)

ANCHOR = "// --- engineer and arranger must be real people in Bookers ----------------"
BLOCK = r"""// v71 (decided 30 Sep): no engineer named, not booked for a colleague, and the requester is an engineer -> the requester
// is the engineer. Resolved below like any named engineer (canonical name, role, title initials); the summary says so.
let __selfEngineer = '';
if (__prep && String(REQ.session_type || '').trim()) {
  const _sg = String(REQ.description || '').split('|');
  const _ei = _sg.findIndex(s => /^\s*engineer\s*:/i.test(s));
  const _e0 = (String(REQ.engineer || '').trim() || (_ei !== -1 ? _sg[_ei].replace(/^\s*engineer\s*:\s*/i, '') : '')).trim();
  const _forP = /\(for\s+[^)]+\)/i.test(String(REQ.description || ''));
  const _noEng = /\b(?:no|without(?:\s+an?)?)\s+engineer\b|\bengineer\s*(?:is|:|=)?\s*(?:none|n\/?a|tbd|tba)\b/i.test(String(REQ.requester_text || ''));
  const _me = ((String(REQ.description || '').match(/booked by\s*:\s*([^|(]+)/i) || [])[1] || '').trim();
  if (!_e0 && !_forP && !_noEng && _me) {
    let _f = null;
    try { _f = $('All Bookers').all().map(i => (i.json && i.json.fields) || {}).find(x => String(x.Name || '').trim().toLowerCase() === _me.toLowerCase()); } catch (e) {}
    if (_f && /engineer/i.test(String(_f.Info || '').split(/goes by/i)[0])) {
      __selfEngineer = String(_f.Name).trim();
      REQ.engineer = __selfEngineer;
      if (_ei !== -1) _sg[_ei] = ' Engineer: ' + __selfEngineer + ' '; else _sg.unshift('Engineer: ' + __selfEngineer + ' ');
      REQ.description = _sg.join('|').replace(/^\s+/, '');
      // "PROJECT / Client" with no initials segment yet: give it one, so the initials are added rather than the client replaced
      const _tp0 = String(REQ.summary || '').split(' / ').map(s => s.trim()), _cl0 = String(REQ.client || '').trim().toLowerCase();
      if (_tp0.length === 2 && _cl0 && _tp0[1].toLowerCase() === _cl0) REQ.summary = _tp0.concat('X').join(' / ');
    }
  }
}

"""
OUT_OLD = "client_known: typeof __aliasClient !== 'undefined' && !!__aliasClient,"
OUT_NEW = OUT_OLD + " self_engineer: typeof __selfEngineer !== 'undefined' ? __selfEngineer : '',"
RS_OLD = "if (newClient) notes.push("
RS_NEW = ("// v71: the requester was put down as the engineer because nobody was named - say so.\n"
          "if (CC.self_engineer) notes.push(\"No engineer was named, so you're down as the engineer. If someone else is engineering, tell me who.\");\n"
          + RS_OLD)

def fix(w):
    w["name"] = "Jessie — Book Session — v71 (self-engineer default)"
    c = node(w, "Check Conflicts")["parameters"]
    s = sub1(c["jsCode"], ANCHOR, BLOCK + ANCHOR, "anchor")
    c["jsCode"] = sub1(s, OUT_OLD, OUT_NEW, "outputs", 2)
    r = node(w, "Render Summary")["parameters"]; r["jsCode"] = sub1(r["jsCode"], RS_OLD, RS_NEW, "render")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
