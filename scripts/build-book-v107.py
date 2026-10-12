#!/usr/bin/env python3
"""Book Session v107 - PENDING 82 ("anj" as a client).

  4 Oct 21:26 / reproduced offline 12 Oct on v106: "client is anj" was prepared as a new client "Anj". "Anj" is how a client
  goes by (Clients Notes: Angela dela Calzada, "Goes by Anj") and how a staff member goes by (Bookers Info: Angelo Villegas,
  "Goes by Angelo, Anj, AV"). The existing AMBIGUOUS_PERSON check covered only "for anj" (a colleague the booking is for).
Book Session v107 (Check Conflicts, prepare): a client given as a word that is both a client's "goes by" alias and a staff
  member's name / first name / alias is asked - "Just to check - by Anj, do you mean Angelo Villegas (Music Arranger) or Angela
  dela Calzada (Producer, a client)?" - unless the requester's words already settle it (the client's or the staff member's
  name, the client's type or the staff role).

  scripts/build-book-v107.py <book-v106> <book-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
ANCHOR = "// v50 (Howard, 2026-09-28): client Technical Requirement"
ADD = r"""// v107 (PENDING 82, "client is anj"): a client given as a word that is both a client's alias and a staff member's name or
// alias is asked, never guessed - unless the requester's own words already say which
if (typeof __prep !== "undefined" && __prep && clientGiven) {
  try {
    const _k2 = s => String(s || '').toLowerCase().replace(/[^a-z0-9ñ ]+/g, ' ').replace(/\s+/g, ' ').trim();
    const _cg = _k2(clientGiven), _al2 = (() => { try { return $('Client Aliases').all().map(i => (i.json && i.json.fields) || {}).filter(f => f.Name); } catch (e) { return []; } })();
    const _ali = (txt, re) => ((String(txt || '').match(re) || [])[1] || '').split(/,|\band\b|\bor\b/i).map(_k2).filter(Boolean);
    const _cH = _al2.filter(f => _k2(f.Name) !== _cg && _ali(f.Notes, /goes by\s+([^.\n]*)/i).indexOf(_cg) !== -1);
    const _bk2 = (() => { try { return $('All Bookers').all().map(i => (i.json && i.json.fields) || {}).filter(f => f.Name); } catch (e) { return []; } })();
    const _sH = _bk2.filter(f => _k2(f.Name) !== _cg && (_k2(String(f.Name).split(/\s+/)[0]) === _cg || _ali(f.Info, /goes by\s+([^\n]*)/i).indexOf(_cg) !== -1));
    if (_cH.length === 1 && _sH.length === 1) {
      const _rt2 = ' ' + _k2(REQ.requester_text) + ' ', _has2 = t => t.length >= 4 && t !== _cg && _rt2.indexOf(' ' + t + ' ') !== -1;
      const _cl = _cH[0], _st = _sH[0], _cType = String((_cl['Booker Type'] && (_cl['Booker Type'].name || _cl['Booker Type'])) || '').trim();
      const _role2 = String(_st.Info || '').split(/,|\bgoes by\b/i)[0].trim();
      const _cSide2 = _k2(_cl.Name).split(' ').some(_has2) || _k2(_cType).split(' ').some(_has2);
      const _sSide2 = _k2(_st.Name).split(' ').some(_has2) || _k2(_role2).split(' ').slice(-1).some(_has2);
      if (_cSide2 === _sSide2) {
        const _say2 = s => String(s).replace(/^./, c => c.toUpperCase());
        return [{ json: { verdict:'REJECTED', reason:'AMBIGUOUS_PERSON', typed: clientGiven, staff: _st.Name, client: _cl.Name,
          human:'Nothing was prepared. Ask exactly this, in one message: "Just to check - by ' + _say2(clientGiven) + ', do you mean ' + _st.Name
            + (_role2 ? ' (' + _role2 + ')' : '') + ' or ' + _cl.Name + ' (' + (_cType ? _cType + ', a client' : 'a client') + ')?"' } }];
      }
    }
  } catch (e) {}
}
"""
def book(w):
    w["name"] = "Jessie — Book Session — v107 (client or staff asked)"
    cc = node(w, "Check Conflicts")["parameters"]; cc["jsCode"] = once(cc["jsCode"], ANCHOR, ADD + ANCHOR, "anchor"); return w
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2: print(__doc__.strip()); sys.exit(2)
    json.dump(book(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
