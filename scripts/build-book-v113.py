#!/usr/bin/env python3
"""Builds workflows/book-session-v113.json - "Jessie — Book Session", v113 (Studio E for Post Processing): round 9 note 4
(19 Oct) - Studio E is Post Processing's room only, like Studio M for Van Recording; any other booking type in Studio E is
refused (ROOM_UNSUITABLE, "Studio E is only for Post Processing."). The forms (Slack Interactions v26) never offer it; this is
the backstop. Nothing else changes.
Built on workflows/imported/book-session-v112-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "book-session-v112-imported.json")
OUT = os.path.join(ROOT, "workflows", "book-session-v113.json")
wf = json.load(open(SRC))
n = [x for x in wf["nodes"] if x["name"] == "Check Conflicts"][0]
js = n["parameters"]["jsCode"]
a = """  if (!/^van recording$/i.test(_st) && _lc.indexOf('studio m') !== -1)
    return [{ json: { verdict:'REJECTED', reason:'ROOM_UNSUITABLE', unsuitable: ['Studio M'], priority: [], last_resort: [],
      human: 'Studio M is only for Van Recording. Nothing was booked.' } }];"""
b = a + """
  // v113 (round 9, 19 Oct): Studio E is Post Processing's room only
  if (!/^post processing$/i.test(_st) && _lc.indexOf('studio e') !== -1)
    return [{ json: { verdict:'REJECTED', reason:'ROOM_UNSUITABLE', unsuitable: ['Studio E'], priority: [], last_resort: [],
      human: 'Studio E is only for Post Processing. Nothing was booked.' } }];"""
assert js.count(a) == 1
n["parameters"]["jsCode"] = js.replace(a, b)
wf["name"] = "Jessie — Book Session — v113 (Studio E for Post Processing)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
