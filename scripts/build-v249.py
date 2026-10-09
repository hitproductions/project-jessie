#!/usr/bin/env python3
"""main v249 + Book Session v101 + Room Availability v22 - PENDING 102-106 (9 Oct), from the 8 Oct 23:35-23:44 Slack
round on main v248 and QA round 3 (B6).

  102  When the room is taken: offer (1) the same room at the nearest free time that day, same length, 8 AM - 10 PM, one
       before and one after, the nearer first (back-to-back allowed); (2) other studios free then (as before); (3) other
       days for that room - one when a same-day time exists, else two (was three). Early room check (main) and Book
       Session's ROOM_OCCUPIED (prepare mode). Every time stays bookable: the window limits what is offered only.
  103  "book 11-1 instead" after a heads-up became 12-1 PM, as an availability answer:
         - Booked For reads a range with no am/pm by working hours (8-11 morning, 12 and 1-7 afternoon, the end the first
           reading after the start), and a range in the newest message is the time (timeForced) when it is the only one;
         - with no room named, a new time after a heads-up keeps the heads-up's room (the offers in it no longer count as
           "Jessie named another room"), and a new time is checked again even though the room was "already told";
         - Room Availability's layout replaces the reply only for an availability question, or when the model's reply asks
           nothing (v246 replaced it on booking turns too);
         - the details question restates what is known (room, date, time) before asking the rest.
  104  Day-by-day availability: an extra blank line between days (both layouts).
  105  The details question never asks "time" and "length" together - the time (range) gives the length.
  106  A Management meeting in a conference room is titled by the meeting, not the department: "SALIN - <meeting title>",
       with no title the person it is for ("SALIN - Vic Icasas"), with neither Prepare Booking asks "What's the meeting
       title?". Joint meetings ("KATHA - Mgmt x BD") keep their departments. Book Session + the prompt.

  scripts/build-v249.py <main-v248> <main-out> <book-v100> <book-out> <ra-v21> <ra-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# ------------------------------------------------------------------------------------------------ Room Availability v22
RA_HOURS_OLD = "    let _a = _tod(reqStart), _b = _tod(reqEnd); if (_b === 0) _b = 1440;\n"
RA_HOURS_NEW = RA_HOURS_OLD + r"""    // v22 (PENDING 102): main's early room check reads the whole day (8 AM - 10 PM, for the nearest free time) and passes the
    // hours asked for separately - each day's window is those hours.
    const _hrs = String(REQ.hours || '').match(/^(\d{2}):(\d{2})-(\d{2}):(\d{2})$/);
    if (_hrs) { const _ha = +_hrs[1] * 60 + +_hrs[2], _hb = +_hrs[3] * 60 + +_hrs[4]; if (_ha < _hb) { _a = _ha; _b = _hb; } }
    // v22: the same room at the nearest free time that day, as long as the window, 8 AM - 10 PM: the nearest before and the
    // nearest after, the nearer first (a tie: the earlier), back-to-back allowed. An event with no room blocks too (Book Session refuses it).
    const __nearest = (room, d0, ws, we) => {
      const D = we - ws; if (!(D > 0)) return [];
      const lo = d0 + 8 * _H, hi = d0 + 22 * _H;
      const blk = _evs.filter(ev => (ev.rooms.indexOf(room) !== -1 || !ev.rooms.length) && ev.s < hi && ev.e > lo);
      const c = new Set(); for (let t = lo; t + D <= hi; t += 30 * 60000) c.add(t);
      for (const b of blk) { c.add(b.e); c.add(b.s - D); }
      const ok = [...c].filter(t => t >= lo && t + D <= hi && t !== ws && blk.every(b => !(b.s < t + D && b.e > t)));
      const bf = ok.filter(t => t < ws).sort((x, y) => y - x)[0], af = ok.filter(t => t > ws).sort((x, y) => x - y)[0];
      return [bf, af].filter(t => t !== undefined).sort((x, y) => Math.abs(x - ws) - Math.abs(y - ws) || x - y)   // a tie: the earlier first
       
        .map(t => ({ start: new Date(t).toISOString(), end: new Date(t + D).toISOString() }));
    };
"""
RA_NEAR_OLD = "                title: ev.title, ref: ev.ref, allDay: ev.allDay })) } : { room: hit, status: 'FREE' }; });"
RA_NEAR_NEW = ("                title: ev.title, ref: ev.ref, allDay: ev.allDay })),\n"
               "              nearest: _hrs ? __nearest(hit, d0, ws, we) : undefined } : { room: hit, status: 'FREE' }; });   // v22")
RA_GAP1_OLD = "return __head(_ws) + '\\n\\n' + (d.free_rooms && d.free_rooms.length ? __layout(d.free_rooms).join('\\n') : '❌ Nothing free.'); }).join('\\n\\n');"
RA_GAP1_NEW = "return __head(_ws) + '\\n\\n' + (d.free_rooms && d.free_rooms.length ? __layout(d.free_rooms).join('\\n') : '❌ Nothing free.'); }).join('\\n\\n\\n');   // v22: a blank line more between days"
RA_GAP2_OLD = ".line).join('\\n'); }).join('\\n\\n');"
RA_GAP2_NEW = ".line).join('\\n'); }).join('\\n\\n\\n');   // v22"

def ra(w):
    w["name"] = "Jessie — Room Availability — v22 (nearest time + day spacing)"
    n = node(w, "Compute Availability")["parameters"]
    c = n["jsCode"]
    c = once(c, RA_HOURS_OLD, RA_HOURS_NEW, "RA hours")
    c = once(c, RA_NEAR_OLD, RA_NEAR_NEW, "RA nearest")
    c = once(c, RA_GAP1_OLD, RA_GAP1_NEW, "RA day gap (rooms)")
    c = once(c, RA_GAP2_OLD, RA_GAP2_NEW, "RA day gap (room asked)")
    n["jsCode"] = c
    trig = node(w, "When Executed by Another Workflow")["parameters"]["workflowInputs"]["values"]
    if not any(v.get("name") == "hours" for v in trig): trig.append({"name": "hours"})
    return w

# ----------------------------------------------------------------------------------------------------- Book Session v101
BS_QUERY_OLD = "if ((j.series_alt === true || String(j.series_alt).toLowerCase() === 'true') && String(j.mode || '').trim().toLowerCase() === 'prepare') {"
BS_QUERY_NEW = "if (String(j.mode || '').trim().toLowerCase() === 'prepare') {   // v101: every prepare (the nearest free time, PENDING 102)"

BS_SAMEDAY_ANCHOR = "  if (!__swap)\n  // v51: the final details ride along"
BS_SAMEDAY = r"""  // v101 (PENDING 102, asked 8 Oct): the same room at the nearest free time that day, as long as the one asked for, 8 AM -
  // 10 PM - the nearest before and the nearest after, the nearer first, back-to-back allowed. Prepare mode reads the whole
  // day (Get Events In Window), so only then. Every time stays bookable: this limits what is offered, not what is booked.
  let _sameDay = [];
  try {
    if (__prep && wanted.length === 1 && !allDay && reqEnd > reqStart) {
      const _D = reqEnd - reqStart, _day = new Date(reqStart + 8 * 3600000).toISOString().slice(0, 10);
      const _lo = Date.parse(_day + 'T08:00:00+08:00'), _hi = Date.parse(_day + 'T22:00:00+08:00');
      const _blk = EVENTS.filter(ev => ev && ev.id && ev.status !== 'cancelled' && !(exclude && ev.id === exclude))
        .map(ev => ({ s: evMs(ev.start && (ev.start.dateTime || ev.start.date)), e: evMs(ev.end && (ev.end.dateTime || ev.end.date)), r: roomsOf(ev) }))
        .filter(b => (!b.r.length || b.r.indexOf(wanted[0].name) !== -1) && b.s < _hi && b.e > _lo);
      const _c = new Set(); for (let t = _lo; t + _D <= _hi; t += 30 * 60000) _c.add(t);
      for (const b of _blk) { _c.add(b.e); _c.add(b.s - _D); }
      const _ok = [..._c].filter(t => t >= _lo && t + _D <= _hi && t !== reqStart && _blk.every(b => !(b.s < t + _D && b.e > t)));
      const _b4 = _ok.filter(t => t < reqStart).sort((x, y) => y - x)[0], _af = _ok.filter(t => t > reqStart).sort((x, y) => x - y)[0];
      const _iso2 = ms => new Date(ms + 8 * 3600000).toISOString().slice(0, 19) + '+08:00';
      _sameDay = [_b4, _af].filter(t => t !== undefined).sort((x, y) => Math.abs(x - reqStart) - Math.abs(y - reqStart) || x - y)   // a tie: the earlier first
       
        .map(t => ({ start: _iso2(t), end: _iso2(t + _D) }));
    }
  } catch (e) { _sameDay = []; }
"""
BS_RET_OLD = "    free_alternatives: _alts,\n"
BS_RET_NEW = "    free_alternatives: _alts, same_day_slots: _sameDay,   // v101\n"

BS_TITLE_ANCHOR = "// v51: the project segment of a studio title is in capitals (the title convention)"
BS_TITLE = r"""// v101 (QA round 3 B6, PENDING 106): a Management meeting in a conference room is titled by the meeting, not the department.
// "Book salin on monday with sir vic at 12pm-1pm" became "SALIN - Management", and the requester could not tell that
// "Management" was the department. With no meeting title, the colleague it is for names it ("SALIN - Vic Icasas"); with
// neither, prepare mode asks. A joint meeting ("KATHA - Mgmt x BD") keeps its departments.
let __needMeetingTitle = false;
try {
  let _R0 = {}; try { _R0 = JSON.parse(String(REQ.reference_data || '{}')); } catch (e) {}
  const _conf = (_R0.rooms || []).filter(r => r.common && !/lobby/i.test(String(r.name))).map(r => String(r.name).toLowerCase());
  const _cf = ['salin', 'katha', 'likha'].concat(_conf);
  const _mt = finalSummary.match(/^\s*([^-/]+?)\s+-\s+(.+?)\s*$/);
  if (_mt && _cf.indexOf(_mt[1].trim().toLowerCase()) !== -1) {
    const _sg = _mt[2].split(/\s+-\s+/).map(s => s.trim()).filter(Boolean);
    if (_sg.length && /^(?:management|mgmt|mgt)$/i.test(_sg[_sg.length - 1])) {
      _sg.pop();
      let _ttl = _sg.join(' - ');
      if (!_ttl && bookedFor) _ttl = bookedFor;
      if (_ttl) finalSummary = _mt[1].trim().toUpperCase() + ' - ' + _ttl;
      else __needMeetingTitle = true;
    }
  }
} catch (e) {}
if (__needMeetingTitle && __prep) {
  return [{ json: { verdict:'REJECTED', reason:'NEED_MEETING_TITLE',
    human:'Nothing was prepared. Ask exactly this, in one message: "What’s the meeting title?" Then prepare it again with the title "'
      + String(finalSummary).split(' - ')[0].trim().toUpperCase() + ' - <their meeting title>" (no department in it).' } }];
}
"""
BS_RR_OLD = "  free_alternatives: Array.isArray(v.free_alternatives) ? v.free_alternatives : null,   // v97: main writes the taken-room reply\n"
BS_RR_NEW = BS_RR_OLD + "  same_day_slots: Array.isArray(v.same_day_slots) ? v.same_day_slots : null,   // v101: the same room, nearest free time that day\n"

def book(w):
    w["name"] = "Jessie — Book Session — v101 (nearest time + meeting titles)"
    q = node(w, "Get Events In Window")["parameters"]["queryParameters"]["parameters"]
    for p in q:
        if p["name"] in ("timeMin", "timeMax"): p["value"] = once(p["value"], BS_QUERY_OLD, BS_QUERY_NEW, "query " + p["name"])
    cc = node(w, "Check Conflicts")["parameters"]
    c = cc["jsCode"]
    c = once(c, BS_SAMEDAY_ANCHOR, BS_SAMEDAY + BS_SAMEDAY_ANCHOR, "same-day slots")
    c = once(c, BS_RET_OLD, BS_RET_NEW, "return same_day_slots")
    c = once(c, BS_TITLE_ANCHOR, BS_TITLE + BS_TITLE_ANCHOR, "meeting title")
    cc["jsCode"] = c
    rr = node(w, "Return Rejection")["parameters"]
    rr["jsCode"] = once(rr["jsCode"], BS_RR_OLD, BS_RR_NEW, "Return Rejection")
    return w

# ---------------------------------------------------------------------------------------------------------- main v249
# Booked For: ranges with no am/pm, the newest range forces, the previous range (for the early check's "already told")
BF_TIMEISH_OLD = "  const TIMEISH = /"
BF_HM_ANCHOR = "  for (const t of mine) {\n    if (!TIMEISH.test(t)) continue;\n    const m = t.match(RANGE);\n    if (m && (m[3] || m[6])) {\n      let m1 = m[3], m2 = m[6];\n      if (!m2) m2 = m1;\n      let s = hm(m[1], m[2], m1 || m2), e = hm(m[4], m[5], m2);\n      if (!m1 && s && e && s >= e) s = hm(m[1], m[2], String(m2).toLowerCase().startsWith('p') ? 'am' : 'pm');   // \"11 to 1pm\"\n      if (s && e && s < e) { out.timeStart = s; out.timeEnd = e; out.timePhrase = m[0].trim(); }\n    } else {"
BF_RNG = r"""  // v249 (PENDING 103, live 8 Oct 23:38): "book 11-1 instead" was not read - a range needed am/pm on at least one side, so the
  // older "12-2pm" stood and the model mixed the two into 12-1. A range with neither is read by working hours: 8-11 is the
  // morning, 12 and 1-7 the afternoon, and the end is its first reading after the start ("11-1" 11 AM-1 PM, "2-5" 2-5 PM,
  // "9-12" 9 AM-12 PM). Never after a month, a room or a count ("oct 10-12", "studios 1-3", "eps 3-5"), never before a unit
  // ("1-2 hours", "2-3 people").
  const rng = m => {
    if (!m) return null;
    let s, e;
    if (m[3] || m[6]) {
      const m1 = m[3], m2 = m[6] || m[3];
      s = hm(m[1], m[2], m1 || m2); e = hm(m[4], m[5], m2);
      if (!m1 && s && e && s >= e) s = hm(m[1], m[2], String(m2).toLowerCase().startsWith('p') ? 'am' : 'pm');   // "11 to 1pm"
    } else {
      const inp = String(m.input || ''), at = m.index || 0, h1 = +m[1], h2 = +m[4];
      if (!(h1 >= 1 && h1 <= 12 && h2 >= 1 && h2 <= 12)) return null;
      if (/(?:\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?|\b(?:studios?|rooms?|booths?|m|ep|eps|episodes?|reels?|scenes?|ch|chapters?|parts?|takes?|pages?|days?|weeks?|lines?|no|nos|items?|spots?|tracks?|songs?)\.?|\b(?:on|from|between|of) the|[#/])\s*$/i.test(inp.slice(0, at))) return null;
      if (/^\s*(?:hours?|hrs?|h\b|mins?|minutes|days?|weeks?|months?|people|pax|persons?|takes?|eps?|episodes?|spots?|tracks?|songs?|%|[\/.-]\d|(?:of\s+)?(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b|(?:st|nd|rd|th)\b)/i.test(inp.slice(at + m[0].length))) return null;
      s = hm(m[1], m[2], h1 >= 8 && h1 <= 11 ? 'am' : 'pm');
      e = hm(m[4], m[5], 'am');
      if (s && e && e <= s) e = hm(m[4], m[5], 'pm');
      if (s && e && (+e.slice(0, 2) * 60 + +e.slice(3)) - (+s.slice(0, 2) * 60 + +s.slice(3)) > 14 * 60) return null;
    }
    return s && e && s < e ? [s, e] : null;
  };
  const allRanges = t => { const re = new RegExp(RANGE.source, 'gi'), r = []; let m; while ((m = re.exec(String(t || '')))) { const x = rng(m); if (x) r.push({ s: x[0], e: x[1], txt: m[0].trim() }); } return r; };
  const timeish = t => TIMEISH.test(t) || allRanges(t).length > 0;
"""
BF_LOOP_NEW = r"""  for (const t of mine) {
    if (!timeish(t)) continue;
    const _rs = allRanges(t);
    if (_rs.length) {
      out.timeStart = _rs[0].s; out.timeEnd = _rs[0].e; out.timePhrase = _rs[0].txt;
      // v249: the newest message's own range is the time (one range only - two can be two bookings)
      if (t === mine[0] && _rs.length === 1) out.timeForced = true;
      out.timeInNewest = (t === mine[0]);
      for (const o of mine.slice(mine.indexOf(t) + 1)) { const _p = allRanges(o); if (_p.length) { out.prevTimeStart = _p[0].s; out.prevTimeEnd = _p[0].e; break; } }
    } else {"""
BF_PREV_OLD = """          const r = o.match(RANGE);
          if (r && (r[3] || r[6])) { let a = hm(r[1], r[2], r[3] || r[6]), b = hm(r[4], r[5], r[6] || r[3]);
            if (!r[3] && a && b && a >= b) a = hm(r[1], r[2], String(r[6]).toLowerCase().startsWith('p') ? 'am' : 'pm');
            if (a && b && a < b) { ps = a; pe = b; } break; }"""
BF_PREV_NEW = """          const _r = allRanges(o);   // v249: no am/pm read by working hours
          if (_r.length) { ps = _r[0].s; pe = _r[0].e; break; }"""
BF_FORCED_OLD = "            out.timeChange = true; out.timeForced = (t === mine[0]);\n"
BF_FORCED_NEW = "            out.timeChange = true; out.timeForced = (t === mine[0]); out.timeInNewest = (t === mine[0]); out.prevTimeStart = ps; out.prevTimeEnd = pe;   // v249\n"
BF_IDX_OLD = "  const __rangeIdx = out.timeStart ? mine.findIndex(t => TIMEISH.test(t)) : -1;"
BF_IDX_NEW = "  const __rangeIdx = out.timeStart ? mine.findIndex(t => timeish(t)) : -1;   // v249"
BF_MENT_OLD = """  { const re = new RegExp(RANGE.source, 'gi'); let m; while ((m = re.exec(allText))) { if (m[3] || m[6]) { let a = hm(m[1], m[2], m[3] || m[6]); const b = hm(m[4], m[5], m[6] || m[3]);
      if (!m[3] && a && b && a >= b) a = hm(m[1], m[2], String(m[6]).toLowerCase().startsWith('p') ? 'am' : 'pm');
      if (a) mentioned.add(a); } } }"""
BF_MENT_NEW = """  for (const _r of allRanges(allText)) { mentioned.add(_r.s); mentioned.add(_r.e); }   // v249: no am/pm too"""
BF_JB_OLD = "          const _tmsg = mine.find(x => /\\b\\d{1,2}(?::\\d{2})?\\s*(?:am|pm|a\\.m\\.|p\\.m\\.|nn|noon)\\b/i.test(x)) || '';"
BF_JB_NEW = "          const _tmsg = mine.find(x => /\\b\\d{1,2}(?::\\d{2})?\\s*(?:am|pm|a\\.m\\.|p\\.m\\.|nn|noon)\\b/i.test(x) || allRanges(x).length) || '';   // v249: \"11-1\" too"
BF_JB2_OLD = """          { const _rg = _tmsg.match(RANGE);
            if (_rg && (_rg[3] || _rg[6])) {
              const m1 = _rg[3], m2 = _rg[6] || _rg[3];
              let s = hm(_rg[1], _rg[2], m1 || m2); const e = hm(_rg[4], _rg[5], m2);
              if (!m1 && s && e && s >= e) s = hm(_rg[1], _rg[2], String(m2).toLowerCase().startsWith('p') ? 'am' : 'pm');
              if (s && e && s < e) { ns = s; ne = e; }
            } }"""
BF_JB2_NEW = """          { const _rg = allRanges(_tmsg); if (_rg.length) { ns = _rg[0].s; ne = _rg[0].e; } }   // v249: no am/pm read by working hours"""

# Early Room Plan
EP_LOOP_OLD = """    if (isBot(m)) {
      if (/^\\s*\\*?(?:booked\\b|done\\s*-|moved\\b|cancell?ed\\b)|has been booked/i.test(x)) break;
      botTexts.push(x); if (!found) roomsIn(x).forEach(r => botRooms.add(r)); continue;
    }"""
EP_LOOP_NEW = """    if (isBot(m)) {
      if (/^\\s*\\*?(?:booked\\b|done\\s*-|moved\\b|cancell?ed\\b)|has been booked/i.test(x)) break;
      botTexts.push(x);
      // v249 (PENDING 103): a heads-up about the requester's room offers other rooms, but a reply with only a new time
      // ("book 11-1 instead") is still about that room - its rooms count only if the requester's room is another one
      const _hu = x.match(/^❌ Heads up: \\*(?:You already have (.+?) booked |(.+?) is already booked )/);
      if (!found) { if (_hu) { huRoom = huRoom || (_hu[1] || _hu[2]); roomsIn(x).forEach(r => huRooms.add(r)); } else roomsIn(x).forEach(r => botRooms.add(r)); }
      continue;
    }"""
EP_DECL_OLD = "  const botRooms = new Set(), botTexts = []; let n = 0, carried = '', found = false;"
EP_DECL_NEW = "  const botRooms = new Set(), botTexts = [], huRooms = new Set(); let n = 0, carried = '', found = false, huRoom = '';   // v249: huRoom/huRooms"
EP_CARRY_OLD = "    if (!found && r.length) { found = true; if (r.length === 1 && ![...botRooms].some(b => b !== r[0])) carried = r[0]; }"
EP_CARRY_NEW = ("    if (!found && r.length) { found = true; if (r.length === 1 && ![...botRooms].some(b => b !== r[0])\n"
                "        && !(huRoom && huRoom !== r[0] && [...huRooms].some(b => b !== r[0]))) carried = r[0]; }")
EP_SAID_OLD = "  const saidTime = /\\b\\d{1,2}(?::\\d{2})?\\s*(?:am|pm|a\\.m\\.|p\\.m\\.|nn)\\b|\\bnoon\\b/i.test(t);"
EP_SAID_NEW = (EP_SAID_OLD + "\n"
  "  // v249 (PENDING 103): a time read from this message (\"11-1\", \"3pm instead\") that is not the one asked for before\n"
  "  const newTime = !!bf.timeInNewest && !!bf.timeStart && (bf.timeStart !== bf.prevTimeStart || bf.timeEnd !== bf.prevTimeEnd);")
EP_ELSE_OLD = "  else if (saidDate || saidTime) { room = carried; if (!room) skip('no room for this booking'); }"
EP_ELSE_NEW = "  else if (saidDate || saidTime || newTime) { room = carried; if (!room) skip('no room for this booking'); }   // v249: newTime"
EP_TOLD_OLD = "    if (botTexts.some(x => told.test(x) || (told2.test(x) && _offer.test(x)))) { room = ''; skip('already told this booking'); }"
EP_TOLD_NEW = ("    // v249: a new time is checked again (\"book 11-1 instead\"); the same request again goes on to the normal flow\n"
               "    if (!newTime && botTexts.some(x => told.test(x) || (told2.test(x) && _offer.test(x)))) { room = ''; skip('already told this booking'); }")
EP_PLAN_OLD = """    Object.assign(plan, { run: true, room, date, timed, timeStart: timed ? ts0 : '', timeEnd: timed ? te0 : '', sessionType: st,
      start_iso: date + 'T' + (timed ? ts0 : '08:00') + ':00+08:00', end_iso: last + 'T' + (timed ? te0 : '22:00') + ':00+08:00' });"""
EP_PLAN_NEW = """    // v249 (PENDING 102): with a time, read 8 AM - 10 PM (or wider) every day and pass the hours, so Room Availability can
    // give the nearest free time that day
    Object.assign(plan, { run: true, room, date, timed, timeStart: timed ? ts0 : '', timeEnd: timed ? te0 : '', sessionType: st,
      start_iso: date + 'T' + (timed && ts0 < '08:00' ? ts0 : '08:00') + ':00+08:00', end_iso: last + 'T' + (timed && te0 > '22:00' ? te0 : '22:00') + ':00+08:00',
      hours: timed ? ts0 + '-' + te0 : '' });"""
EP_KNOWN_OLD = "} catch (e) { plan.run = false; plan.why = 'error: ' + ((e && e.message) || e); }\nitem.earlyPlan = plan;"
EP_KNOWN_NEW = """  // v249 (PENDING 103): the room this booking is for, for the details question to restate (not on a cancel, move or yes)
  if (!/^(?:a yes|answering a cancel or move card|a cancel or move)$/.test(plan.why)) plan.knownRoom = now.length === 1 ? now[0] : carried;
} catch (e) { plan.run = false; plan.why = 'error: ' + ((e && e.message) || e); }
item.earlyPlan = plan;"""

# Early Room Result: the nearest same-day time first, other days one (two when there is no same-day time)
ER_DAYS_OLD = "      const days = r.days.filter(d => d !== d0 && ((d.rooms || []).find(x => x.room === P.room) || {}).status === 'FREE').slice(0, 3).map(d => d.label);"
ER_DAYS_NEW = """      // v249 (PENDING 102): the same room at the nearest free time that day (Room Availability v22), then other rooms, then
      // other days - one when there is a same-day time, else two (was three)
      const near = P.timed ? [].concat(a0.nearest || []).filter(x => x && x.start && x.end) : [];
      const days = r.days.filter(d => d !== d0 && ((d.rooms || []).find(x => x.room === P.room) || {}).status === 'FREE').slice(0, near.length ? 1 : 2).map(d => d.label);"""
ER_OPTS_OLD = "        const opts = [];\n        if (alts.length) opts.push("
ER_OPTS_NEW = ("        const opts = [];\n"
               "        if (near.length) opts.push('✅ ' + P.room + ' is free on the same day at:\\n' + near.map(x => '• ' + hm(x.start) + ' – ' + hm(x.end)).join('\\n'));   // v249\n"
               "        if (alts.length) opts.push(")

# Guard Probe
GP_ROOMOCC_OLD = """        const _alts = [].concat(_oT.free_alternatives || []).filter(Boolean);
        text = _heads.join('\\n') + '\\n\\n' + (_own ? 'Want to move that booking to this time instead?'
          : (_alts.length ? '✅ Free at that time:\\n' + _alts.join(' · ') + '\\n\\nWant one of those, or another day or time?' : 'Nothing like it is free then. What other day or time works?'));"""
GP_ROOMOCC_NEW = """        const _alts = [].concat(_oT.free_alternatives || []).filter(Boolean);
        // v249 (PENDING 102): the same room at the nearest free time that day first (Book Session v101), then other rooms
        const _sd = [].concat(_oT.same_day_slots || []).filter(x => x && x.start && x.end), _rmT = Object.keys(_by), _blT = [];
        if (_sd.length && _rmT.length === 1) _blT.push('✅ ' + _rmT[0] + ' is free on the same day at:\\n' + _sd.map(x => '• ' + _hmT(x.start) + ' – ' + _hmT(x.end)).join('\\n'));
        if (_alts.length) _blT.push('✅ Free at that time:\\n' + _alts.join(' · '));
        text = _heads.join('\\n') + '\\n\\n' + (_own ? 'Want to move that booking to this time instead?'
          : (_blT.length ? _blT.join('\\n\\n') + '\\n\\nWant one of those, or another day or time?' : 'Nothing like it is free then. What other day or time works?'));"""
GP_V246_OLD = "    if (_oR && _oR.status === 'OK' && _oR.reply_text && !_prepared && !/\\*Date:\\*|\\*Dates|\\*Moving to:\\*|Book it\\?|Cancel it\\?|Move it\\?|Confirm to/i.test(text)) {"
GP_V246_NEW = """    // v249 (PENDING 103, live 8 Oct 23:38): only for an availability question, or a reply that asks nothing - "book 11-1
    // instead" was answered with the availability layout because the model had checked the room on a booking turn
    const _trA = String((($('Slack Trigger').first() || {}).json || {}).text || '').replace(/\\*sent using\\*[\\s\\S]*$/i, '').trim();
    const _avA = /\\b(?:free|available|availability|vacant|open|taken|booked|occupied|busy)\\b/i.test(_trA)
      || (!/\\b(?:book|rebook|reserve)\\b|\\binstead\\b/i.test(_trA) && (/\\?\\s*$/.test(_trA) || /^\\s*(?:is|are|any|which|what|when|check|how about)\\b/i.test(_trA)));
    if (_oR && _oR.status === 'OK' && _oR.reply_text && !_prepared && (_avA || !/\\?/.test(text)) && !/\\*Date:\\*|\\*Dates|\\*Moving to:\\*|Book it\\?|Cancel it\\?|Move it\\?|Confirm to/i.test(text)) {"""
GP_FREE_OLD = """    if (/\\?\\s*$/.test(text) && text.length <= 400
        && !/department|booking type|arranger|internal|external|personal|likha|katha|salin|\\(|\\bfree\\b|\\btaken\\b|\\bbooked\\b|\\d{1,2}(?::\\d{2})?\\s*(?:am|pm)\\b/i.test(text)) {"""
GP_FREE_NEW = """    // v249 (PENDING 103): "Studio 7 is free then." before the details question, when the early room check found that room
    // free this turn - said by code instead, in the line that restates the booking
    let _freeSaid = '';
    try {
      const _er2 = (($('Early Room Result').first() || {}).json || {}).earlyRoom, _pl2 = (((($('Early Room Plan').first() || {}).json) || {}).earlyPlan) || {};
      if (_er2 && _er2.mode === 'free' && _pl2.room) {
        const _reF = new RegExp('^' + String(_pl2.room).replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + ' is (?:free|available|open)(?: (?:then|at that time|that day|for that time|on [^.?!\\n]+|from [^.?!\\n]+))?[.!]\\\\s+(?=[^\\\\n]*\\\\?\\\\s*$)', 'i');
        if (_reF.test(text)) { text = text.replace(_reF, ''); _freeSaid = String(_pl2.room); }
      }
    } catch (e) {}
""" + GP_FREE_OLD
GP_FREE2_OLD = """    }
  }
} catch (e) {}

// --- v238 (card guard)"""
GP_FREE2_NEW = """    }
    if (_freeSaid && !/^✅/.test(text)) text = '✅ ' + _freeSaid + ' is free\\n' + text;   // v249: not rewritten - still said by code
  }
} catch (e) {}

// --- v238 (card guard)"""
GP_DET_OLD = """      if (_it.length >= 2) {
        const _j = _it.length === 2 ? _it.join(' and ') : _it.slice(0, -1).join(', ') + ' and ' + _it[_it.length - 1];
        text = "What's the " + _j + '?' + (_it.indexOf('client') !== -1 ? ' (or "none" for no client)' : '');
      }"""
GP_DET_NEW = """      // v249: the fixed shape itself ("What's the date, time, ...", v247's own words, or the model copying them) is read too
      if (/\\bthe date\\b|\\bdate(?:,| and)/i.test(text)) _it.push('date');
      if (/\\bthe time\\b|\\b(?:date|day)(?:,| and) time\\b|\\btime(?:,| and) /i.test(text)) _it.push('time');
      if (/\\blength\\b|\\bduration\\b/i.test(text)) _it.push('length');
      { const _O = ['date', 'time', 'length', 'room', 'session type', 'project', 'client', 'engineer'];
        const _u = [...new Set(_it)].sort((a, b) => _O.indexOf(a) - _O.indexOf(b)); _it.length = 0; _u.forEach(x => _it.push(x)); }
      // v249 (PENDING 105): never "time" and "length" together - a time range gives the length
      if (_it.indexOf('time') !== -1 && _it.indexOf('length') !== -1) _it.splice(_it.indexOf('length'), 1);
      // v249 (PENDING 103): what is already known is said back first - the room (Early Room Plan), the date (Gate Context)
      // and the time (Booked For), each from the requester's own words - and not asked again
      const _kn = { room: '', date: '', time: '' };
      if (_it.length >= 2) {
        try { _kn.room = String(((($('Early Room Plan').first() || {}).json || {}).earlyPlan || {}).knownRoom || ''); } catch (e) {}
        try { const _ds = String((($('Gate Context').first() || {}).json || {}).datesUnderDiscussion || '').split(',').map(x => x.trim()).filter(x => /^\\d{4}-\\d{2}-\\d{2}$/.test(x));
          // the date only when the model did not ask for it, or it was named in this message - a date carried from earlier
          // today may belong to another booking
          const _dm = String((($('Gate Context').first() || {}).json || {}).datesInMessage || '').split(',').map(x => x.trim()).filter(Boolean);
          if (_ds.length === 1 && (_it.indexOf('date') === -1 || _dm.indexOf(_ds[0]) !== -1)) _kn.date = new Date(_ds[0] + 'T12:00:00+08:00').toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' }); } catch (e) {}
        try { const _bk = (($('Booked For').first() || {}).json) || {}, _f12 = x => (+x.slice(0, 2) % 12 || 12) + ':' + x.slice(3) + ' ' + (+x.slice(0, 2) < 12 ? 'AM' : 'PM');
          if (/^\\d{2}:\\d{2}$/.test(String(_bk.timeStart || '')) && /^\\d{2}:\\d{2}$/.test(String(_bk.timeEnd || ''))) _kn.time = _f12(_bk.timeStart) + ' – ' + _f12(_bk.timeEnd); } catch (e) {}
      }
      const _left = _it.filter(x => !((x === 'room' && _kn.room) || (x === 'date' && _kn.date) || ((x === 'time' || x === 'length') && _kn.time)));
      if (_it.length >= 2 && _left.length) {
        const _j = _left.length === 1 ? _left[0] : _left.length === 2 ? _left.join(' and ') : _left.slice(0, -1).join(', ') + ' and ' + _left[_left.length - 1];
        const _pre = [_kn.room && _freeSaid === _kn.room ? '✅ ' + _kn.room + ' is free' : _kn.room, _kn.date, _kn.time].filter(Boolean).join(' · ');
        text = (_pre ? _pre + '\\n' : '') + "What's the " + _j + '?' + (_left.indexOf('client') !== -1 ? ' (or "none" for no client)' : '');
      }"""

# The prompt: Management meetings (106) and ranges with no am/pm (103)
PR_CONF_OLD = "Title: `KATHA - <Meeting Title> - Marketing x BD`, or `KATHA - Marketing x BD` without a meeting title. Join departments with \" x \"."
PR_CONF_NEW = (PR_CONF_OLD + " A meeting of Management alone has no department segment: `SALIN - <Meeting Title>`, or the name of the "
               "colleague it is for when there is no title; with neither, Prepare Booking asks.")
PR_DEPT_OLD = "Management → Mgmt"
PR_DEPT_NEW = "Management → Mgmt (only with another department)"

def main(w):
    w["name"] = "Project Jessie — v249 (taken-room options + time ranges)"
    bf = node(w, "Booked For")["parameters"]
    c = bf["jsCode"]
    c = once(c, BF_HM_ANCHOR, BF_RNG + BF_LOOP_NEW, "Booked For range loop")
    c = once(c, BF_PREV_OLD, BF_PREV_NEW, "Booked For previous range")
    c = once(c, BF_FORCED_OLD, BF_FORCED_NEW, "Booked For forced")
    c = once(c, BF_IDX_OLD, BF_IDX_NEW, "Booked For range index")
    c = once(c, BF_MENT_OLD, BF_MENT_NEW, "Booked For mentioned")
    c = once(c, BF_JB_OLD, BF_JB_NEW, "Booked For just-booked message")
    c = once(c, BF_JB2_OLD, BF_JB2_NEW, "Booked For just-booked range")
    bf["jsCode"] = c
    ep = node(w, "Early Room Plan")["parameters"]
    c = ep["jsCode"]
    for old, new, what in [(EP_DECL_OLD, EP_DECL_NEW, "plan decl"), (EP_LOOP_OLD, EP_LOOP_NEW, "plan loop"), (EP_CARRY_OLD, EP_CARRY_NEW, "plan carry"),
                           (EP_SAID_OLD, EP_SAID_NEW, "plan newTime"), (EP_ELSE_OLD, EP_ELSE_NEW, "plan else"), (EP_TOLD_OLD, EP_TOLD_NEW, "plan told"),
                           (EP_PLAN_OLD, EP_PLAN_NEW, "plan window"), (EP_KNOWN_OLD, EP_KNOWN_NEW, "plan knownRoom")]:
        c = once(c, old, new, what)
    ep["jsCode"] = c
    er = node(w, "Early Room Result")["parameters"]
    c = er["jsCode"]
    c = once(c, ER_DAYS_OLD, ER_DAYS_NEW, "result days")
    c = once(c, ER_OPTS_OLD, ER_OPTS_NEW, "result options")
    er["jsCode"] = c
    chk = node(w, "Early Room Check")["parameters"]["workflowInputs"]
    if not any(s["id"] == "hours" for s in chk["schema"]):
        chk["schema"].append({"canBeUsedToMatch": True, "defaultMatch": False, "display": True, "displayName": "hours", "id": "hours", "required": False, "type": "string"})
    chk["value"]["hours"] = "={{ $json.earlyPlan.hours || '' }}"
    gp = node(w, "Guard Probe")["parameters"]
    c = gp["jsCode"]
    c = once(c, GP_ROOMOCC_OLD, GP_ROOMOCC_NEW, "Guard Probe ROOM_OCCUPIED")
    c = once(c, GP_V246_OLD, GP_V246_NEW, "Guard Probe v246")
    c = once(c, GP_FREE_OLD, GP_FREE_NEW, "Guard Probe free statement")
    c = once(c, GP_DET_OLD, GP_DET_NEW, "Guard Probe details")
    c = once(c, GP_FREE2_OLD, GP_FREE2_NEW, "Guard Probe free fallback")
    gp["jsCode"] = c
    ag = next(x for x in w["nodes"] if x["type"].endswith(".agent"))
    sm = ag["parameters"]["options"]["systemMessage"]
    sm = once(sm, PR_CONF_OLD, PR_CONF_NEW, "prompt conference title")
    sm = once(sm, PR_DEPT_OLD, PR_DEPT_NEW, "prompt Mgmt")
    ag["parameters"]["options"]["systemMessage"] = sm
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 6: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(book(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
    json.dump(ra(json.load(open(a[4]))), open(a[5], "w"), indent=2, ensure_ascii=False); print("wrote", a[5])
