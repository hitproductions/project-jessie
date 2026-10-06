#!/usr/bin/env python3
"""main v220 + Book Session v91 + Room Availability v17 (past bookings allowed) - decided 6 Oct (Howard): a session in the
past can be booked (e.g. to record one that happened). A date with a year is taken as written, so during the QA year shift
"oct 1 2026" books 1 Oct 2026, not 2027.
  Before: Gate Context told the model THE DATE THEY GAVE HAS ALREADY PASSED ... do not attempt to book it (any explicit-year
  date before the shifted today, i.e. every 2026 date); Book Session refused PAST_DATE (before Manila midnight, real time)
  and refused "yesterday" / "last Monday" in prepare mode; Room Availability answered PAST_DATE instead of checking.
  - main v220 Gate Context: the past-date notice says it is allowed (still names the date - Guard Probe reads its year);
    "yesterday", "the day before yesterday", "last <weekday>" (not "last Monday of ...") and "N days ago" resolve to dates.
    The prompt no longer says to refuse a past date.
  - Book Session v91: no PAST_DATE refusal; "yesterday" etc. no longer refused in prepare mode (Gate Context resolves
    them; an unresolved past phrase is asked "Which day?"). The card says "Heads up: this date has already passed." for a
    start before today (real time, so it appears on real past dates - after launch, every past date).
  - Room Availability v17: a past window is checked like any other.
  scripts/build-past-bookings.py <book-v90> <book-out> <main-v219> <main-out> <ra-v16> <ra-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# ---------------------------------------------------------------- Book Session
BS_PREP_OLD = """    if (/\\b(?:yesterday|last\\s+(?:mon|tues|wednes|thurs|fri|satur|sun)day(?!\\s+of\\b)|last\\s+week(?:end)?|\\d+\\s+days?\\s+ago)\\b/i.test(String(REQ.requester_text || ''))) {
      return [{ json: { verdict:'REJECTED', reason:'PAST_DATE',
        human:'Nothing was prepared - the day they asked for has already passed. Tell the requester it is in the past and ask for the correct date.' } }];
    }
"""
BS_PREP_NEW = """    // v91 (decided 6 Oct): past sessions can be booked - "yesterday" / "last Monday" are resolved by Gate Context now
"""
BS_PAST_OLD = """if (REQ.__past) {
  return [{ json: { verdict:'REJECTED', reason:'PAST_DATE', requested: REQ.start_iso,
    human:'Nothing was booked - ' + String(REQ.start_iso).slice(0, 10) + ' has already passed. '
        + 'Tell the requester the date is in the past and ask for the correct one. Do not book '
        + 'anything until they give you a new date.' } }];
}
"""
BS_PAST_NEW = """// v91 (decided 6 Oct): a session in the past can be booked (to record one that happened) - REQ.__past is no longer
// refused; Render Summary's card says the date has passed.
"""
RS_OLD = "const notes = [];\n"
RS_NEW = """const notes = [];
// v91 (decided 6 Oct): past sessions can be booked; the card says so, so a mistyped date is seen before the yes
try { const _ps = Date.parse(String(CC.final_start || '')), _pn = new Date(Date.now() + 8 * 3600 * 1000);
  if (_ps && _ps < Date.UTC(_pn.getUTCFullYear(), _pn.getUTCMonth(), _pn.getUTCDate()) - 8 * 3600 * 1000) notes.push('Heads up: this date has already passed.'); } catch (e) {}
"""
def book(w):
    w["name"] = "Jessie — Book Session — v91 (past bookings allowed)"
    cc = node(w, "Check Conflicts")["parameters"]; s = cc["jsCode"]
    s = sub1(s, BS_PREP_OLD, BS_PREP_NEW, "bs prep"); s = sub1(s, BS_PAST_OLD, BS_PAST_NEW, "bs past"); cc["jsCode"] = s
    rs = node(w, "Render Summary")["parameters"]; rs["jsCode"] = sub1(rs["jsCode"], RS_OLD, RS_NEW, "rs note")
    return w

# ---------------------------------------------------------------- Room Availability
RA_OLD = """if (reqStart && reqStart < manilaMidnight) {
  return [{ json: { status:'PAST_DATE', window: { start: REQ.start_iso, end: REQ.end_iso },
    human: String(REQ.start_iso).slice(0, 10) + ' has already passed, so there is nothing to check. '
         + 'Tell the requester the date is in the past and ask for the right one.' } }];
}
"""
RA_NEW = """// v17 (decided 6 Oct): past sessions can be booked, so a past window is checked like any other (was PAST_DATE).
"""
def ra(w):
    w["name"] = "Jessie — Room Availability — v17 (past bookings allowed)"
    ca = node(w, "Compute Availability")["parameters"]; ca["jsCode"] = sub1(ca["jsCode"], RA_OLD, RA_NEW, "ra past")
    return w

# ---------------------------------------------------------------- main
GC_NOTICE_OLD = """    pastDateNotice = 'THE DATE THEY GAVE HAS ALREADY PASSED: ' + pastHit.shown + '. Before anything else, '
      + 'tell them that date is in the past and ask for the correct one. Do not ask for the session type, '
      + 'the client, the project or the engineer, and do not attempt to book it.';"""
GC_NOTICE_NEW = """    // v220 (decided 6 Oct): past sessions can be booked - the date is taken as written (a year included)
    pastDateNotice = 'THE DATE THEY GAVE HAS ALREADY PASSED: ' + pastHit.shown + '. That is allowed - a past session '
      + 'can be booked. Use exactly that date, year included, and carry on as normal; do not ask them to change it.';"""
GC_REL_OLD = """if (/\\btomorrow\\b/i.test(msgText)) note('tomorrow', addDays(today, 1));
"""
GC_REL_NEW = """if (/\\btomorrow\\b/i.test(msgText)) note('tomorrow', addDays(today, 1));
// v220 (decided 6 Oct): past sessions can be booked, so past days resolve too - yesterday, last <weekday>, N days ago
{ const _NWp = { one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10 };
  if (/\\b(?:the\\s+)?day\\s+before\\s+yesterday\\b/i.test(msgText)) note('the day before yesterday', addDays(today, -2));
  else if (/\\byesterday\\b/i.test(msgText)) note('yesterday', addDays(today, -1));
  const _reLast = new RegExp('\\\\blast\\\\s+' + DAYRE + '\\\\b(?!\\\\s+of\\\\b)', 'gi'); let _lm;
  while ((_lm = _reLast.exec(msgText)) !== null) { let _d = addDays(weekMonday, (dayIndex(_lm[1]) + 6) % 7); if (_d.getTime() >= today.getTime()) _d = addDays(_d, -7); note(_lm[0], _d, '(the most recent one)'); }
  const _ago = msgText.match(/\\b(\\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten)\\s+days?\\s+ago\\b/i);
  if (_ago) { const _k = String(_ago[1]).toLowerCase(); const _n = /^\\d+$/.test(_k) ? +_k : _NWp[_k]; if (_n > 0 && _n <= 60) note(_ago[0], addDays(today, -_n)); } }
"""
GC_FIRST_OLD = """  if ((m = t.match(/\\btomorrow\\b/i))) add(m.index, addDays(today, 1));
"""
GC_FIRST_NEW = """  if ((m = t.match(/\\btomorrow\\b/i))) add(m.index, addDays(today, 1));
  { const _NWp = { one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10 };   // v220: past days
    if ((m = t.match(/\\b(?:the\\s+)?day\\s+before\\s+yesterday\\b/i))) add(m.index, addDays(today, -2));
    else if ((m = t.match(/\\byesterday\\b/i))) add(m.index, addDays(today, -1));
    const _rl = new RegExp('\\\\blast\\\\s+' + DAYRE + '\\\\b(?!\\\\s+of\\\\b)', 'gi');
    while ((m = _rl.exec(t)) !== null) { let _d = addDays(weekMonday, (dayIndex(m[1]) + 6) % 7); if (_d.getTime() >= today.getTime()) _d = addDays(_d, -7); add(m.index, _d); }
    const _ag = t.match(/\\b(\\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten)\\s+days?\\s+ago\\b/i);
    if (_ag) { const _k = String(_ag[1]).toLowerCase(); const _n = /^\\d+$/.test(_k) ? +_k : _NWp[_k]; if (_n > 0 && _n <= 60) add(_ag.index, addDays(today, -_n)); } }
"""
SM1_OLD = "*Check the date first.* If it has passed, say so and ask for the right one before collecting anything else."
SM1_NEW = "*Past dates are fine.* A session in the past can be booked (to record one that happened); use the date exactly as given, year included, and carry on as normal."
SM2_OLD = "book through Book Session with the exact room name, never in the past, and if the room is taken"
SM2_NEW = "book through Book Session with the exact room name, and if the room is taken"

def main(w):
    w["name"] = "Project Jessie — v220 (past bookings allowed)"
    gc = node(w, "Gate Context")["parameters"]; s = gc["jsCode"]
    s = sub1(s, GC_NOTICE_OLD, GC_NOTICE_NEW, "gc notice"); s = sub1(s, GC_REL_OLD, GC_REL_NEW, "gc rel"); s = sub1(s, GC_FIRST_OLD, GC_FIRST_NEW, "gc first")
    gc["jsCode"] = s
    ag = node(w, "Jessie AI Agent")["parameters"]["options"]
    ag["systemMessage"] = sub1(sub1(ag["systemMessage"], SM1_OLD, SM1_NEW, "prompt 1"), SM2_OLD, SM2_NEW, "prompt 2")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    for f, i, o in [(book, 0, 1), (main, 2, 3), (ra, 4, 5)]:
        json.dump(f(json.load(open(a[i]))), open(a[o], "w"), indent=2, ensure_ascii=False); print("wrote", a[o])
