#!/usr/bin/env python3
"""main v234 (heads-up blocks) - asked 7 Oct (PENDING 95), on v233 (never imported; v234 includes it). The heads-up becomes
three blocks with emoji, the room and its time still in bold, the session title without quotes:
    ❌ Heads up: *Studio 7 is already booked 3:00 PM – 5:00 PM* on Friday, October 8 by this session: WHEAT SUN / Jem Lim / AEG

    ✅ Studio 7 is free on the same day at:
    • 8:00 AM – 3:00 PM
    • 5:00 PM – 10:00 PM

    ✅ Free all day:
    Studio 1 · Studio 2 · Studio 8 · Studio F · Studio 3
Several bookings that day: "*... booked 8:00 AM – 12:00 PM and 12:15 PM – 9:45 PM* ... by these sessions: A · B" (same order).
The requester's own: "*You already have Studio 7 booked ...* ... with this session: X". An M booth at a requested time:
"✅ Free at that time:" and the booths on the next line. The prompt notice gets it as plain text.
  scripts/build-early-room-emoji.py <main-v233> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

OLD = """        const _opts = [];
        if (!P.timed && _gaps.length) _opts.push(P.room + ' is free ' + _gaps.map(x => _hmT(x[0]) + ' – ' + _hmT(x[1])).join(' and ') + '.');
        if (alts.length) _opts.push((P.timed ? 'Free at that time: ' : 'Free all day: ') + alts.join(' · '));
        // v233 (asked 7 Oct): the room and its time in bold, then a blank line before the options
        const _bt = evs.map((e, i) => '*' + (i === 0 ? (own ? 'you already have ' + P.room + ' booked ' : P.room + ' is already booked ') : '')
          + (e.allDay ? 'all day' : hm(e.start) + ' – ' + hm(e.end)) + '* (“' + e.title + '”)').join(' and ');
        const text = 'Heads up: ' + _bt + ' on ' + d0.label + '.'
          + (_opts.length ? '\\n\\n' + _opts.join('\\n') : '');"""
NEW = """        // v234 (asked 7 Oct): three blocks with emoji - what is taken (room and time in bold), when the room is still free that
        // day (one time per line), and the other rooms; a blank line between blocks
        const _opts = [];
        if (!P.timed && _gaps.length) _opts.push('✅ ' + P.room + ' is free on the same day at:\\n' + _gaps.map(x => '• ' + _hmT(x[0]) + ' – ' + _hmT(x[1])).join('\\n'));
        if (alts.length) _opts.push((P.timed ? '✅ Free at that time:' : '✅ Free all day:') + '\\n' + alts.join(' · '));
        const _times = evs.map(e => e.allDay ? 'all day' : hm(e.start) + ' – ' + hm(e.end)).join(' and ');
        const text = '❌ Heads up: *' + (own ? 'You already have ' + P.room + ' booked ' : P.room + ' is already booked ') + _times + '* on ' + d0.label
          + (own ? ' with ' : ' by ') + (evs.length > 1 ? 'these sessions: ' : 'this session: ') + evs.map(e => e.title).join(' · ')
          + (_opts.length ? '\\n\\n' + _opts.join('\\n\\n') : '');"""
NOTICE_OLD = """text.replace(/^Heads up: /, '').replace(/\\*/g, '').replace(/\\n+/g, ' ')"""
NOTICE_NEW = """text.replace(/^❌ Heads up: /, '').replace(/[*❌✅]/g, '').replace(/\\n•\\s*/g, ' / ').replace(/:\\s*\\/\\s*/g, ': ').replace(/\\s*\\n+\\s*/g, ' ')"""
GP_OLD = """!/^\\s*heads up:[^\\n]*already (?:booked|have)/i.test(text)"""
GP_NEW = """!/^\\s*(?:❌\\s*)?heads up:[^\\n]*already (?:booked|have)/i.test(text)"""

def main(w):
    w["name"] = "Project Jessie — v234 (heads-up blocks)"
    r = node(w, "Early Room Result")["parameters"]; s = r["jsCode"]
    s = sub1(s, OLD, NEW, "text"); s = sub1(s, NOTICE_OLD, NOTICE_NEW, "notice"); r["jsCode"] = s
    g = node(w, "Guard Probe")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GP_OLD, GP_NEW, "gp")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
