#!/usr/bin/env python3
"""Room Availability v12 (week check fix) + main v197 (week check fix) - PENDING 62.
  scripts/build-week-check.py <ra-live> <ra-out> <main-live> <main-out>

29 Sep 23:17 PHT: "this week" availability came back "Studio 7 is taken in that window by SPORT / Alex Gorne / AEG.
Dates checked: Monday, September 27, 2027." The model sent ONE window, Monday to Sunday, and Room Availability answered
for the whole span - a room is "taken" if anything overlaps it at any point in the week - and Monday had already passed
(Thursday 30 Sep in the QA calendar). Gate Context's "this week" ran from the week's Monday; the "Dates checked" line
read only the window's first day.

Room Availability v12: a window over more than one day is answered day by day - the same hours each day (the window's
start and end times; the whole day when it runs midnight to midnight), at most 14 days. For a named room: each day
free, or taken and by what and when. With no room: each day's free rooms (the usual rooms for the session type when one
is given). Status OK with `days`; `asked.status` MULTI_DAY, so Guard Probe's "that room is busy" check does not read
a week as one booking. A one-day window is answered exactly as before.
main v197: "this week" runs from today to Sunday; "Dates checked" covers the window's first to last day; the Room
Availability tool description says to pass a range of days as one window.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label, n=1):
    if s.count(old) != n: raise SystemExit(f"{label}: expected {n} match(es), found {s.count(old)}")
    return s.replace(old, new)

RA_ANCHOR = "const out = { status:'OK', window: { start: REQ.start_iso, end: REQ.end_iso }, asked: askedAnswer,"
RA_BLOCK = r"""// v12 (PENDING 62): a window over several days ("this week") is answered day by day, the same hours each day. As one
// block, a room was "taken" if anything touched it all week, and the requester could not tell which day was free.
{
  const _H = 3600000, _D = 86400000;
  const _day0 = t => { const d = new Date(t + 8 * _H); return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) - 8 * _H; };
  const _tod = t => Math.round((t - _day0(t)) / 60000);
  const _first = _day0(reqStart), _last = _day0(reqEnd - 1);
  const _n = Math.round((_last - _first) / _D) + 1;
  if (_n > 1) {
    let _a = _tod(reqStart), _b = _tod(reqEnd); if (_b === 0) _b = 1440;
    const _whole = !(_a < _b) || (_a === 0 && _b >= 1439);
    if (_whole) { _a = 0; _b = 1440; }
    const _hm = t => new Date(t).toLocaleTimeString('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' });
    const _lbl = t => new Date(t + 12 * _H).toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' });
    const _iso = t => new Date(t + 8 * _H).toISOString().slice(0, 10);
    const _roomsOf = ev => {
      const emails = (ev.attendees || []).map(a => String(a.email || '').toLowerCase());
      const loc = String(ev.location || '').toLowerCase(), seg = String(ev.summary || '').split(' - ')[0].trim().toLowerCase();
      return keys.filter(k => emails.indexOf(ROOMS[k].toLowerCase()) !== -1 || (loc && loc.indexOf(k.toLowerCase()) !== -1) || seg === k.toLowerCase());
    };
    const _evs = events.map(ev => ({ s: evMs(ev.start && (ev.start.dateTime || ev.start.date)), e: evMs(ev.end && (ev.end.dateTime || ev.end.date)),
      title: ev.summary || '(no title)', allDay: !!(ev.start && ev.start.date && !ev.start.dateTime), rooms: _roomsOf(ev) }));
    const _studiosOnly = String(REQ.scope || '').toLowerCase() === 'studios';
    const _one = askedList.length ? askedList.map(answerFor) : [];
    // a room that is not a room, or not run for this session type, is answered once, not per day
    const _fixed = _one.find(x => x.status === 'UNKNOWN_ROOM' || x.status === 'NOT_RUN_HERE');
    if (!_fixed && _n <= 14) {
      const days = [], lines = [];
      for (let i = 0; i < _n; i++) {
        const d0 = _first + i * _D;
        const ws = Math.max(reqStart, d0 + _a * 60000), we = Math.min(reqEnd, d0 + _b * 60000);
        if (!(we > ws)) continue;
        const busyD = {};
        for (const ev of _evs) if (ev.s < we && ev.e > ws) for (const k of ev.rooms) (busyD[k] = busyD[k] || []).push(ev);
        const day = { date: _iso(d0), label: _lbl(d0), window: { start: new Date(ws).toISOString(), end: new Date(we).toISOString() } };
        const _desc = evs => evs.map(ev => ev.allDay ? 'all day by "' + ev.title + '"' : _hm(Math.max(ev.s, d0)) + ' – ' + _hm(Math.min(ev.e, d0 + _D)) + ' by "' + ev.title + '"').join(', ');
        if (askedList.length) {
          day.rooms = askedList.map(r => { const hit = keys.find(k => k.toLowerCase() === r.toLowerCase()) || r;
            return busyD[hit] ? { room: hit, status: 'BUSY', taken: _desc(busyD[hit]) } : { room: hit, status: 'FREE' }; });
          lines.push('- ' + day.label + ': ' + day.rooms.map(x => (day.rooms.length > 1 ? x.room + ' ' : '') + (x.status === 'FREE' ? 'free' : 'taken ' + x.taken)).join('; '));
        } else {
          const fr = n => !busyD[n];
          if (st && (priority.length || lastResort.length)) {
            day.free_priority = priority.filter(fr); day.free_last_resort = lastResort.filter(fr);
            lines.push('- ' + day.label + ': ' + (day.free_priority.length ? day.free_priority.join(', ')
              : 'none of the usual rooms' + (day.free_last_resort.length ? ' (also free: ' + day.free_last_resort.join(', ') + ')' : '')));
          } else {
            day.free_rooms = Object.keys(active).filter(fr).filter(n => !(_studiosOnly && isCommon[n])).sort();
            lines.push('- ' + day.label + ': ' + (day.free_rooms.length ? day.free_rooms.join(', ') : 'nothing free'));
          }
        }
        days.push(day);
      }
      if (days.length) {
        const hours = _whole ? 'all day' : _hm(_first + _a * 60000) + ' – ' + _hm(_first + _b * 60000);
        const head = askedList.length ? askedRaw + ', ' + hours + ', day by day:'
          : (st ? 'Free for ' + String(REQ.session_type || '').trim() : (_studiosOnly ? 'Free studios and booths' : 'Free rooms')) + ', ' + hours + ', day by day:';
        const outM = { status: 'OK', multi_day: true, window: { start: REQ.start_iso, end: REQ.end_iso },
          hours: _whole ? 'all day' : { from: _hm(_first + _a * 60000), to: _hm(_first + _b * 60000) }, days,
          asked: askedList.length ? { room: askedRaw, status: 'MULTI_DAY', days: days.map(d => ({ date: d.date, rooms: d.rooms })) } : null,
          human: head + '\n' + lines.join('\n') + '\nGive this day by day as it is; do not merge the days or add rooms.' };
        if (st) outM.session_type = st;
        if (unidentified.length) { outM.unidentified = unidentified; outM.human += ' Note: ' + unidentified.length + ' event(s) in that window have no identifiable room, so treat this as incomplete.'; }
        return [{ json: outM }];
      }
    }
  }
}
"""

# main: Gate Context "this week" from today
GATE_OLD = "if ((rm = msgText.match(/\\bthis\\s+week\\b/i))) rangeNote(rm[0], weekMonday, addDays(weekMonday, 6));"
GATE_NEW = ("// v197 (PENDING 62): from today, not from the week's Monday - the days already past are not available to book.\n"
            "if ((rm = msgText.match(/\\bthis\\s+week\\b/i))) rangeNote(rm[0], today, addDays(weekMonday, 6));")
# main: Guard Probe "Dates checked" - every day of the window, not only its first
GP_OLD = "for (const s of _st) { const ti = ((s || {}).action || {}).toolInput || {}; for (const k of ['window_start', 'booking_date', 'start']) { const m = String(ti[k] || '').match(/\\d{4}-\\d{2}-\\d{2}/); if (m) _ds.add(m[0]); } }"
GP_NEW = ("for (const s of _st) { const ti = ((s || {}).action || {}).toolInput || {}; for (const k of ['window_start', 'booking_date', 'start']) { const m = String(ti[k] || '').match(/\\d{4}-\\d{2}-\\d{2}/); if (m) _ds.add(m[0]); }\n"
          "      // v197 (PENDING 62): a window over several days - every day of it, not only the first\n"
          "      const _w0 = String(ti.window_start || '').match(/\\d{4}-\\d{2}-\\d{2}/), _w1 = String(ti.window_end || '').match(/\\d{4}-\\d{2}-\\d{2}/);\n"
          "      if (_w0 && _w1) for (let _t = Date.parse(_w0[0] + 'T00:00:00Z'), _e = Date.parse(_w1[0] + 'T00:00:00Z'), _c = 0; _t <= _e && _c < 31; _t += 86400000, _c++) _ds.add(new Date(_t).toISOString().slice(0, 10)); }")
STRIP_OLD = "text = text.replace(/[ \\t]*(?:List exactly these and no others|Name every one of them, and nothing else)\\.?/gi, '');"
STRIP_NEW = "text = text.replace(/[ \\t]*(?:List exactly these and no others|Name every one of them, and nothing else|Give this day by day as it is; do not merge the days or add rooms)\\.?/gi, '');   // v197: + the day-by-day instruction"
DESC_OLD = "Find out whether a room is free, or which rooms are free, in a window."
DESC_NEW = ("Find out whether a room is free, or which rooms are free, in a window. For a range of days (\"this week\", "
            "\"Monday to Friday\") pass it as one window - the first day at the start time to the last day at the end time - "
            "and it answers day by day, the same hours each day; relay that list day by day.")

def ra(w):
    w["name"] = "Jessie — Room Availability — v12 (week check fix)"
    c = node(w, "Compute Availability")["parameters"]; c["jsCode"] = sub1(c["jsCode"], RA_ANCHOR, RA_BLOCK + RA_ANCHOR, "ra anchor")
    return w

def main(w):
    w["name"] = "Project Jessie — v197 (week check fix)"
    g = node(w, "Gate Context")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GATE_OLD, GATE_NEW, "gate")
    p = node(w, "Guard Probe")["parameters"]; p["jsCode"] = sub1(p["jsCode"], GP_OLD, GP_NEW, "guard")
    p["jsCode"] = sub1(p["jsCode"], STRIP_OLD, STRIP_NEW, "strip")
    t = node(w, "Room Availability")["parameters"]; t["description"] = sub1(t["description"], DESC_OLD, DESC_NEW, "desc")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(ra(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
