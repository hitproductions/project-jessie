#!/usr/bin/env python3
"""main v192 (move range fix) + Book Session v66 (proposed time) - live QA 29 Sep 20:34-20:36 PHT (ORANGE / Sasa Abella / AEG).
  scripts/build-move-range-proposed-time.py <main-pull> <main-out> <book-pull> <book-out>

main v192  "move it to 3-6pm" right after "Booked." (10-11 AM) became a move to 6-7 PM, and "3-6pm not 6-7" gave the same
           card again. The change-after-booking code (v184/v185) counted only times carrying am/pm, so "3-6pm" was one time,
           6 PM, read as a new start with the old one-hour length; Move Booking's times are forced from it. The newest
           message's range is now read first, with the same reader new bookings use ("3-6pm", "3pm to 6pm", "from 3 to
           6pm", "10am-12nn"); the first range wins ("3-6pm not 6-7" -> 3-6). A single time still keeps the length.
Book v66   "i want to book a sched tomorrow" ... no time was ever typed, and the summary showed 10:00-11:00 AM as if asked
           for. Decided 29 Sep: propose a time, say it was proposed, and ask what time they want. In prepare mode, when
           the requester's messages hold no time at all, the summary notes "No time was given, so I proposed 10:00 AM -
           11:00 AM (Studio 7 is free then). What time would you like? Tell me, or reply yes to book this time."
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

BF_OLD = """          let ns = '', ne = '';
          if (tm && one.length === 1 && !/\\b\\d+(?:\\.\\d+)?\\s*(?:hours?|hrs?|mins?|minutes)\\b/i.test(_tmsg)) {"""
BF_NEW = """          let ns = '', ne = '';
          // v192 (live QA 29 Sep): a range in the newest message is the new time as given - "3-6pm" was read as one time
          // (6 PM, the only one with pm) and became 6-7. Same reader as a new booking; the first range wins ("3-6pm not 6-7").
          { const _rg = _tmsg.match(RANGE);
            if (_rg && (_rg[3] || _rg[6])) {
              const m1 = _rg[3], m2 = _rg[6] || _rg[3];
              let s = hm(_rg[1], _rg[2], m1 || m2); const e = hm(_rg[4], _rg[5], m2);
              if (!m1 && s && e && s >= e) s = hm(_rg[1], _rg[2], String(m2).toLowerCase().startsWith('p') ? 'am' : 'pm');
              if (s && e && s < e) { ns = s; ne = e; }
            } }
          if (!ns && tm && one.length === 1 && !/\\b\\d+(?:\\.\\d+)?\\s*(?:hours?|hrs?|mins?|minutes)\\b/i.test(_tmsg)) {"""

CC_OLD = "return [{ json: { verdict:'CLEAR', duration_note: durationNote, final_rooms: REQ.rooms,"
CC_NEW = """// v66 (live QA 29 Sep): no time typed at all - the summary says the time was proposed and asks for theirs.
const __timeProposed = __prep && !__series && !allDay && !!String(REQ.requester_text || '').trim()
  && !/\\b\\d{1,2}(?::\\d{2})?\\s*(?:am|pm|a\\.m\\.|p\\.m\\.|nn|noon)\\b|\\b\\d{1,2}:\\d{2}\\b|\\b(?:noon|midnight|morning|afternoon|evening|tonight|lunch|all day|whole day|half day)\\b|\\bat\\s+\\d{1,2}\\b|\\b\\d{1,2}\\s*(?:-|–|to|until|till)\\s*\\d{1,2}\\b/i.test(String(REQ.requester_text));
return [{ json: { verdict:'CLEAR', duration_note: durationNote, time_proposed: __timeProposed, final_rooms: REQ.rooms,"""
RS_OLD = "// v63 (QA bugs 11/13): the room was picked, not asked for - say so and ask if it is OK."
RS_NEW = """// v66: no time was typed - the time shown is a proposal; say so and ask what time they want.
if (CC.time_proposed && F['Time'] && !allDay) notes.unshift('No time was given, so I proposed ' + F['Time'] + ' (' + (rooms || 'the room') + ' is free then). What time would you like? Tell me, or reply yes to book this time.');
""" + RS_OLD

def main_fix(w):
    w["name"] = "Project Jessie — v192 (move range fix)"
    b = node(w, "Booked For")["parameters"]; b["jsCode"] = sub1(b["jsCode"], BF_OLD, BF_NEW, "bf")
    return w

def book_fix(w):
    w["name"] = "Jessie — Book Session — v66 (proposed time)"
    c = node(w, "Check Conflicts")["parameters"]; c["jsCode"] = sub1(c["jsCode"], CC_OLD, CC_NEW, "cc")
    r = node(w, "Render Summary")["parameters"]; r["jsCode"] = sub1(r["jsCode"], RS_OLD, RS_NEW, "rs")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main_fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    json.dump(book_fix(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1], a[3])
