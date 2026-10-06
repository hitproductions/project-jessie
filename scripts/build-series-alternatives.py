#!/usr/bin/env python3
"""Book Session v93 + Book Series v6 + main v227 (series alternatives) - decided 6 Oct (Howard), after the taken-date test
(15:47-15:49: 15 Oct was only left out):
  - a taken date in a series gets a replacement on the card, worked out in code and checked like every other date:
    1. another usual room for the session type at the same time; else
    2. the same room at the nearest free time of the same length that day, between 8 AM and 10 PM; else
    3. left out, and the card says so.
  - the requester changes single dates BEFORE the yes ("skip the 15th", "use Studio F on the 15th", "make the 15th 7-10pm"):
    Jessie prepares the series again with those changes and shows a new card. The yes still books exactly the card.

Book Session v93 (prepare mode, series_alt = true - only Book Series sets it)
  - Get Events In Window reads the whole day 8 AM - 10 PM (conflicts are still only the events overlapping the window).
  - On ROOM_OCCUPIED (not the requester's own booking, one room asked): swap to the first free usual room (Check Conflicts'
    own _alts); else, timed bookings, the nearest free slot of the same length in that room - an event with no room counts
    as busy. The swap falls through to CLEAR, so the card and every remaining check use the new room / time, and `swap`
    says what changed. Render Summary passes swap and the final room / times on.
Book Series v6
  - `changes` (prepare): one per line "YYYY-MM-DD skip" | "YYYY-MM-DD room <room>" | "YYYY-MM-DD HH:MM-HH:MM"; a changed date
    is checked as asked (no swap). `per_date` (book): {date: {rooms, start, end}} - each date in its own room and time.
  - the card: a swapped date reads "- Friday, 15 October 2027 · Studio 8 (Studio 7 is taken)" or
    "· 6:00 PM – 9:00 PM (Studio 7 is taken 3:00 – 6:00 PM)"; a changed one "· Studio F"; skipped ones are named. The base
    Time / Room lines are the series' own. per_date is stored with the series (and in its integrity code).
main v227
  - Prepare Series takes `changes` ($fromAI series_changes); Series Direct passes the stored per_date; the prompt says how a
    single date is changed before the yes.
  scripts/build-series-alternatives.py <book-session-v92> <book-session-out> <book-series-v5> <book-series-out> <main-v226> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label, count=1):
    if s.count(old) != count: raise SystemExit(f"{label}: expected {count} match(es), found {s.count(old)}")
    return s.replace(old, new)

# ================================================================ Book Session v93
Q_OLD = """  return { start: start, end: end };"""
Q_NEW = """  // v93 (series alternatives): a series date being prepared reads its whole day, 8 AM - 10 PM, so a taken room can be swapped
  // for another room or time. Conflicts are still only the events that overlap the window.
  if ((j.series_alt === true || String(j.series_alt).toLowerCase() === 'true') && String(j.mode || '').trim().toLowerCase() === 'prepare') {
    var _d = start.slice(0, 10), _a = _d + 'T08:00:00+08:00', _b = _d + 'T22:00:00+08:00';
    if (new Date(_a).getTime() < new Date(start).getTime()) start = _a;
    if (new Date(_b).getTime() > new Date(end).getTime()) end = _b;
  }
  return { start: start, end: end };"""

SWAP_DECL_OLD = "let __roomSuggested = '', __roomDefault = '';"
SWAP_DECL_NEW = "let __swap = null;   // v93: a series date moved to another room or time (Book Series' series_alt)\nlet __roomSuggested = '', __roomDefault = '';"

OCC_OLD = """  // v51: the final details ride along so Prepare Booking can render a summary for a consent-eligible clash.
  return [{ json: { verdict:'REJECTED', reason:'ROOM_OCCUPIED', conflicts, final_rooms: REQ.rooms,"""
OCC_NEW = r"""  // v93 (decided 6 Oct): a series date whose room is taken gets a replacement, checked here like the rest - another usual
  // room at the same time (the _alts above), else the same room at the nearest free time of the same length that day,
  // 8 AM - 10 PM. Only when Book Series asks (series_alt), only in prepare mode, and only for one room. It falls through to
  // CLEAR with the new room / time, so the card and the remaining checks use them.
  if (__prep && (REQ.series_alt === true || String(REQ.series_alt).toLowerCase() === 'true') && wanted.length === 1) {
    try {
      const _fromRooms = wanted.map(w => w.name).join(', '), _fs = REQ.start_iso, _fe = REQ.end_iso;
      if (_alts.length) {
        REQ.rooms = _alts[0]; __swap = { kind: 'room', from_rooms: _fromRooms, from_start: _fs, from_end: _fe, to_rooms: _alts[0], to_start: _fs, to_end: _fe };
      } else if (!allDay) {
        const _D = reqEnd - reqStart, _day = String(REQ.start_iso).slice(0, 10);
        const _lo = Date.parse(_day + 'T08:00:00+08:00'), _hi = Date.parse(_day + 'T22:00:00+08:00');
        const _blk = EVENTS.filter(ev => ev && ev.id && ev.status !== 'cancelled' && !(exclude && ev.id === exclude))
          .map(ev => ({ s: evMs(ev.start && (ev.start.dateTime || ev.start.date)), e: evMs(ev.end && (ev.end.dateTime || ev.end.date)), r: roomsOf(ev) }))
          .filter(b => !b.r.length || b.r.indexOf(wanted[0].name) !== -1);
        const _cands = [];
        for (let t = _lo; t + _D <= _hi; t += 30 * 60000) _cands.push(t);
        _cands.sort((a, b) => (Math.abs(a - reqStart) - Math.abs(b - reqStart)) || (b - a));   // nearest first, later on a tie
        const _iso = ms => new Date(ms + 8 * 3600000).toISOString().slice(0, 19) + '+08:00';
        const _t = _cands.find(t => t !== reqStart && _blk.every(b => !(b.s < t + _D && b.e > t)));
        if (_D > 0 && _t !== undefined) {
          REQ.start_iso = _iso(_t); REQ.end_iso = _iso(_t + _D);
          __swap = { kind: 'time', from_rooms: _fromRooms, from_start: _fs, from_end: _fe, to_rooms: _fromRooms, to_start: REQ.start_iso, to_end: REQ.end_iso };
        }
      }
    } catch (e) { __swap = null; }
  }
  if (!__swap)
  // v51: the final details ride along so Prepare Booking can render a summary for a consent-eligible clash.
  return [{ json: { verdict:'REJECTED', reason:'ROOM_OCCUPIED', conflicts, final_rooms: REQ.rooms,"""
CLEAR_OLD = "return [{ json: { verdict:'CLEAR', duration_note: durationNote,"
CLEAR_NEW = "return [{ json: { verdict:'CLEAR', swap: __swap, duration_note: durationNote,"
RS_OLD = "return [{ json: { status: 'PREPARED', summary_text: out,"
RS_NEW = "return [{ json: { status: 'PREPARED', swap: CC.swap || null, final_rooms: CC.final_rooms || REQ.rooms || '', final_start: CC.final_start || '', final_end: CC.final_end || '', summary_text: out,"   # v93

def book_session(w):
    w["name"] = "Jessie — Book Session — v93 (series alternatives)"
    tr = node(w, "When Executed by Another Workflow")["parameters"]["workflowInputs"]["values"]
    if not any(v["name"] == "series_alt" for v in tr): tr.append({"name": "series_alt", "type": "boolean"})
    q = node(w, "Get Events In Window")["parameters"]["queryParameters"]["parameters"]
    for p in q:
        if p["name"] in ("timeMin", "timeMax"): p["value"] = sub1(p["value"], Q_OLD, Q_NEW, "query " + p["name"])
    cc = node(w, "Check Conflicts")["parameters"]; s = cc["jsCode"]
    s = sub1(s, SWAP_DECL_OLD, SWAP_DECL_NEW, "swap decl"); s = sub1(s, OCC_OLD, OCC_NEW, "occupied"); s = sub1(s, CLEAR_OLD, CLEAR_NEW, "clear")
    cc["jsCode"] = s
    rs = node(w, "Render Summary")["parameters"]; rs["jsCode"] = sub1(rs["jsCode"], RS_OLD, RS_NEW, "render")
    return w

# ================================================================ Book Series v6
ED_OLD = """const __prep = String(REQ.mode || '').trim().toLowerCase() === 'prepare';"""
ED_NEW = r"""const __prep = String(REQ.mode || '').trim().toLowerCase() === 'prepare';
// v6 (series alternatives): changes the requester asked for to single dates, before the yes - one per line:
// "YYYY-MM-DD skip" | "YYYY-MM-DD room <room>" | "YYYY-MM-DD HH:MM-HH:MM". A line that does not read that way is ignored.
const __chg = {};
String(REQ.changes || '').split(/\n|;/).map(s => s.trim()).filter(Boolean).forEach(l => {
  const m = l.match(/^(\d{4}-\d{2}-\d{2})\s*:?\s+(?:(skip)|room\s+(.+)|(\d{1,2}:\d{2})\s*(?:-|–|to)\s*(\d{1,2}:\d{2}))\s*$/i);
  if (m) __chg[m[1]] = m[2] ? { skip: true } : m[3] ? { rooms: m[3].trim() } : { start: m[4].padStart(5, '0'), end: m[5].padStart(5, '0') };
});
// v6: at the yes (Series Direct), each date in the room and time that was on the card
let __per = {}; try { __per = typeof REQ.per_date === 'string' ? JSON.parse(REQ.per_date || '{}') : (REQ.per_date || {}); } catch (e) { __per = {}; }"""
ED_RET_OLD = """return res.occurrences.map(function(o){"""
ED_RET_NEW = """const __occ = __prep ? res.occurrences.filter(o => { const d = o.all_day ? o.date : String(o.start_iso).slice(0, 10); return !(__chg[d] && __chg[d].skip); }) : res.occurrences;
if (!__occ.length) return [{ json: { _go:false, status:'MISSING_DETAILS', human:'Every date of that series was left out - nothing to book.' } }];
return __occ.map(function(o){"""
ED_DATE_OLD = """  if (__prep) j.expected_date = j._date;"""
ED_DATE_NEW = """  if (__prep) j.expected_date = j._date;
  // v6: a series date whose room is taken gets another room / time (Book Session v93) - unless the requester set this date
  const _c = __chg[j._date], _p = __per[j._date];
  if (__prep) j.series_alt = !_c;
  const _set = (x) => { if (x.rooms) j.rooms = x.rooms; if (x.start && x.end && !j.all_day) { j.start_iso = j._date + 'T' + x.start + ':00+08:00'; j.end_iso = j._date + 'T' + x.end + ':00+08:00'; } };
  if (__prep && _c && !_c.skip) { _set(_c); j._changed = true; }
  if (!__prep && _p) _set(_p);"""

AG_LOOP_OLD = """    // v5: every date in the first date's room - one prepared in another room (no room named) means that room was not free
    if (r.status === 'PREPARED' && P && P.F && !r.needs_consent && (!first || pbNorm(P.F['Room']) === pbNorm(first.P.F['Room']))) { ok.push(d); if (!first) first = { r, P, d }; }"""
AG_LOOP_NEW = """    // v6: a date swapped by Book Session (r.swap) or set by the requester (_changed) keeps its own room / time; otherwise
    // every date is in the first date's room (v5) - another room there means that room was not free
    const _own = !!r.swap || !!occ[i]._changed;
    if (r.status === 'PREPARED' && P && P.F && !r.needs_consent && (_own || !first || pbNorm(P.F['Room']) === pbNorm(first.P.F['Room']))) {
      ok.push(d); if (_own) moved[d] = { r, P, swap: r.swap || null, changed: !!occ[i]._changed }; else if (!first) first = { r, P, d };
      if (!any) any = { r, P, d };
    }"""
AG_DECL_OLD = """  const ok = [], taken = [];
  let first = null, ask = null;"""
AG_DECL_NEW = """  const ok = [], taken = [], moved = {};
  let first = null, ask = null, any = null;"""
AG_NOFIRST_OLD = """  if (!first) return [{ json: { status: 'REJECTED', reason: 'ROOM_OCCUPIED',"""
AG_NOFIRST_NEW = """  if (!first && any) first = any;   // v6: every date moved - the series' own room / time come from the first one's swap
  if (!first) return [{ json: { status: 'REJECTED', reason: 'ROOM_OCCUPIED',"""
AG_CARD_OLD = """  const F = first.P.F;
  const shown = ok.map(long);"""
AG_CARD_NEW = r"""  const F = Object.assign({}, first.P.F);
  const tl = iso => new Date(iso).toLocaleTimeString('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' });
  const hm = iso => { const m = String(iso || '').match(/T(\d{2}:\d{2})/); return m ? m[1] : ''; };
  if (moved[first.d] && first.r.swap) {   // the base lines are the series' own, not this date's replacement
    F['Room'] = first.r.swap.from_rooms; if (!occ[0].all_day) F['Time'] = tl(first.r.swap.from_start) + ' – ' + tl(first.r.swap.from_end);
  }
  const perDate = {};
  const shown = ok.map(d => {
    const m = moved[d]; if (!m) return long(d);
    const rm = String(m.r.final_rooms || m.P.F['Room'] || ''), st = m.r.final_start || '', en = m.r.final_end || '';
    perDate[d] = { rooms: rm, start: hm(st), end: hm(en) };
    const sameRoom = pbNorm(rm) === pbNorm(F['Room']), sameTime = !st || (tl(st) + ' – ' + tl(en)) === F['Time'];
    const what = [sameRoom ? '' : rm, sameTime ? '' : tl(st) + ' – ' + tl(en)].filter(Boolean).join(', ');
    const why = m.swap ? (m.swap.kind === 'room' ? ' (' + m.swap.from_rooms + ' is taken)' : ' (' + m.swap.from_rooms + ' is taken ' + tl(m.swap.from_start) + ' – ' + tl(m.swap.from_end) + ')') : '';
    return long(d) + (what ? ' · ' + what + why : '');
  });
  const _skipAsked = Object.keys(__chgAsked).filter(d => __chgAsked[d].skip).sort();"""
AG_TAKEN_OLD = """  if (taken.length) notes.unshift('Heads up: ' + F['Room'] + ' is taken on ' + taken.map(long).join(', ') + ' - ' + (taken.length === 1 ? 'that date' : 'those dates') + ' left out.');"""
AG_TAKEN_NEW = """  if (taken.length) notes.unshift('Heads up: ' + F['Room'] + ' is taken on ' + taken.map(long).join(', ') + ', and no other usual room or time that day is free - ' + (taken.length === 1 ? 'that date' : 'those dates') + ' left out.');
  if (_skipAsked.length) notes.unshift('Left out as asked: ' + _skipAsked.map(long).join(', ') + '.');"""
AG_INPUTS_OLD = """    requester_text: String(REQ0.requester_text || '') };"""
AG_INPUTS_NEW = """    requester_text: String(REQ0.requester_text || ''), per_date: JSON.stringify(perDate) };   // v6: each date's own room / time"""
AG_PREP_OLD = """if (String(REQ0.mode || '').trim().toLowerCase() === 'prepare') {"""
AG_PREP_NEW = """if (String(REQ0.mode || '').trim().toLowerCase() === 'prepare') {
  const __chgAsked = {};   // v6: the requester's changes, read the same way Expand Dates reads them
  String(REQ0.changes || '').split(/\\n|;/).map(s => s.trim()).filter(Boolean).forEach(l => { const m = l.match(/^(\\d{4}-\\d{2}-\\d{2})\\s*:?\\s+(skip)\\s*$/i); if (m) __chgAsked[m[1]] = { skip: true }; });"""

def book_series(w):
    w["name"] = "Jessie — Book Series — v6 (series alternatives)"
    tr = node(w, "When Executed by Another Workflow")["parameters"]["workflowInputs"]["values"]
    for k in ("changes", "per_date"):
        if not any(v["name"] == k for v in tr): tr.append({"name": k})
    ed = node(w, "Expand Dates")["parameters"]; s = ed["jsCode"]
    s = sub1(s, ED_OLD, ED_NEW, "ed chg"); s = sub1(s, ED_RET_OLD, ED_RET_NEW, "ed ret"); s = sub1(s, ED_DATE_OLD, ED_DATE_NEW, "ed date"); ed["jsCode"] = s
    ag = node(w, "Aggregate")["parameters"]; s = ag["jsCode"]
    for a, b, l in ((AG_PREP_OLD, AG_PREP_NEW, "prep"), (AG_DECL_OLD, AG_DECL_NEW, "decl"), (AG_LOOP_OLD, AG_LOOP_NEW, "loop"), (AG_NOFIRST_OLD, AG_NOFIRST_NEW, "nofirst"),
                    (AG_CARD_OLD, AG_CARD_NEW, "card"), (AG_TAKEN_OLD, AG_TAKEN_NEW, "taken"), (AG_INPUTS_OLD, AG_INPUTS_NEW, "inputs")):
        s = sub1(s, a, b, "agg " + l)
    ag["jsCode"] = s
    return w

# ================================================================ main v227
PROMPT_OLD = """Their yes books the series automatically - do not call Book Series yourself."""
PROMPT_NEW = """Their yes books the series automatically - do not call Book Series yourself. When a date's room is taken, the card already shows another room or time for it. To change single dates before the yes - skip one, another room, another time - call Prepare Series again with the same pattern and details plus the changes, and send its new card."""
CHANGES_EXPR = ("={{ $fromAI('series_changes', 'Changes the requester asked for to single dates of this series, one per line: YYYY-MM-DD skip, "
                "or YYYY-MM-DD room followed by the exact room name, or YYYY-MM-DD HH:MM-HH:MM for another time that day. Empty when they asked for none.', 'string', '') }}")

def main(w):
    w["name"] = "Project Jessie — v227 (series alternatives)"
    ps = node(w, "Prepare Series")["parameters"]["workflowInputs"]
    ps["value"]["changes"] = CHANGES_EXPR
    for k in ("changes", "per_date"):
        if not any(c.get("id") == k for c in ps["schema"]):
            ps["schema"].append({"id": k, "displayName": k, "required": False, "defaultMatch": False, "display": True, "canBeUsedToMatch": True, "type": "string"})
    sd = node(w, "Series Direct")["parameters"]["workflowInputs"]["value"]
    sd["per_date"] = "={{ $('Prepared Series').first().json._seriesDirect.p.per_date || '{}' }}"; sd["changes"] = ""
    ag = node(w, "Jessie AI Agent")["parameters"]["options"]; ag["systemMessage"] = sub1(ag["systemMessage"], PROMPT_OLD, PROMPT_NEW, "prompt")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    for f, i, o in [(book_session, 0, 1), (book_series, 2, 3), (main, 4, 5)]:
        json.dump(f(json.load(open(a[i]))), open(a[o], "w"), indent=2, ensure_ascii=False); print("wrote", a[o])
