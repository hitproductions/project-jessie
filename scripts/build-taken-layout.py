#!/usr/bin/env python3
"""main v235 + Book Session v97 + Book Series v7 (taken-room layout) - asked 7 Oct (PENDING 95): every message that says a room
is taken uses the heads-up layout of v234 - ❌ and the room + time in bold, the session after "by this session:", then ✅
blocks for what is free, one item per line where it is a list of times or days:

    ❌ Heads up: *Studio 7 is already booked 3:00 PM – 5:00 PM* on Friday, October 8 by this session: WHEAT SUN / Jem Lim / AEG

    ✅ Free at that time:
    Studio 8 · Studio F · Studio C · Studio 4 · Studio 5

    ✅ Studio 7 is free at that time on:
    • Sunday, October 10

    Want one of those, or another day or time?

  main v235:
    - Early Room Result, the reply for a requested time (or a whole day) that is taken: the layout above (was two plain lines).
    - Guard Probe writes the reply to Book Session's ROOM_OCCUPIED itself (was the model's wording of "Studio 7 is taken by
      ... - offer those"): the ❌ line per room, "✅ Free at that time:" from Book Session's free_alternatives, and "Want one of
      those, or another day or time?"; the requester's own booking: "❌ Heads up: *You already have ...* with this session:
      X" and "Want to move that booking to this time instead?". A move into a taken time (Move Booking before the yes, and
      Move Direct at the yes): "❌ Heads up: *That time is already booked* by this session: X" + "The booking stays where
      it is. Want a different time or room?".
    - Early Room Plan: "said once" knows the new layout (and the old one).
  Book Session v97:
    - Return Rejection passes free_alternatives and own_booking on (the agent saw only the conflicts).
    - The heads-up on a question (v88) in the layout: "❌ Heads up: *Studio F is already booked 1:00 PM – 4:00 PM* on
      Thursday, October 14 by this session: TITLE", a blank line, then the question.
    - The priority card's note: "❌ *Studio 7 is already booked then* by this session: TITLE" and the outrank line under it;
      an M booth hold the same way.
  Book Series v7: "❌ Heads up: *Studio 7 is already booked on Friday, 15 October 2027* - no other usual room or time that
    day is free, so that date is left out."; every date taken: "❌ *Studio 7 is already booked on all of those dates.*" and
    "Another room or time?"; a replaced date "(Studio 1 is already booked)".
  scripts/build-taken-layout.py <main-v234> <main-out> <book-v96> <book-out> <series-v6> <series-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# ================================================================ main
ER_OLD = """        const head = (own ? 'You already have ' + P.room + ' booked on ' : P.room + ' is already booked on ') + d0.label + ', ' + desc + '.';
        const opts = [];
        if (alts.length) opts.push((P.timed ? 'Free at that time: ' : 'Free that day: ') + alts.join(' · '));
        if (days.length) opts.push(P.room + ' is free ' + (P.timed ? 'at that time ' : '') + 'on ' + days.join(' · '));
        const text = head + '\\n\\n' + (opts.length ? opts.join('\\n') + '\\n\\nWant one of those, or another day or time?'
          : 'Nothing like it is free then, and ' + P.room + ' is taken at that time all week. What other day or time works?');
        early = { mode: 'replace', text, own, room: P.room };
        notice = 'ROOM CHECK (done by code this turn - do not call Room Availability for it): ' + head + ' Your whole reply this turn is '
          + 'exactly this, and nothing else - do not ask for any other details yet:\\n' + text;"""
ER_NEW = """        // v235 (asked 7 Oct): the heads-up layout - ❌ the room and time in bold, then ✅ blocks
        const _tm = evs.map(e => e.allDay ? 'all day' : hm(e.start) + ' – ' + hm(e.end)).join(' and ');
        const head = '❌ Heads up: *' + (own ? 'You already have ' + P.room + ' booked ' : P.room + ' is already booked ') + _tm + '* on ' + d0.label
          + (own ? ' with ' : ' by ') + (evs.length > 1 ? 'these sessions: ' : 'this session: ') + evs.map(e => e.title).join(' · ');
        const opts = [];
        if (alts.length) opts.push((P.timed ? '✅ Free at that time:' : '✅ Free all day:') + '\\n' + alts.join(' · '));
        if (days.length) opts.push('✅ ' + P.room + (P.timed ? ' is free at that time on:' : ' is free all day on:') + '\\n' + days.map(d => '• ' + d).join('\\n'));
        const text = head + '\\n\\n' + (opts.length ? opts.join('\\n\\n') + '\\n\\nWant one of those, or another day or time?'
          : 'Nothing like it is free then, and ' + P.room + ' is booked at that time all week. What other day or time works?');
        early = { mode: 'replace', text, own, room: P.room };
        notice = 'ROOM CHECK (done by code this turn - do not call Room Availability for it): ' + head.replace(/^❌ Heads up: /, '').replace(/\\*/g, '')
          + '. Your whole reply this turn is exactly this, and nothing else - do not ask for any other details yet:\\n' + text;"""

PL_OLD = """    const told = new RegExp('^(?:you already have ' + esc(room) + ' booked|' + esc(room) + ' is already booked) on ' + esc(lbl) + '\\\\b', 'i');
    if (botTexts.some(x => told.test(x))) { room = ''; skip('already told this booking'); }"""
PL_NEW = """    const told = new RegExp('^(?:you already have ' + esc(room) + ' booked|' + esc(room) + ' is already booked) on ' + esc(lbl) + '\\\\b', 'i');
    // v235: the ❌ layout - a reply that offered other rooms or days (a heads-up on a question is not "told")
    const told2 = new RegExp('^❌ Heads up: \\\\*(?:you already have ' + esc(room) + ' booked|' + esc(room) + ' is already booked) [^*\\\\n]*\\\\* on ' + esc(lbl) + '\\\\b', 'i');
    const _offer = /(?:Want one of those, or another day or time\\?|What other day or time works\\?|Want to move that booking to this time instead\\?)\\s*$/;
    if (botTexts.some(x => told.test(x) || (told2.test(x) && _offer.test(x)))) { room = ''; skip('already told this booking'); }"""

GP_ANCHOR = "// v230 (QA B4, 7 Oct): the early room check."
GP_BLOCK = r"""// v235 (asked 7 Oct): a room taken at the time asked for is said in the heads-up layout, by code - Book Session's
// ROOM_OCCUPIED (its conflicts, free_alternatives and own_booking) and Move Booking's. The model used to word these itself.
try {
  const _sT = (($input.first().json || {}).intermediateSteps) || [];
  for (let i = _sT.length - 1; i >= 0; i--) {
    const _tT = String(((_sT[i] || {}).action || {}).tool || '').replace(/[_\s]+/g, ' ').toLowerCase();
    if (!/^(prepare booking|book session|move booking)$/.test(_tT)) continue;
    let _oT = null; try { _oT = [].concat(JSON.parse(String((_sT[i] || {}).observation || '')))[0]; } catch (e) {}
    if (_oT && (_oT.status || _oT.verdict) === 'REJECTED' && _oT.reason === 'ROOM_OCCUPIED' && !_prepared) {
      const _hmT = x => new Date(x).toLocaleTimeString('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' });
      const _dayT = x => new Date(/^\d{4}-\d{2}-\d{2}$/.test(String(x)) ? x + 'T12:00:00+08:00' : x).toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' });
      const _allT = c => /^\d{4}-\d{2}-\d{2}$/.test(String(c.start || '')) || (/T00:00/.test(String(c.start || '')) && /T00:00/.test(String(c.end || '')));
      if (_tT === 'move booking') {
        const _ti = (String(_oT.human || '').match(/by "(.+?)"\. The original/) || [])[1] || '';
        text = '❌ Heads up: *That time is already booked*' + (_ti ? ' by ' + (/", "/.test(_ti) ? 'these sessions: ' + _ti.split('", "').join(' · ') : 'this session: ' + _ti) : '')
          + '\n\nThe booking stays where it is. Want a different time or room?';
      } else if (Array.isArray(_oT.conflicts) && _oT.conflicts.length) {
        const _own = _oT.own_booking === true, _by = {};
        for (const c of _oT.conflicts) (_by[c.room] = _by[c.room] || []).push(c);
        const _heads = Object.keys(_by).map(r => { const cs = _by[r];
          return '❌ Heads up: *' + (_own ? 'You already have ' + r + ' booked ' : r + ' is already booked ') + cs.map(c => _allT(c) ? 'all day' : _hmT(c.start) + ' – ' + _hmT(c.end)).join(' and ')
            + '* on ' + _dayT(cs[0].start) + (_own ? ' with ' : ' by ') + (cs.length > 1 ? 'these sessions: ' : 'this session: ') + cs.map(c => c.summary).join(' · '); });
        const _alts = [].concat(_oT.free_alternatives || []).filter(Boolean);
        text = _heads.join('\n') + '\n\n' + (_own ? 'Want to move that booking to this time instead?'
          : (_alts.length ? '✅ Free at that time:\n' + _alts.join(' · ') + '\n\nWant one of those, or another day or time?' : 'Nothing like it is free then. What other day or time works?'));
      }
    }
    break;
  }
} catch (e) {}

"""

MD_OLD = """  ROOM_OCCUPIED: "That time is taken now, so nothing was moved. Want a different time or room?","""
MD_NEW = """  ROOM_OCCUPIED: "❌ Heads up: *That time is already booked now*\\n\\nThe booking stays where it is. Want a different time or room?",   // v235: the heads-up layout"""

def main(w):
    w["name"] = "Project Jessie — v235 (taken-room layout)"
    r = node(w, "Early Room Result")["parameters"]; r["jsCode"] = sub1(r["jsCode"], ER_OLD, ER_NEW, "early replace")
    p = node(w, "Early Room Plan")["parameters"]; p["jsCode"] = sub1(p["jsCode"], PL_OLD, PL_NEW, "told")
    g = node(w, "Guard Probe")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GP_ANCHOR, GP_BLOCK + GP_ANCHOR, "gp")
    m = node(w, "Move Direct Reply")["parameters"]; m["jsCode"] = sub1(m["jsCode"], MD_OLD, MD_NEW, "move direct")
    return w

# ================================================================ Book Session
RR_OLD = """  unverifiable: v.unverifiable || null,"""
RR_NEW = """  unverifiable: v.unverifiable || null,
  free_alternatives: Array.isArray(v.free_alternatives) ? v.free_alternatives : null,   // v97: main writes the taken-room reply
  own_booking: v.own_booking === true,"""
BUSY_OLD = """            _busy = 'Heads up: ' + _h.k + ' is booked ' + (_h.all ? 'all day' : _t(_h.a) + ' – ' + _t(_h.b)) + ' (\\\\"' + _h.s.replace(/"/g, '') + '\\\\").';"""
BUSY_NEW = """            // v97 (asked 7 Oct): the heads-up layout, then a blank line before the question
            const _dl = new Date(_h.a + (_h.all ? 12 * 3600000 : 0)).toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' });
            _busy = '❌ Heads up: *' + _h.k + ' is already booked ' + (_h.all ? 'all day' : _t(_h.a) + ' – ' + _t(_h.b)) + '* on ' + _dl + ' by this session: ' + _h.s.replace(/"/g, '') + '\\n\\n';"""
BUSYUSE_OLD = """      __j.human = String(__j.human).replace(/(Ask exactly this[^"]*")/, (m, a) => a + _busy + ' ');   // v88"""
BUSYUSE_NEW = """      __j.human = String(__j.human).replace(/(Ask exactly this[^"]*")/, (m, a) => a + _busy);   // v88; v97: _busy ends in a blank line"""
ASKED_OLD = """!/Heads up: \\S.* is booked/.test(String(_R.asked_text || ''))"""
ASKED_NEW = """!/Heads up: \\*?\\S.*\\bbooked\\b/.test(String(_R.asked_text || ''))"""
NOTE_OLD = """    ? (o.room + ' has a standing hold (' + (o.incumbentTitle || o.approverName || 'the holder') + '). If you confirm, I will ask ' + (o.approverName || 'the holder') + ' to release it for this session, and book it once they agree.')
    : (o.room + ' is already booked then (' + (o.incumbentTitle || 'another session') + '). Your session outranks it, so if you confirm I will ask them to move, and book it once they do.'));"""
NOTE_NEW = """    // v97 (asked 7 Oct): the heads-up layout
    ? ('❌ *' + o.room + ' is already booked then* by this session: ' + (o.incumbentTitle || o.approverName || 'a standing hold') + '\\nIt is a standing hold - if you confirm, I will ask ' + (o.approverName || 'the holder') + ' to release it for this session, and book it once they agree.')
    : ('❌ *' + o.room + ' is already booked then* by this session: ' + (o.incumbentTitle || 'another session') + '\\nYour session outranks it, so if you confirm I will ask them to move, and book it once they do.'));"""

def book(w):
    w["name"] = "Jessie — Book Session — v97 (taken-room layout)"
    rr = node(w, "Return Rejection")["parameters"]; rr["jsCode"] = sub1(rr["jsCode"], RR_OLD, RR_NEW, "return rejection")
    cc = node(w, "Check Conflicts")["parameters"]; s = cc["jsCode"]
    s = sub1(s, BUSY_OLD, BUSY_NEW, "busy"); s = sub1(s, BUSYUSE_OLD, BUSYUSE_NEW, "busy use")
    if s.count(ASKED_OLD) < 1: raise SystemExit("asked: not found")
    s = s.replace(ASKED_OLD, ASKED_NEW); cc["jsCode"] = s
    rs = node(w, "Render Summary")["parameters"]; rs["jsCode"] = sub1(rs["jsCode"], NOTE_OLD, NOTE_NEW, "note")
    return w

# ================================================================ Book Series
ALL_OLD = """    human: 'Nothing was prepared - the room is taken on every one of those dates (' + taken.map(long).join('; ') + '). Ask exactly this, in one message: "The room is taken on all of those dates. Another room or time?"' } }];"""
ALL_NEW = """    // v7 (asked 7 Oct): the heads-up layout
    human: 'Nothing was prepared - the room is taken on every one of those dates (' + taken.map(long).join('; ') + '). Ask exactly this, in one message: "❌ *' + (String(REQ0.rooms || '').trim() || 'The room') + ' is already booked on all of those dates.*\\n\\nAnother room or time?"' } }];"""
WHY_OLD = """    const why = m.swap ? (m.swap.kind === 'room' ? ' (' + m.swap.from_rooms + ' is taken)' : ' (' + m.swap.from_rooms + ' is taken ' + tl(m.swap.from_start) + ' – ' + tl(m.swap.from_end) + ')') : '';"""
WHY_NEW = """    const why = m.swap ? (m.swap.kind === 'room' ? ' (' + m.swap.from_rooms + ' is already booked)' : ' (' + m.swap.from_rooms + ' is already booked ' + tl(m.swap.from_start) + ' – ' + tl(m.swap.from_end) + ')') : '';   // v7"""
FIL_OLD = """.filter(s => s && !/already passed|^Heads up: \\S.* is booked|picked|No time given/i.test(s));"""
FIL_NEW = """.filter(s => s && !/already passed|^(?:❌ )?Heads up: \\*?\\S.*\\bbooked\\b|picked|No time given/i.test(s));   // v7: the ❌ layout too"""
TK_OLD = """  if (taken.length) notes.unshift('Heads up: ' + F['Room'] + ' is taken on ' + taken.map(long).join(', ') + ', and no other usual room or time that day is free - ' + (taken.length === 1 ? 'that date' : 'those dates') + ' left out.');"""
TK_NEW = """  if (taken.length) notes.unshift('❌ Heads up: *' + F['Room'] + ' is already booked on ' + taken.map(long).join(', ') + '* - no other usual room or time that day is free, so ' + (taken.length === 1 ? 'that date is' : 'those dates are') + ' left out.');   // v7"""

def series(w):
    w["name"] = "Jessie — Book Series — v7 (taken-room layout)"
    ag = node(w, "Aggregate")["parameters"]; s = ag["jsCode"]
    s = sub1(s, ALL_OLD, ALL_NEW, "all"); s = sub1(s, WHY_OLD, WHY_NEW, "why"); s = sub1(s, FIL_OLD, FIL_NEW, "filter"); s = sub1(s, TK_OLD, TK_NEW, "taken")
    ag["jsCode"] = s
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(book(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
    json.dump(series(json.load(open(a[4]))), open(a[5], "w"), indent=2, ensure_ascii=False); print("wrote", a[5])
