#!/usr/bin/env python3
"""Live QA, 29 Sep ~12:00 PHT ("tomorrow at Salin" for a meeting): four fixes, built from fresh pulls.
  scripts/build-date-room-fixes.py <main-pull.json> <main-out.json> <book-pull.json> <book-out.json>

A  main: the model re-worked "tomorrow" out by itself on the follow-up turns and sent 1 Oct; Gate Context had it right
   (30 Sep). Book Session refused (DATE_MISMATCH), but its refusal read as if the requester had asked for 1 Oct. Now
   Prepare Booking's start / end use the one date under discussion whenever the model's date differs from it and the
   requester never typed that date themselves ("october 1", "oct 1", "1 oct", "10 1", "friday"). Done in main, before
   Book Session reads the calendar: correcting it inside Book Session would check availability on the wrong day.
   Two dates under discussion, or the model's date typed by the requester: unchanged (Book Session still asks).
B  Book Session: a conference room taken -> the other conference rooms free in that same window are offered (the lobby
   only if the lobby was asked for). Before: no session type, no ranking, so nothing was offered and the model named
   "Likha or Katha" unchecked; Katha was taken all day.
C  Book Session: an all-day clash is described as "taken all day" (the model had written "from 12:00 AM to 12:00 AM");
   Guard Probe rewrites that phrase too, as a backstop.
D  main Guard Probe: "And which day is it for?" was appended to a greeting ("Hi Howard! What do you need?") because the
   conversation mentioned booking and no date was set. It is now added only to a question about the booking's details.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# ---------------------------------------------------------------- A: date under discussion, main
DATEFIX = (r"""((g, b, v, isEnd) => { const s = String(v || ''); const d = s.slice(0, 10); """
    r"""const want = String((g || {}).datesUnderDiscussion || '').split(',').map(x => x.trim()).filter(x => /^\d{4}-\d{2}-\d{2}$/.test(x)); """
    r"""if (want.length !== 1 || !/^\d{4}-\d{2}-\d{2}$/.test(d)) return v; """
    r"""const add = (ymd, n) => new Date(Date.parse(ymd + 'T00:00:00Z') + n * 864e5).toISOString().slice(0, 10); """
    r"""const allDayEnd = isEnd && s.length === 10; const target = allDayEnd ? add(want[0], 1) : want[0]; if (d === target) return v; """
    r"""const md = allDayEnd ? add(d, -1) : d; const dt = new Date(Date.parse(md + 'T00:00:00Z')); """
    r"""const M = ['january','february','march','april','may','june','july','august','september','october','november','december'][dt.getUTCMonth()]; """
    r"""const W = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday'][dt.getUTCDay()]; const n = String(dt.getUTCDate()); """
    r"""const days = [n, n + 'st', n + 'nd', n + 'rd', n + 'th']; const said = ' ' + String((b || {}).saidWords || '') + ' '; """
    r"""const typed = [W, md, String(dt.getUTCMonth() + 1) + ' ' + n].concat(...days.map(x => [M + ' ' + x, M.slice(0, 3) + ' ' + x, x + ' ' + M, x + ' ' + M.slice(0, 3), x + ' of ' + M])).some(t => said.includes(' ' + t + ' ')); """
    r"""return typed ? v : target + s.slice(10); })""")

def wrap_date(expr, is_end):
    if not (expr.startswith("={{ ") and expr.endswith(" }}")): raise SystemExit("unexpected start/end expression shape")
    inner = expr[4:-3]
    return "={{ " + DATEFIX + "(($('Gate Context').first() || {}).json, ($('Booked For').first().json || {}), " + inner + ", " + ("true" if is_end else "false") + ") }}"

# ---------------------------------------------------------------- C + D: Guard Probe
GP_D_OLD = "  if (_asks && _booking && _noDate && !/\\b(date|day|when|which day)\\b/i.test(text)) text = text.trim() + '\\nAnd which day is it for?';"
GP_D_NEW = ("  // 29 Sep: it was added to a greeting (\"Hi Howard! What do you need?\"). Only a question about the booking's details\n"
            "  // gets it now.\n"
            "  const _aboutBooking = /\\b(session|client|project|engineer|arranger|room|studio|booth|time|how long|external|personal|type|title|department)\\b/i.test(text);\n"
            "  if (_asks && _booking && _noDate && _aboutBooking && !/\\b(date|day|when|which day)\\b/i.test(text)) text = text.trim() + '\\nAnd which day is it for?';")
GP_C_ANCHOR = "const fallback = \"Sorry — I lost the thread on that one. Could you say it again?\";"
GP_C_NEW = ("// 29 Sep: an all-day clash was described as \"from 12:00 AM to 12:00 AM\" (the model formatting a midnight-to-midnight\n"
            "// event). Book Session now says \"all day\"; this is the backstop.\n"
            "text = text.replace(/\\s*(?:from\\s+)?12:00\\s*AM\\s*(?:to|until|till|-|–|—)\\s*12:00\\s*AM\\b/gi, ' all day');\n\n")

def main_fix(w):
    w["name"] = "Project Jessie — v182 (v181 fixed)"
    v = node(w, "Prepare Booking")["parameters"]["workflowInputs"]["value"]
    v["start_iso"] = wrap_date(v["start_iso"], False)
    v["end_iso"] = wrap_date(v["end_iso"], True)
    g = node(w, "Guard Probe")["parameters"]
    c = sub1(g["jsCode"], GP_D_OLD, GP_D_NEW, "D date ask")
    c = sub1(c, GP_C_ANCHOR, GP_C_NEW + GP_C_ANCHOR, "C all day")
    g["jsCode"] = c
    return w

# ---------------------------------------------------------------- B + C: Book Session
BS_ALTS_OLD = """    _alts = [...new Set(priorityIds.concat(lastIds).map(id => nameById[id]).filter(Boolean))]
      .filter(r => !_busy.has(r.toLowerCase()) && _asked.indexOf(r.toLowerCase()) === -1 && !_common.has(r.toLowerCase())).slice(0, 4);"""
BS_ALTS_NEW = BS_ALTS_OLD + """
    // 29 Sep (live QA): a conference room was taken and she offered "Likha or Katha" unchecked - Katha was taken all
    // day. A meeting room has no session type, so there was no ranking to draw from. The other conference rooms free
    // in that window are offered instead (the lobby only when the lobby was asked for).
    _commonMode = _asked.length > 0 && _asked.every(a => _common.has(a));
    if (_commonMode) {
      const _lobbyAsked = _asked.some(a => /lobby/.test(a));
      _alts = (_R.rooms || []).filter(r => r.common).map(r => String(r.name))
        .filter(n => !_busy.has(n.toLowerCase()) && _asked.indexOf(n.toLowerCase()) === -1 && (_lobbyAsked || !/lobby/i.test(n))).slice(0, 4);
    }"""
BS_LET_OLD = "  let _alts = [];\n  try {\n    let _R = {};"
BS_LET_NEW = "  let _alts = [], _commonMode = false;\n  try {\n    let _R = {};"
BS_LINES_OLD = """  const lines = conflicts.map(c => c.room + ' is taken by "' + c.summary + '"').join('; ');"""
BS_LINES_NEW = """  // 29 Sep: an all-day clash came out as "from 12:00 AM to 12:00 AM". Say "all day" (Manila midnight to midnight, or a date-only event).
  const _allDay = c => { const s = String(c.start || ''), e = String(c.end || ''); return /^\\d{4}-\\d{2}-\\d{2}$/.test(s) || (/T00:00(:00)?(\\.\\d+)?(\\+08:00|Z)?$/.test(s) && /T00:00(:00)?(\\.\\d+)?(\\+08:00|Z)?$/.test(e)); };
  const lines = conflicts.map(c => c.room + ' is taken' + (_allDay(c) ? ' all day' : '') + ' by "' + c.summary + '"').join('; ');"""
BS_HUMAN_OLD = """    human: lines + '. Nothing was booked. ' + (_alts.length ? 'Free in that same window, and usual for this session: ' + _alts.join(', ') + ' - offer those, or another time.' : 'No other usual room is free then - offer 2-3 other times.') + ' Never offer the same room at the same time again.' } }];"""
BS_HUMAN_NEW = """    human: lines + '. Nothing was booked. ' + (_alts.length ? (_commonMode ? 'Free in that same window: ' : 'Free in that same window, and usual for this session: ') + _alts.join(', ') + ' - offer those, or another time.' : (_commonMode ? 'No other conference room is free then - offer 2-3 other times.' : 'No other usual room is free then - offer 2-3 other times.')) + ' Never offer the same room at the same time again, and never offer a room this check did not list.' } }];"""

def book_fix(w):
    w["name"] = "Jessie — Book Session — v59 (v58 fixed)"
    n = node(w, "Check Conflicts")["parameters"]
    c = n["jsCode"]
    c = sub1(c, BS_LET_OLD, BS_LET_NEW, "B let")
    c = sub1(c, BS_ALTS_OLD, BS_ALTS_NEW, "B alternatives")
    c = sub1(c, BS_LINES_OLD, BS_LINES_NEW, "C lines")
    c = sub1(c, BS_HUMAN_OLD, BS_HUMAN_NEW, "B human")
    n["jsCode"] = c
    return w

if __name__ == "__main__":
    m = main_fix(json.load(open(sys.argv[1]))); json.dump(m, open(sys.argv[2], "w"), indent=2, ensure_ascii=False)
    b = book_fix(json.load(open(sys.argv[3]))); json.dump(b, open(sys.argv[4], "w"), indent=2, ensure_ascii=False)
    print("wrote", sys.argv[2], "and", sys.argv[4])
