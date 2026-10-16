#!/usr/bin/env python3
"""main v274 (rows: rooms, all day, session type): Jessie's own booking lists in chat ("what do I have …" - Mine Reply; a typed
change / cancel - Change Reply) get the form's row fixes (Slack Interactions v22): a booking's rooms in order from its "Rooms:"
line (Google reorders the attendees), "Likha (Big Room)" read as Likha, "Studio F + Studio A" with the holding rooms after, and
"all day" for an all-day booking (12:00 AM to 12:00 AM). And each row's Change / Cancel carries the booking's session type
(its "SType:" line), which the Change form (Slack Interactions v24) needs for its fields.
Built on workflows/imported/project-jessie-v273-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v273-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v274.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
PAIRS = [
    ("""function whenLine(b) { return dayShort(b.d) + ' · ' + (b.s ? t12(b.s) + ' – ' + t12(b.e) : 'all day') + (b.r ? ' · ' + b.r : ''); }""",
     """// v274: a booking's rooms - the studio (+ its booth), then the holding rooms; all day for 12:00 AM to 12:00 AM
function roomList(r) { return String(r || '').split(',').map(x => x.trim()).filter(Boolean); }
function roomMain(r) { const a = roomList(r); return [a[0]].concat(a.slice(1).filter(x => /^(?:Studio\\s|M\\d)/i.test(x))).filter(Boolean).join(' + '); }
function roomHold(r) { return roomList(r).slice(1).filter(x => !/^(?:Studio\\s|M\\d)/i.test(x)).join(', '); }
function whenLine(b) { return dayShort(b.d) + ' · ' + (b.s && !(b.s === '00:00' && b.e === '00:00') ? t12(b.s) + ' – ' + t12(b.e) : 'all day') + (b.r ? ' · ' + roomMain(b.r) + (roomHold(b.r) ? ' + ' + roomHold(b.r) : '') : ''); }"""),
    ("""function bkValue(b, n) { const v = { id: b.id, d: b.d, s: b.s || '', e: b.e || '', r: b.r || '', t: String(b.t || '').slice(0, 150) };""",
     """function bkValue(b, n) { const v = { id: b.id, d: b.d, s: b.s || '', e: b.e || '', r: b.r || '', t: String(b.t || '').slice(0, 150), st: b.st || '' };   // v274: st"""),
    ("""function roomName(x) { return String(x || '').replace(/^KDC Plaza-Top Level-/i, '').replace(/\\s*\\([^)]*\\)\\s*$/, '').trim(); }""",
     """function roomName(x) { return String(x || '').replace(/^KDC Plaza-Top Level-/i, '').replace(/(?:\\s*\\([^)]*\\))+\\s*$/, '').trim(); }   // v274: every "(…)" """),
    ("""  .map(a => roomName(a.displayName)).filter(Boolean);
  return r.length ? r.join(', ') : roomName(e.location); }""",
     """  .map(a => roomName(a.displayName)).filter(Boolean);
  // v274: Google lists the rooms in its own order - the booking's "Rooms:" line keeps studio, booth, holding rooms
  const w = (String(e.description || '').match(/(?:^|\\|)\\s*Rooms:\\s*([^|\\n]+)/i) || [])[1];
  if (w && r.length) { const o = w.split(',').map(x => x.trim()).filter(Boolean), lc = a => a.map(x => x.toLowerCase()).sort().join();
    if (lc(o) === lc(r)) return r.slice().sort((x, y) => o.findIndex(z => z.toLowerCase() === x.toLowerCase()) - o.findIndex(z => z.toLowerCase() === y.toLowerCase())).join(', '); }
  return r.length ? r.join(', ') : roomName(e.location); }"""),
    ("""function evBooking(e) {""",
     """function evType(e) { return ((String(e.description || '').match(/\\n\\s*SType:\\s*([^\\n]+)/) || [])[1] || '').trim(); }   // v274
function evBooking(e) {"""),
]
for name in ("Mine Reply", "Change Reply"):
    js = by[name]["parameters"]["jsCode"]
    for a, b in PAIRS:
        assert js.count(a) == 1, (name, a[:70], js.count(a))
        js = js.replace(a, b)
    a = """r: evRoom(e), t: e.summary || '(no title)' };"""
    assert js.count(a) == 2, (name, js.count(a))
    js = js.replace(a, """r: evRoom(e), t: e.summary || '(no title)', st: evType(e) };""")
    by[name]["parameters"]["jsCode"] = js
wf["name"] = "Project Jessie — v274 (rows: rooms, all day, session type)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
