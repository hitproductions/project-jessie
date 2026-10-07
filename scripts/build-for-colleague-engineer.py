#!/usr/bin/env python3
"""Book Session v95 (colleague engineers) - QA round 3 B2 (7 Oct, trish): "Book Studio F for elijah next Tuesday from 1pm to
4pm" - Trish is not an engineer, so v94 asked "Who's the engineer ...?"; the expectation is that "for Elijah" makes Elijah
(Alec Elijah Gan, Post Engineer) both the engineer and the "For:". Decided 7 Oct: a booking FOR a colleague who is an engineer
is engineered by that colleague, the same way an engineer booking for themselves is never asked (replaces v80, 1 Oct:
"booking FOR a colleague, the engineer is asked" - that still holds for a colleague who is not an engineer).
  1. No engineer named, booked for a colleague whose Bookers role is an engineer that fits the session type (its roles, e.g.
     Post Engineer for VO Recording; "Secondary Music Engineer" fits Music) -> that colleague is the engineer: put in, not
     asked (the title initials then come from Bookers, as for any engineer). While the session type is still unknown the
     engineer question is held back (the colleague may fit); a colleague who does not fit is asked about as before.
  2. The same run's first question had no "What's the project?" - the model's title project was most likely the colleague's
     name ("ELIJAH"), which counts as typed. A project that is only the booked-for colleague's name now counts as missing.
  scripts/build-for-colleague-engineer.py <book-session-v94> <book-session-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
ENG_OLD = """    __engAsk = !_engNow && (!!_st || __studioRoom)   // Localization too: a Loc session needs a Loc engineer"""
ENG_NEW = r"""    // v95 (QA B2, decided 7 Oct): booked FOR a colleague who is an engineer that fits the session type -> they engineer it
    let _forHold = false;
    if (!_engNow && !_declined) {
      try {
        const _forName = ((String(REQ.description || '').match(/\(for\s+([^)]+)\)/i) || [])[1] || '').trim();
        const _fs = _forName ? $('All Bookers').all().map(i => (i.json && i.json.fields) || {}).find(f => String(f.Name || '').trim().toLowerCase() === _forName.toLowerCase()) : null;
        const _fRoles = _fs ? String(_fs.Info || '').split(/\bgoes by\b/i)[0].split(/[,.]/).map(x => x.trim().replace(/^(?:secondary|tertiary)\s+/i, '').toLowerCase()).filter(x => /engineer/.test(x)) : [];
        if (_fRoles.length) {
          const _tRoles = _ty ? [].concat(_ty.roles || []).map(r => String(r).trim().toLowerCase()).filter(r => /engineer/.test(r)) : null;
          if (_tRoles === null) _forHold = true;   // type not known yet: hold the question, the colleague may fit
          else if (_tRoles.some(r => _fRoles.indexOf(r) !== -1)) {
            REQ.engineer = String(_fs.Name).trim(); REQ.__forEng = true;
            const _s5 = String(REQ.description || '').split('|'); _s5.unshift('Engineer: ' + REQ.engineer + ' '); REQ.description = _s5.join('|');
          }
        }
      } catch (e) {}
    }
    const _engSet = String(REQ.engineer || '').trim();
    __engAsk = !_engNow && !_engSet && !_forHold && (!!_st || __studioRoom)   // Localization too: a Loc session needs a Loc engineer"""
PROJ_OLD = """        _noProj = !_p || !_typed || _isType || _isRoom || _isClient;"""
PROJ_NEW = """        // v95 (QA B2): the booked-for colleague's name is not a project ("for elijah" -> ELIJAH)
        const _forN = _nz(((String(_R.description || '').match(/\\(for\\s+([^)]+)\\)/i) || [])[1] || ''));
        const _isFor = !!_p && !!_forN && (_p === _forN || _forN.split(' ').indexOf(_p) !== -1);
        _noProj = !_p || !_typed || _isType || _isRoom || _isClient || _isFor;"""
def book(w):
    w["name"] = "Jessie — Book Session — v95 (colleague engineers)"
    cc = node(w, "Check Conflicts")["parameters"]; s = cc["jsCode"]
    s = sub1(s, ENG_OLD, ENG_NEW, "eng"); s = sub1(s, PROJ_OLD, PROJ_NEW, "proj"); cc["jsCode"] = s
    return w
if __name__ == "__main__":
    json.dump(book(json.load(open(sys.argv[1]))), open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
