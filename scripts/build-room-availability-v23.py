#!/usr/bin/env python3
"""Builds workflows/room-availability-v23.json - "Jessie — Room Availability", v23 (taken rooms with their bookings), 21 Oct.

Slice 2 (docs/design/slice-2-approvals.md): the booking form's "Booked – ask to use" group needs to know, for each taken room,
what is in it - so a single window's answer now also carries busy_detail: per taken room, the bookings in that window (event
id, title, start / end, booking type from its SType line, ref: and team: ids, standing hold = a recurring event, all day).
Everything else is unchanged (the day-by-day answer has no busy_detail - requests are for a single date).
Built on workflows/imported/room-availability-v22-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "room-availability-v22-imported.json")
OUT = os.path.join(ROOT, "workflows", "room-availability-v23.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
js = by["Compute Availability"]["parameters"]["jsCode"]

a = "const busy = {}, busyIv = {}, unidentified = [];   // v20: busyIv = what and when, per room\n"
assert js.count(a) == 1
js = js.replace(a, a.rstrip("\n") + "\nconst busyEv = {};   // v23: the bookings themselves, per taken room (the form's \"Booked – ask to use\")\n")
a = "      busy[k] = ev.summary || '(no title)'; matched = true;\n"
assert js.count(a) == 1
js = js.replace(a, a + "      (busyEv[k] = busyEv[k] || []).push(ev);   // v23\n")
a = "const out = { status:'OK', window: { start: REQ.start_iso, end: REQ.end_iso }, asked: askedAnswer,\n  busy: Object.keys(busy).map(k => k + ' (' + busy[k] + ')') };\n"
assert js.count(a) == 1
js = js.replace(a, a + r"""// v23 (slice 2): each taken room with its bookings - the form works out which can be asked for (the same rules as Book Session)
out.busy_detail = Object.keys(busyEv).map(k => ({ room: k, events: busyEv[k].map(ev => { const d = String(ev.description || '');
  return { id: ev.id || '', title: ev.summary || '(no title)', start: (ev.start && (ev.start.dateTime || ev.start.date)) || '', end: (ev.end && (ev.end.dateTime || ev.end.date)) || '',
    allDay: !!(ev.start && ev.start.date && !ev.start.dateTime), recurring: !!ev.recurringEventId,
    stype: ((d.match(/SType:\s*([^\n|]+)/i) || [])[1] || '').trim(), ref: ((d.match(/ref:\s*([A-Za-z0-9]+)/) || [])[1] || ''),
    team: ((d.match(/team:\s*([^|\n]+)/) || [])[1] || '').split(/[\s,]+/).filter(Boolean) }; }) }));
""")
by["Compute Availability"]["parameters"]["jsCode"] = js
wf["name"] = "Jessie — Room Availability — v23 (taken rooms with their bookings)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
