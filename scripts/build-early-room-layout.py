#!/usr/bin/env python3
"""main v233 (heads-up layout) - asked 7 Oct after the v232 Slack check (PENDING 95). The heads-up's first line puts the
taken room and its time in bold, and a blank line follows it:
    Heads up: *Studio 7 is already booked 3:00 PM – 5:00 PM* (“WHEAT SUN / Jem Lim / AEG”) on Friday, October 8.

    Studio 7 is free 8:00 AM – 3:00 PM and 5:00 PM – 10:00 PM.
    Free all day: Studio 1 · Studio 2 · Studio 8 · Studio F · Studio 3
With several bookings that day each time is bold ("*... booked 8:00 AM – 12:00 PM* (“A”) and *12:15 PM – 9:45 PM* (“B”)").
Only the heads-up (Early Room Result's prepend mode) changes; the "already booked" reply for a requested time is as it was.
  scripts/build-early-room-layout.py <main-v232> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

OLD = """        const text = 'Heads up: ' + (own ? 'you already have ' + P.room + ' booked ' : P.room + ' is already booked ') + desc + ' on ' + d0.label + '.'
          + (_opts.length ? '\\n' + _opts.join('\\n') : '');"""
NEW = """        // v233 (asked 7 Oct): the room and its time in bold, then a blank line before the options
        const _bt = evs.map((e, i) => '*' + (i === 0 ? (own ? 'you already have ' + P.room + ' booked ' : P.room + ' is already booked ') : '')
          + (e.allDay ? 'all day' : hm(e.start) + ' – ' + hm(e.end)) + '* (“' + e.title + '”)').join(' and ');
        const text = 'Heads up: ' + _bt + ' on ' + d0.label + '.'
          + (_opts.length ? '\\n\\n' + _opts.join('\\n') : '');"""
NOTICE_OLD = """text.replace(/^Heads up: /, '').replace(/\\n/g, ' ')"""
NOTICE_NEW = """text.replace(/^Heads up: /, '').replace(/\\*/g, '').replace(/\\n+/g, ' ')"""

def main(w):
    w["name"] = "Project Jessie — v233 (heads-up layout)"
    r = node(w, "Early Room Result")["parameters"]; s = r["jsCode"]
    s = sub1(s, OLD, NEW, "text"); s = sub1(s, NOTICE_OLD, NOTICE_NEW, "notice")
    r["jsCode"] = s
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
