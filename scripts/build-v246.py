#!/usr/bin/env python3
"""Room Availability v20 + main v246 (availability read in code) - live 8 Oct 21:44 on main v245 (Haiku 5.5): "what time is
studio 7 free tom" -> "Studio 7 is taken all day tomorrow ... by CATTAIL / Sasa Abella / HL, so it's not free at any time."
The booking was 1:00-3:00 PM. Room Availability answered a room asked about with only "Studio 7 is taken in that window by
..." - no times - and for a whole day the window IS the day, so "taken in that window" read as "taken all day". Its
code-written layout ("Free all day ... Studio 7 (free except 1:00 PM - 3:00 PM)") was built only when no room was named,
and main sent it only when the model's own reply had no question mark. A wrong read of the calendar, not a model quirk.

Room Availability v20:
  - every room asked about carries what is booked and when (`booked`: times + titles, `whole_window`, `free_gaps`) and its
    human text says so: "Studio 7 is booked 1:00 PM - 3:00 PM (CATTAIL / Sasa Abella / HL) - free the rest of the day."
    Status stays BUSY for any overlap (nothing downstream changes); "booked all day" only when it really covers the window.
  - a reply is written in code for a room asked about too, one day or several: the room's line first, then for a day
    "Free all day:" and each room booked for part of it with its times; for a set time, the other rooms free then (the
    usual rooms for a session type, when one was given).
  - the part-booked lines read "Studio 5: booked 12:00 PM - 3:00 PM, free the rest of the day." (was "(free except ...)").
main v246 (Guard Probe): Room Availability's reply is the answer whenever it wrote one and the reply is not a card - a
  question or "free" in the model's text no longer decides it. The model's closing question is kept only when it states
  nothing about rooms or times ("Want one of those?").
  scripts/build-v246.py <ra-v19> <ra-out> <main-v245> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

HELPERS = r"""// v20 (8 Oct 21:44, a wrong read): "what time is studio 7 free tom" was answered "taken all day" for a 1-3 PM booking -
// the room asked about came back as "taken in that window" with no times, and for a day the window is the day. Every room
// asked about now carries its booked times, its free gaps, and a line written here, never by the model.
function __hmx(t) { return new Date(t).toLocaleTimeString('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' }); }
function __roomRead(n, ws, we, ivs) {
  const whole = we - ws >= 8 * 3600000;
  const a = [].concat(ivs || []).map(x => ({ s: Math.max(x.s, ws), e: Math.min(x.e, we), title: x.title || '(no title)' })).filter(x => x.e > x.s).sort((x, y) => x.s - y.s);
  const m = [];
  for (const x of a) { const l = m[m.length - 1]; if (l && x.s <= l.e) { l.e = Math.max(l.e, x.e); if (l.titles.indexOf(x.title) === -1) l.titles.push(x.title); } else m.push({ s: x.s, e: x.e, titles: [x.title] }); }
  const span = whole ? 'all day' : __hmx(ws) + ' – ' + __hmx(we);
  if (!m.length) return { status: 'FREE', booked: [], whole_window: false, gaps: [span], line: '✅ ' + n + ' is free ' + span + '.' };
  const covers = m.length === 1 && m[0].s <= ws && m[0].e >= we;
  const booked = m.map(x => ({ start: new Date(x.s).toISOString(), end: new Date(x.e).toISOString(),
    time: (whole && x.s <= ws && x.e >= we) ? 'all day' : __hmx(x.s) + ' – ' + __hmx(x.e), titles: x.titles }));
  const gaps = []; let c = ws;
  for (const x of m) { if (x.s > c) gaps.push(__hmx(c) + ' – ' + __hmx(x.s)); c = Math.max(c, x.e); }
  if (c < we) gaps.push(__hmx(c) + ' – ' + __hmx(we));
  const what = booked.map(b => b.time + ' (' + b.titles.join(', ') + ')').join(' and ');
  const line = covers ? '❌ ' + n + ' is booked ' + span + ' (' + booked[0].titles.join(', ') + ').'
    : '⚠️ ' + n + ' is booked ' + what + (whole ? ' - free the rest of the day.' : ' - free ' + gaps.join(' and ') + '.');
  return { status: 'BUSY', booked, whole_window: covers, gaps: covers ? [] : gaps, line };
}
"""

def ra(w):
    w["name"] = "Jessie — Room Availability — v20 (times for the room asked about)"
    n = node(w, "Compute Availability")["parameters"]; s = n["jsCode"]
    # 1. intervals beside the busy titles
    s = once(s, "const busy = {}, unidentified = [];", "const busy = {}, busyIv = {}, unidentified = [];   // v20: busyIv = what and when, per room", "busy decl")
    s = once(s, "      busy[k] = ev.summary || '(no title)'; matched = true;\n",
             "      busy[k] = ev.summary || '(no title)'; matched = true;\n"
             "      (busyIv[k] = busyIv[k] || []).push({ s: Math.max(s0, reqStart), e: Math.min(e0, reqEnd), title: ev.summary || '(no title)' });   // v20\n", "busyIv push")
    # 2. the room asked about: times in its answer
    s = once(s, """  if (busy[hit]) {
    return { room: hit, status: 'BUSY', taken_by: busy[hit],
      human: hit + ' is taken in that window by "' + busy[hit] + '".' };
  }""", """  if (busy[hit]) {   // v20: with what is booked when, and what is still free - never "taken in that window" alone
    const _rr = __roomRead(hit, reqStart, reqEnd, busyIv[hit]);
    return { room: hit, status: 'BUSY', taken_by: busy[hit], booked: _rr.booked, whole_window: _rr.whole_window, free_gaps: _rr.gaps,
      human: _rr.line.replace(/^\\S+\\s/, '') };
  }""", "answerFor BUSY")
    # 3. helpers, next to the other layout helpers
    s = once(s, "// v13 (decided 2 Oct): the free list laid out by category", HELPERS + "// v13 (decided 2 Oct): the free list laid out by category", "helpers")
    # 4. whole-day layout: leave out the rooms already answered; part-booked lines in the new wording
    s = once(s, "function __wholeDay(ws, we, sOnly) {", "function __wholeDay(ws, we, sOnly, excl) {", "wholeDay sig")
    s = once(s, "  const cand = [...new Set(Object.keys(active).concat(boothNames))].filter(n => !(sOnly && isCommon[n]));",
             "  const cand = [...new Set(Object.keys(active).concat(boothNames))].filter(n => !(sOnly && isCommon[n])).filter(n => !(excl || []).includes(n));   // v20: rooms answered above", "wholeDay excl")
    s = once(s, "    for (const [n, m] of partial) lines.push('⚠️ ' + n + ' (free except ' + m.map(x => _hmx(x[0]) + ' – ' + _hmx(x[1])).join(', ') + ').'); }",
             "    for (const [n, m] of partial) lines.push('⚠️ ' + n + ': booked ' + m.map(x => _hmx(x[0]) + ' – ' + _hmx(x[1])).join(' and ') + ', free the rest of the day.'); }   // v20 (was \"(free except ...)\")", "partial wording")
    # 5. one window, a room asked about: the reply written here
    s = once(s, "// Booth availability is computed here rather than left to the model to work out",
             """// v20: a room asked about is answered here as well - its line first, then the rest of the day (or the other rooms free
// at that time). Only for plain FREE / BUSY answers; "not normally used for" and unknown rooms stay with the model.
if (askedAnswer && askedList.length) {
  const _hits = askedList.map(r => keys.find(k => k.toLowerCase() === r.toLowerCase()));
  const _each = askedAnswer.rooms || [askedAnswer];
  if (_hits.every(Boolean) && _each.every(a => a.status === 'FREE' || a.status === 'BUSY')) {
    const _sOnly = String(REQ.scope || '').toLowerCase() === 'studios';
    const _whole = reqEnd - reqStart >= 8 * 3600000;
    const _lines = _hits.map(h => __roomRead(h, reqStart, reqEnd, busyIv[h]).line);
    let _rest;
    if (_whole) {
      const _wl = __wholeDay(reqStart, reqEnd, _sOnly, _hits);
      _rest = _wl.length ? _wl.join('\\n') : '❌ No other room is free that day.';
    } else if (st && (priority.length || lastResort.length)) {
      const _u = priority.filter(free).filter(n => _hits.indexOf(n) === -1);
      _rest = _u.length ? '✅ Usual rooms for ' + String(REQ.session_type || '').trim() + ' free then:\\n' + __layout(_u).join('\\n') : '❌ No usual room for ' + String(REQ.session_type || '').trim() + ' is free then.';
    } else {
      const _o = Object.keys(active).filter(free).filter(n => _hits.indexOf(n) === -1 && !(_sOnly && isCommon[n]));
      const _L = __layout(_o.concat(boothNames.filter(n => free(n) && _o.indexOf(n) === -1 && _hits.indexOf(n) === -1)));
      _rest = _L.length ? '✅ Also free then:\\n' + _L.join('\\n') : '❌ No other room is free then.';
    }
    out.reply_text = __head(reqStart, _whole ? '' : ', ' + __hmx(reqStart) + ' – ' + __hmx(reqEnd)) + '\\n\\n' + _lines.join('\\n') + '\\n\\n' + _rest;
  }
}
// Booth availability is computed here rather than left to the model to work out""", "single-window reply")
    # 6. several days, a room asked about: day by day, its line each day
    s = once(s, "        if (st) outM.session_type = st;\n",
             """        // v20: a room asked about over several days - its line each day, with times, written here
        if (askedList.length && days.every(d => (d.rooms || []).length && d.rooms.every(x => x.status === 'FREE' || x.status === 'BUSY'))) {
          outM.reply_text = (_whole ? '' : askedRaw + ', ' + hours + ':\\n\\n') + days.map(d => { const _ws = Date.parse(d.window.start), _we = Date.parse(d.window.end);
            return __head(_ws) + '\\n' + d.rooms.map(x => __roomRead(x.room, _ws, _we, (x.events || []).map(ev => ({ s: Date.parse(ev.start), e: Date.parse(ev.end), title: ev.title }))).line).join('\\n'); }).join('\\n\\n');
        }
        if (st) outM.session_type = st;
""", "multi-day reply")
    # 7. two rooms read "8 and F", not "8, and F" (v13 layout, long-standing)
    s = once(s, "  const _and = a => a.length <= 1 ? a.join('') : a.slice(0, -1).join(', ') + ', and ' + a[a.length - 1];",
             "  const _and = a => a.length <= 1 ? a.join('') : a.length === 2 ? a[0] + ' and ' + a[1] : a.slice(0, -1).join(', ') + ', and ' + a[a.length - 1];   // v20: two rooms", "_and")
    n["jsCode"] = s
    return w

def main(w):
    w["name"] = "Project Jessie — v246 (availability read in code)"
    gp = node(w, "Guard Probe")["parameters"]
    gp["jsCode"] = once(gp["jsCode"],
        """    if (_oR && _oR.status === 'OK' && _oR.reply_text && !_prepared && !/\\?/.test(text) && !/\\*Date:\\*|Book it\\?|Confirm to/i.test(text) && /\\bfree\\b/i.test(text))
      text = String(_oR.reply_text);""",
        """    // v246 (8 Oct 21:44): "Studio 7 is taken all day" for a 1-3 PM booking. Room Availability's reply is the answer whenever it
    // wrote one and this is not a card; the model's closing question is kept only if it says nothing about rooms or times.
    if (_oR && _oR.status === 'OK' && _oR.reply_text && !_prepared && !/\\*Date:\\*|\\*Dates|\\*Moving to:\\*|Book it\\?|Cancel it\\?|Move it\\?|Confirm to/i.test(text)) {
      const _pp = text.trim().split(/\\n\\s*\\n/), _lp = String(_pp[_pp.length - 1] || '').trim();
      const _keepQ = /\\?\\s*$/.test(_lp) && _lp.length <= 160 && !/\\b(?:free|taken|booked|available|availability|occupied|busy|open|all day|studio|booth|room)\\b|\\d{1,2}(?::\\d{2})?\\s*(?:am|pm)\\b/i.test(_lp);
      text = String(_oR.reply_text) + (_keepQ ? '\\n\\n' + _lp : '');
    }""", "GP reply_text")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 4: print(__doc__.strip()); sys.exit(2)
    json.dump(ra(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
