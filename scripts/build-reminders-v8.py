#!/usr/bin/env python3
"""Builds workflows/reminders-v8.json - Jessie — Reminders — v8 (meeting rooms), 28 Oct.

With Slack Interactions v53 a meeting or event can hold several rooms (one event, "Likha, Katha"). The reminder card read every
room after the first that is not a studio or M booth as a holding room ("Room: Likha / Holding room: Katha"). v8: a booking
whose first room is not a studio / M booth (a meeting room) lists all its rooms on the Room line ("Room: Likha + Katha"); a
session's studios, booths and holding rooms read as before. Nothing else changed (the launch switches untouched).
Built on workflows/imported/reminders-v7-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "reminders-v7-imported.json")))
RM_OLD = "function roomMain(r) { const a = roomList(r); return [a[0]].concat(a.slice(1).filter(x => /^(?:Studio\\s|M\\d)/i.test(x))).filter(Boolean).join(' + '); }"
RM_NEW = ("function roomMain(r) { const a = roomList(r); if (a[0] && !/^(?:Studio\\s|M\\d)/i.test(a[0])) return a.join(' + ');   // v8: a meeting in several rooms (\"Likha + Katha\")\n"
          "  return [a[0]].concat(a.slice(1).filter(x => /^(?:Studio\\s|M\\d)/i.test(x))).filter(Boolean).join(' + '); }")
RH_OLD = "function roomHold(r) { return roomList(r).slice(1).filter(x => !/^(?:Studio\\s|M\\d)/i.test(x)).join(', '); }"
RH_NEW = ("function roomHold(r) { const a = roomList(r); if (a[0] && !/^(?:Studio\\s|M\\d)/i.test(a[0])) return '';   // v8: a meeting's rooms are all its rooms\n"
          "  return a.slice(1).filter(x => !/^(?:Studio\\s|M\\d)/i.test(x)).join(', '); }")
n = 0
for node in wf["nodes"]:
    js = node["parameters"].get("jsCode")
    if js and RM_OLD in js:
        assert js.count(RM_OLD) == 1 and js.count(RH_OLD) == 1
        node["parameters"]["jsCode"] = js.replace(RM_OLD, RM_NEW).replace(RH_OLD, RH_NEW)
        n += 1
assert n == 1, n
wf["name"] = "Jessie — Reminders — v8 (meeting rooms)"
out = os.path.join(ROOT, "workflows", "reminders-v8.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
