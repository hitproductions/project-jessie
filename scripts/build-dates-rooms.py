#!/usr/bin/env python3
"""main v211 (on top of build-project-words.py) + Room Availability v13 (live 2 Oct notes):
  1. "in 2 days" was no date to Gate Context (the model guessed one, and it ran into another booking). Gate Context now
     reads "in N days", "N days from now / from today" (digits or one..ten) and "the day after tomorrow".
  2. Free-room answers are laid out by category, one line each (PENDING 67's layout):
         Free studios:
         Studios 1, 2, 3, 7, 8, F, and C.
         M2, M3, M5.
     Room Availability v13 writes this text (reply_text; day by day with a blank line between days for a range).
     Guard Probe sends it when this turn's latest Room Availability answered OK and the model's reply is just the list
     (no question, no booking card).
  scripts/build-dates-rooms.py <main-in> <main-out> <ra-live> <ra-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

NUMRE = r"(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten)"
G1_OLD = "if (/\\btomorrow\\b/i.test(msgText)) note('tomorrow', addDays(today, 1));"
G1_NEW = G1_OLD + r"""
// v211 (live 2 Oct, "in 2 days"): N days ahead, and the day after tomorrow
{ const _NW = { one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10 };
  const _dm = msgText.match(/\bin\s+""" + NUMRE + r"""\s+days?\b|\b""" + NUMRE + r"""\s+days?\s+from\s+(?:now|today)\b/i);
  if (_dm) { const _k = String(_dm[1] || _dm[2]).toLowerCase(); const _nd = /^\d+$/.test(_k) ? +_k : _NW[_k]; if (_nd > 0 && _nd <= 60) note(_dm[0], addDays(today, _nd)); }
  if (/\bday after tomorrow\b/i.test(msgText)) note('the day after tomorrow', addDays(today, 2)); }"""
G2_OLD = "if ((m = t.match(/\\btomorrow\\b/i))) add(m.index, addDays(today, 1));"
G2_NEW = G2_OLD + r"""
  { const _NW2 = { one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10 };   // v211
    const _dm2 = t.match(/\bin\s+""" + NUMRE + r"""\s+days?\b|\b""" + NUMRE + r"""\s+days?\s+from\s+(?:now|today)\b/i);
    if (_dm2) { const _k2 = String(_dm2[1] || _dm2[2]).toLowerCase(); const _n2 = /^\d+$/.test(_k2) ? +_k2 : _NW2[_k2]; if (_n2 > 0 && _n2 <= 60) add(_dm2.index, addDays(today, _n2)); }
    const _da = t.match(/\bday after tomorrow\b/i); if (_da) add(_da.index, addDays(today, 2)); }"""

GP_ANCHOR = "// v194: a compact list of this turn's tool calls, for the Turn Log (Turn Log Row cannot read the agent itself)."
GP_NEW = r"""// v211 (decided 2 Oct): a free-room answer is sent in Room Availability's own layout (studios / booths / M booths / rooms
// on their own lines, day by day for a range) when the model's reply is just the list - no question, no booking card.
try {
  const _sR = (($input.first().json || {}).intermediateSteps) || [];
  for (let i = _sR.length - 1; i >= 0; i--) {
    const _tR = String(((_sR[i] || {}).action || {}).tool || '').replace(/[_\s]+/g, ' ').toLowerCase();
    if (_tR !== 'room availability') continue;
    let _oR = null; try { _oR = [].concat(JSON.parse(String((_sR[i] || {}).observation || '')))[0]; } catch (e) {}
    if (_oR && _oR.status === 'OK' && _oR.reply_text && !_prepared && !/\?/.test(text) && !/\*Date:\*|Book it\?|Confirm to/i.test(text) && /\bfree\b/i.test(text))
      text = String(_oR.reply_text);
    break;
  }
} catch (e) {}

""" + GP_ANCHOR

RA_HELPER_ANCHOR = "const out = { status:'OK', window: { start: REQ.start_iso, end: REQ.end_iso }, asked: askedAnswer,"
RA_HELPER = r"""// v13 (decided 2 Oct): the free list laid out by category - studios, vocal booths, M booths, other rooms - one line each.
function __layout(list) {
  const L = [].concat(list || []);
  const _sk = x => { const t = String(x).replace(/^Studio\s+/i, ''); return /^\d+$/.test(t) ? [0, +t, ''] : [1, 0, t]; };
  const _sort = a => a.slice().sort((p, q) => { const a1 = _sk(p), b1 = _sk(q); return a1[0] - b1[0] || a1[1] - b1[1] || String(a1[2]).localeCompare(String(b1[2])); });
  const _and = a => a.length <= 1 ? a.join('') : a.slice(0, -1).join(', ') + ', and ' + a[a.length - 1];
  const booths = _sort(L.filter(n => isBooth[n]));
  const studios = _sort(L.filter(n => /^Studio\s/i.test(n) && !isBooth[n]));
  const mb = L.filter(n => /^M[1-8]$/i.test(n)).sort((p, q) => +String(p).slice(1) - +String(q).slice(1));
  const other = L.filter(n => !isBooth[n] && !/^Studio\s/i.test(n) && !/^M[1-8]$/i.test(n)).sort();
  const out = [];
  if (studios.length) out.push(studios.length === 1 ? studios[0] + '.' : 'Studios ' + _and(studios.map(n => String(n).replace(/^Studio\s+/i, ''))) + '.');
  if (booths.length) out.push((booths.length === 1 ? 'Vocal booth ' : 'Vocal booths ') + _and(booths.map(n => String(n).replace(/^Studio\s+/i, ''))) + '.');
  if (mb.length) out.push(mb.join(', ') + '.');
  if (other.length) out.push(other.join(', ') + '.');
  return out;
}
""" + RA_HELPER_ANCHOR

RA_SINGLE_OLD = "// Booth availability is computed here rather than left to the model to work out"
RA_SINGLE_NEW = r"""// v13: the laid-out reply for a plain free-room question (no session type, no room asked about)
if (Array.isArray(out.free_rooms) && !askedAnswer) {
  const _lines = __layout(out.free_rooms.concat(boothNames.filter(n => free(n) && out.free_rooms.indexOf(n) === -1)));
  const _sOnly = String(REQ.scope || '').toLowerCase() === 'studios';
  out.reply_text = _lines.length ? (_sOnly ? 'Free studios:' : 'Free rooms:') + '\n' + _lines.join('\n') : (_sOnly ? 'No studio is free then.' : 'Nothing is free then.');
}
""" + RA_SINGLE_OLD

RA_MULTI_OLD = "        if (st) outM.session_type = st;"
RA_MULTI_NEW = r"""        if (!askedList.length && !(st && (priority.length || lastResort.length))) {   // v13: day by day, each day laid out
          outM.reply_text = (_studiosOnly ? 'Free studios' : 'Free rooms') + ', ' + (_whole ? 'all day' : hours) + ':\n\n'
            + days.map(d => d.label + ':\n' + (d.free_rooms && d.free_rooms.length ? __layout(d.free_rooms).join('\n') : 'Nothing free.')).join('\n\n');
        }
""" + RA_MULTI_OLD

def main(w):
    w["name"] = "Project Jessie — v211 (project, dates + room list)"
    g = node(w, "Gate Context")["parameters"]; s = g["jsCode"]
    s = sub1(s, G1_OLD, G1_NEW, "gate note"); s = sub1(s, G2_OLD, G2_NEW, "gate add"); g["jsCode"] = s
    gp = node(w, "Guard Probe")["parameters"]; gp["jsCode"] = sub1(gp["jsCode"], GP_ANCHOR, GP_NEW, "guard")
    return w
def ra(w):
    w["name"] = "Jessie — Room Availability — v13 (room list layout)"
    c = node(w, "Compute Availability")["parameters"]; s = c["jsCode"]
    s = sub1(s, RA_HELPER_ANCHOR, RA_HELPER, "ra helper"); s = sub1(s, RA_SINGLE_OLD, RA_SINGLE_NEW, "ra single"); s = sub1(s, RA_MULTI_OLD, RA_MULTI_NEW, "ra multi")
    c["jsCode"] = s
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(ra(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
