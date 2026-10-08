#!/usr/bin/env python3
"""Book Session v100 (room question word for word) - 8 Oct 23:08 on main v248: "book studio 3 ... vo recording" still got the
model's "VO Recording isn't normally run in Studio 3. The usual rooms are ... Do you want one of those, or still Studio 3?"
That is ROOM_UNSUITABLE (a room in neither ranking list) - Book Session v99 changed ROOM_NOT_PRIORITY only. Now the same
"Ask exactly this" question, sent word for word by Guard Probe (v203): "Studio 3 isn't a usual VO Recording room - the
usual ones are Studio 7, Studio 8, Studio F and Studio C. One of those, or still Studio 3?"
  scripts/build-book-v100.py <book-v99> <book-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
OLD = ("human: ((stRec ? stRec.type : '') || 'That session type') + ' is not normally run in '\n"
       "             + notRun.join(', ') + '. Nothing was booked. The usual rooms for it are: '\n"
       "             + priorityNames.join(', ')\n"
       "             + '. Ask the requester whether they want one of those or still want ' + notRun.join(', ')\n"
       "             + '; if they still want it, call Prepare Booking again with room_override true.' } }];")
NEW = ("// v100 (8 Oct 23:08): one short question, sent word for word, as ROOM_NOT_PRIORITY since v99\n"
       "        human: 'Nothing was booked. Ask exactly this, in one message: \"' + (notRun.join(' and ') + ' isn\\'t a usual '\n"
       "             + ((stRec ? stRec.type : '') || 'this session type') + ' room - the usual ones are '\n"
       "             + (a => a.length <= 1 ? a.join('') : a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1])(priorityNames)\n"
       "             + '. One of those, or still ' + notRun.join(' and ') + '?').replace(/\"/g, '\\\\\"')\n"
       "             + '\" If they still want it, call Prepare Booking again with room_override true.' } }];")
def book(w):
    w["name"] = "Jessie — Book Session — v100 (room question word for word)"
    cc = node(w, "Check Conflicts")["parameters"]
    cc["jsCode"] = once(cc["jsCode"], OLD, NEW, "ROOM_UNSUITABLE")
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2: print(__doc__.strip()); sys.exit(2)
    json.dump(book(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
