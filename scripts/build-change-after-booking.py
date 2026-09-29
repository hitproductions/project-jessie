#!/usr/bin/env python3
"""Live QA 29 Sep 13:44 PHT: "Book Studio 8 ... 2pm to 4pm" -> yes -> "Booked." -> "actually make it 3pm instead".
Jessie prepared a NEW 3-5 PM booking, which clashed with the one just made (by the same person), and offered other
rooms. A change right after a booking is a move of that booking.
  scripts/build-change-after-booking.py <main-pull> <main-out> <book-pull> <book-out>

main  Booked For: when the scan stops at Jessie's "Booked.", the booking just made is read from the summary before it
      (title, date, time, room). If the requester's messages since are a change ("actually", "instead", "make it",
      "push", "extend", "until" ...) and not another booking ("also", "another", "too"), the model is told it is a move
      of that booking, with the new times worked out the same way as before a booking (a new start keeps the length).
      Gate Context: a lone time right after "Booked." is not flagged start-time-only.
book  Check Conflicts: when every clash is the requester's own booking (same ref:), the refusal says so and asks
      whether to move that booking, instead of "room taken" and other rooms. The reason stays ROOM_OCCUPIED (with
      own_booking: true) so nothing downstream changes.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

BF_SCAN_OLD = """    if (isBot(m)) {
      if (/^\\s*\\*?(booked\\b|done\\s*-|moved\\b|cancell?ed\\b)|has been booked/i.test(t)) break;"""
BF_SCAN_NEW = """    if (isBot(m)) {
      if (/^\\s*\\*?(booked\\b|done\\s*-|moved\\b|cancell?ed\\b)|has been booked/i.test(t)) { if (/^\\s*\\*?booked\\b|has been booked/i.test(t)) __bookedAt = n; break; }"""
BF_LET_OLD = "  const mine = [], theirs = [];"
BF_LET_NEW = "  let __bookedAt = -1;   // v184: where the scan met Jessie's \"Booked.\"\n  const mine = [], theirs = [];"

BF_NOTE_ANCHOR = "  const notes = [];\n  const said = [];"
BF_NOTE_NEW = r"""  // --- v184 (live QA 29 Sep): a change right after a booking is a move of that booking --------------------------
  // "Booked." then "actually make it 3pm instead" was prepared as a second booking, which clashed with the first.
  out.justBooked = null; out.changeJustBooked = false;
  try {
    if (__bookedAt > 0 && mine.length) {
      let sum = '';
      for (let k = __bookedAt; k < msgs.length && k < __bookedAt + 6; k++) {
        const mm = msgs[k]; if (!isBot(mm)) continue; const tx = textOf(mm);
        if (/\*Date:\*/.test(tx) && /\*Time:\*/.test(tx)) { sum = tx; break; }
      }
      const said2 = mine.join('\n');
      const CHANGE = /\b(actually|instead|make it|change|move|push|shift|extend|shorten|earlier|later|until|till|reschedule|switch)\b/i;
      const NEWREQ = /\b(another|also|too|second|as well|new booking|one more)\b/i;
      if (sum && CHANGE.test(said2) && !NEWREQ.test(said2)) {
        const g = re => ((sum.match(re) || [])[1] || '').trim();
        const jb = { title: g(/^\s*\*([^*\n]+)\*\s*$/m), date: g(/\*Date:\*\s*([^\n]+)/), time: g(/\*Time:\*\s*([^\n]+)/), room: g(/\*Rooms?:\*\s*([^\n]+)/) };
        const MN = ['january','february','march','april','may','june','july','august','september','october','november','december'];
        const dm = jb.date.toLowerCase().match(/([a-z]+)\s+(\d{1,2}),?\s+(\d{4})/);
        jb.iso = dm && MN.indexOf(dm[1]) !== -1 ? dm[3] + '-' + String(MN.indexOf(dm[1]) + 1).padStart(2, '0') + '-' + String(+dm[2]).padStart(2, '0') : '';
        if (jb.title) {
          out.justBooked = jb; out.changeJustBooked = true;
          // new times, as before a booking: a new start keeps the length; "until / extend to" moves the end
          const tm = jb.time.match(/(\d{1,2}):(\d{2})\s*([AP]M)\s*[–-]\s*(\d{1,2}):(\d{2})\s*([AP]M)/i);
          const one = [...said2.matchAll(/\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.|nn|noon)\b/gi)];
          let ns = '', ne = '';
          if (tm && one.length === 1 && !/\b\d+(?:\.\d+)?\s*(?:hours?|hrs?|mins?|minutes)\b/i.test(said2)) {
            const ps = hm(tm[1], tm[2], tm[3]), pe = hm(tm[4], tm[5], tm[6]), v = hm(one[0][1], one[0][2], one[0][3]);
            const mins = x => +x.slice(0, 2) * 60 + +x.slice(3), fmt = x => String(Math.floor(x / 60)).padStart(2, '0') + ':' + String(x % 60).padStart(2, '0');
            const endWord = /\b(?:until|till|til|up to|to end|end(?:s|ing)?(?: at)?|finish(?:es|ing)?(?: at)?|extend(?:ed)?(?: it)?(?: to| until| till)?)\b/i.test(said2);
            if (ps && pe && v) {
              if (endWord) { if (mins(v) > mins(ps)) { ns = ps; ne = v; } }
              else { const e2 = mins(v) + (mins(pe) - mins(ps)); if (e2 <= 23 * 60 + 59) { ns = v; ne = fmt(e2); } }
            }
          }
          const f12 = x => { const h = +x.slice(0, 2); return (h % 12 || 12) + ':' + x.slice(3) + ' ' + (h < 12 ? 'AM' : 'PM'); };
          out.moveStart = ns; out.moveEnd = ne;
          notes.push('THEY ARE CHANGING THE BOOKING THEY JUST MADE: "' + jb.title + '" on ' + jb.date + ', ' + jb.time + (jb.room ? ', ' + jb.room : '')
            + '. This is a change to that booking, not a new one: call Move Booking for it (title exactly "' + jb.title + '"'
            + (jb.iso ? ', booking_date ' + jb.iso : '') + (ns ? ', new time ' + f12(ns) + ' to ' + f12(ne) + (jb.iso ? ' on ' + jb.iso : '') : '')
            + ') and show them the move to confirm. Do not call Prepare Booking or Book Session for it.');
        }
      }
    }
  } catch (e) {}
"""

GATE_OLD = "else if (timeHits.length === 1 && /\\*?Time:\\*?\\s*\\d{1,2}:\\d{2}\\s*[AP]M\\s*[–-]\\s*\\d{1,2}:\\d{2}\\s*[AP]M/i.test(lastBotText)) { delete store[soKey]; }"
GATE_NEW = ("else if (timeHits.length === 1 && (/\\*?Time:\\*?\\s*\\d{1,2}:\\d{2}\\s*[AP]M\\s*[–-]\\s*\\d{1,2}:\\d{2}\\s*[AP]M/i.test(lastBotText)"
            " || /^\\s*\\*?booked\\b/i.test(lastBotText))) { delete store[soKey]; }   // v184: right after \"Booked.\" it is a change too")

def main_fix(w):
    w["name"] = "Project Jessie — v184 (change after booking)"
    b = node(w, "Booked For")["parameters"]; c = b["jsCode"]
    c = sub1(c, BF_LET_OLD, BF_LET_NEW, "let")
    c = sub1(c, BF_SCAN_OLD, BF_SCAN_NEW, "scan")
    c = sub1(c, BF_NOTE_ANCHOR, BF_NOTE_ANCHOR.split("\n")[0] + "\n" + BF_NOTE_NEW + BF_NOTE_ANCHOR.split("\n")[1], "notice")
    b["jsCode"] = c
    g = node(w, "Gate Context")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GATE_OLD, GATE_NEW, "gate")
    return w

BS_OLD = "  // v51: the final details ride along so Prepare Booking can render a summary for a consent-eligible clash.\n  return [{ json: { verdict:'REJECTED', reason:'ROOM_OCCUPIED', conflicts,"
BS_NEW = """  // v61 (live QA 29 Sep): every clash is the requester's own booking - most often the one just made, and they are
  // changing it. Say so and ask whether to move it, instead of "room taken" and other rooms.
  const _myRef = (String(REQ.description || '').match(/ref:\\s*([A-Za-z0-9]+)/) || [])[1] || '';
  const _own = !!_myRef && conflicts.length > 0 && conflicts.every(c => ((String(c.description || '').match(/ref:\\s*([A-Za-z0-9]+)/) || [])[1] || '') === _myRef);
  if (_own) {
    const _t = x => new Date(x).toLocaleTimeString('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' });
    const _when = c => _allDay(c) ? 'all day' : (_t(c.start) + ' – ' + _t(c.end));
    return [{ json: { verdict:'REJECTED', reason:'ROOM_OCCUPIED', own_booking: true, conflicts,
      human: 'That overlaps a booking you already have: ' + conflicts.map(c => '"' + c.summary + '" (' + c.room + ', ' + _when(c) + ')').join('; ')
        + '. Nothing was booked. Ask the requester whether they want to move that booking to the new time instead of making a second one; if they do, call Move Booking for it.' } }];
  }
""" + BS_OLD

def book_fix(w):
    w["name"] = "Jessie — Book Session — v61 (own booking)"
    n = node(w, "Check Conflicts")["parameters"]; n["jsCode"] = sub1(n["jsCode"], BS_OLD, BS_NEW, "own booking")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main_fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    json.dump(book_fix(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1], a[3])
