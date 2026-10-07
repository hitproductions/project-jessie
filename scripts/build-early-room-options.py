#!/usr/bin/env python3
"""main v231 (early room options) - live 7 Oct 17:17 PHT on main v230 (PENDING 95):
  "book studio 7 tomorrow for me" -> "Heads up: Studio 7 is already booked 3:00 PM – 5:00 PM (“WHEAT SUN / Jem Lim / AEG”) on
  Friday, October 8." and then the questions. The options (other rooms, other times) only came a turn later, once a time was
  given. Decided (Howard, 7 Oct): the recommendation comes with the heads-up, in the first reply.
  With no time yet the heads-up now also says when that room is still free that day and which rooms are free all day:
    Heads up: Studio 7 is already booked 3:00 PM – 5:00 PM (“WHEAT SUN / Jem Lim / AEG”) on Friday, October 8.
    Studio 7 is free 8:00 AM – 3:00 PM and 5:00 PM – 10:00 PM.
    Free all day: Studio 8 · Studio F · ...
  An M booth taken at a requested time (heads-up only, consent engine) gets "Free at that time: M1 · M2 ...". The questions
  still follow. Only Early Room Result changes.
  scripts/build-early-room-options.py <main-v230> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

OLD = """        const text = 'Heads up: ' + (own ? 'you already have ' + P.room + ' booked ' : P.room + ' is already booked ') + desc + ' on ' + d0.label + '.';
        early = { mode: 'prepend', text, own, room: P.room };"""
NEW = """        // v231 (live 7 Oct 17:17, decided): the options come with the heads-up - when the room is still free that day (no
        // time yet; gaps of 30 minutes or more in 8 AM - 10 PM) and the other rooms free all day, or at the requested time
        // for an M booth
        const _gaps = []; { let at2 = ws; for (const x of iv) { if (x[0] - at2 >= 1800000) _gaps.push([at2, x[0]]); at2 = Math.max(at2, x[1]); } if (we - at2 >= 1800000) _gaps.push([at2, we]); }
        const _hmT = t => new Date(t).toLocaleTimeString('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' });
        const _opts = [];
        if (!P.timed && _gaps.length) _opts.push(P.room + ' is free ' + _gaps.map(x => _hmT(x[0]) + ' – ' + _hmT(x[1])).join(' and ') + '.');
        if (alts.length) _opts.push((P.timed ? 'Free at that time: ' : 'Free all day: ') + alts.join(' · '));
        const text = 'Heads up: ' + (own ? 'you already have ' + P.room + ' booked ' : P.room + ' is already booked ') + desc + ' on ' + d0.label + '.'
          + (_opts.length ? '\\n' + _opts.join('\\n') : '');
        early = { mode: 'prepend', text, own, room: P.room };"""
NOTICE_OLD = """        notice = 'ROOM CHECK (done by code this turn): ' + text.replace(/^Heads up: /, '') + ' That line is added above your reply - do not '
          + 'repeat it. Carry on collecting the details' + (P.timed ? '.' : '; when you ask for the time, do not suggest those hours.');"""
NOTICE_NEW = """        notice = 'ROOM CHECK (done by code this turn): ' + text.replace(/^Heads up: /, '').replace(/\\n/g, ' ') + ' Those lines are added above '
          + 'your reply - do not repeat them or list rooms yourself. Carry on collecting the details' + (P.timed ? '.' : '; when you ask for the time, do not suggest the booked hours.');"""

def main(w):
    w["name"] = "Project Jessie — v231 (early room options)"
    r = node(w, "Early Room Result")["parameters"]; s = r["jsCode"]
    s = sub1(s, OLD, NEW, "prepend"); s = sub1(s, NOTICE_OLD, NOTICE_NEW, "notice")
    r["jsCode"] = s
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
