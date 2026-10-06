#!/usr/bin/env python3
"""Book Session v94 + main v228 (QA round 3 fixes) - from the review of the round-3 sheets against the live build (6 Oct):
  1. The engineer was never asked of a requester who is not an engineer. docs/design/booking-defaults.md rule 5 ("Anyone else
     booking a studio -> 'Who's engineering?'") lived only in the prompt, and since v203 Book Session's own questions go out
     word for word, so nothing asked it: on the live code Trish, Jess and Camy (none of them engineers) get "What kind of
     session is this? What's the project, and who's the client?" and then a card with NO engineer, the title ending in
     whatever initials the model wrote. QA B1 would fail for all three.
     Book Session v94: for a studio booking (not a Meeting / Event, not a conference room or M booth) by a requester whose
     Bookers role is not an engineer, with no engineer named, "who's the engineer" rides on the first questions - "What's
     the project, who's the engineer, and who's the client? (or "none")" - and is asked on its own when nothing else is
     missing (NEED_ENGINEER). "no engineer" / "engineer: none" / "without an engineer" ends it. An engineer requester is
     never asked (the self default stands).
  2. Past dates (QA E2, "last Monday"): since v220 / v91 a past date is booked, and the card says "Heads up: this date has
     already passed." - but Book Session compares with the REAL date, so during the QA year shift (dates in 2027) the
     heads-up never shows and "last Monday" is booked silently. main v228: Gate Context also returns the date it treats as
     today (todayIso, year shift included); Guard Probe adds the heads-up to a booking card whose date is before it, when
     the card does not already say so. At launch (YEAR_SHIFT 0) the two agree and only one line is ever shown.
  scripts/build-qa3-fixes.py <book-session-v93> <book-session-out> <main-v227> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# ---------------------------------------------------------------- Book Session v94
DECL_OLD = "let __cliAsk = false;"
DECL_NEW = "let __cliAsk = false;\nlet __engAsk = false;   // v94: the engineer is still to be asked (a requester who is not an engineer)"
ENG_OLD = """    && !/^(Internal|Personal)$/.test(__tyWords(_rt));   // v90 (decided 6 Oct): asked until answered or declined - no cap
}"""
ENG_NEW = r"""    && !/^(Internal|Personal)$/.test(__tyWords(_rt));   // v90 (decided 6 Oct): asked until answered or declined - no cap
  // v94 (QA round 3 review, 6 Oct): booking-defaults rule 5 - anyone who is not an engineer booking a studio is asked who is
  // engineering, with the first questions; it lived only in the prompt, and nothing asked it once questions went out word
  // for word (v203). Not for an engineer requester (the self default), a Meeting / Event, or a type whose roles hold no
  // engineer; "no engineer" ends it.
  try {
    const _segE = (String(REQ.description || '').split('|').find(s => /^\s*engineer\s*:/i.test(s)) || '').replace(/^\s*engineer\s*:\s*/i, '').trim();
    const _engNow = String(REQ.engineer || '').trim() || _segE;
    let _ref = {}; try { _ref = JSON.parse(String(REQ.reference_data || '{}')); } catch (e) {}
    const _ty = (_ref.types || []).find(x => String(x.type || '').toLowerCase() === _st.toLowerCase());
    const _needsEng = !_ty || [].concat(_ty.roles || []).some(r => /engineer/i.test(String(r)));
    const _declined = /\bno engineer\b|\bwithout (?:an? )?engineer\b|\bengineer\s*(?:is|:|=)?\s*(?:none|n\/?a|tbd|tba)\b|\bno need (?:for )?(?:an? )?engineer\b/i.test(_rt);
    __engAsk = !_engNow && (!!_st || __studioRoom)   // Localization too: a Loc session needs a Loc engineer
      && !/^(meeting|event)$/i.test(_st) && _needsEng && !_declined
      && !!__reqStaff && !/engineer/i.test(__reqRole);
  } catch (e) { __engAsk = false; }
}"""
PC_OLD = """    const _pc = _pj && _cli ? 'What’s the project, and who’s the client? (or \\\\"none\\\\")' : _pj ? 'What’s the project?' : _cli ? 'Who’s the client? (or \\\\"none\\\\")' : '';"""
PC_NEW = """    // v94: the engineer too - project, engineer, then the client last so its (or "none") stays at the end
    const _eng = __engAsk && __j && __j.reason !== 'ON_BEHALF_OR_OWN' && __j.reason !== 'NEED_ENGINEER' && !/\\bengineer/i.test(_q0);
    const _parts = [_pj ? 'what’s the project' : '', _eng ? 'who’s the engineer' : '', _cli ? 'who’s the client' : ''].filter(Boolean);
    const _join = a => a.length === 1 ? a[0] : a.length === 2 ? a[0] + ', and ' + a[1] : a.slice(0, -1).join(', ') + ', and ' + a[a.length - 1];
    const _pc = _parts.length ? (_join(_parts).replace(/^./, c => c.toUpperCase()) + '?' + (_cli ? ' (or \\\\"none\\\\")' : '')) : '';"""
CLEAR_OLD = """    else if (__j.verdict === 'CLEAR' && (__j.time_proposed || _noProj)) {
      const _q = _noProj ? 'What’s the project?' + (__j.time_proposed ? ' And what time?' : '') : 'What time?';
      return [{ json: { verdict:'REJECTED', reason: _noProj ? 'NEED_PROJECT' : 'NEED_TIME',"""
CLEAR_NEW = """    else if (__j.verdict === 'CLEAR' && (__j.time_proposed || _noProj || __engAsk)) {
      // v94: the engineer is asked here too when nothing else is missing
      const _p2 = [_noProj ? 'what’s the project' : '', __engAsk ? 'who’s the engineer' : ''].filter(Boolean);
      const _q = _p2.length ? (_join(_p2).replace(/^./, c => c.toUpperCase()) + '?' + (__j.time_proposed ? ' And what time?' : '')) : 'What time?';
      return [{ json: { verdict:'REJECTED', reason: __engAsk ? 'NEED_ENGINEER' : _noProj ? 'NEED_PROJECT' : 'NEED_TIME',"""

def book(w):
    w["name"] = "Jessie — Book Session — v94 (engineer asked first)"
    cc = node(w, "Check Conflicts")["parameters"]; s = cc["jsCode"]
    s = sub1(s, DECL_OLD, DECL_NEW, "decl"); s = sub1(s, ENG_OLD, ENG_NEW, "eng"); s = sub1(s, PC_OLD, PC_NEW, "pc"); s = sub1(s, CLEAR_OLD, CLEAR_NEW, "clear")
    cc["jsCode"] = s
    return w

# ---------------------------------------------------------------- main v228
GC_OLD = "  pastDate: pastDate,"
GC_NEW = "  pastDate: pastDate,\n  todayIso: today.toISOString().slice(0, 10),   // v228: the date treated as today (QA year shift included)"
GP_ANCHOR = "// 29 Sep: an all-day clash was described as"
GP_BLOCK = r"""// v228 (QA round 3 review): a booking card for a date before the one treated as today says so. Book Session's own heads-up
// (v91) compares with the real date, so during the QA year shift it never showed for a 2027 date; at launch they agree and
// this adds nothing to a card that already says it.
try {
  const _gT = String((($('Gate Context').first() || {}).json || {}).todayIso || '');
  const _dl = text.match(/^\*Date:\*\s*(?:[A-Za-z]+,\s*)?([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})\s*$/m);
  if (_gT && _dl && /\n\nBook it\? Reply yes or no\.\s*$/.test(text) && !/already passed/i.test(text)) {
    const _mo = ['january','february','march','april','may','june','july','august','september','october','november','december'].indexOf(_dl[1].toLowerCase());
    const _iso = _dl[3] + '-' + String(_mo + 1).padStart(2, '0') + '-' + String(+_dl[2]).padStart(2, '0');
    if (_mo >= 0 && _iso < _gT) {
      const _at = text.lastIndexOf('\n\nBook it?'), _prev = text.slice(0, _at).split('\n').pop();
      text = text.slice(0, _at) + (/^\*/.test(_prev) ? '\n\n' : '\n') + 'Heads up: this date has already passed.' + text.slice(_at);
    }
  }
} catch (e) {}

"""
def main(w):
    w["name"] = "Project Jessie — v228 (QA round 3 fixes)"
    gc = node(w, "Gate Context")["parameters"]; gc["jsCode"] = sub1(gc["jsCode"], GC_OLD, GC_NEW, "gate")
    gp = node(w, "Guard Probe")["parameters"]; gp["jsCode"] = sub1(gp["jsCode"], GP_ANCHOR, GP_BLOCK + GP_ANCHOR, "gp")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(book(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
