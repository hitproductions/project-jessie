#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v80.json - Jessie — Slack Interactions — v80 (Additional studios), 9 Nov.

Howard, 9 Nov: change the "Multiple studios" label to "Additional studios". The optional multi-select after the room (v53) reads
"+ Additional studios" on Book a room (Build Step 2) and on Change (pairBlocksC - the same function in Build Change, Read Change,
To Move, After Move, Note Toggle, Build Change C). Label only: block ids, action ids and the placeholder ("Select more studios")
are unchanged, and meetings keep "+ Multiple rooms". Includes v79 ("Not free then:" under Vocal booths; not imported on its own).
Built on workflows/slack-interactions-v79.json (v79 built on v78 == the v78 live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "slack-interactions-v79.json")))
by = {n["name"]: n for n in wf["nodes"]}
OLD = "? '+ Multiple rooms' : '+ Multiple studios'"
NEW = "? '+ Multiple rooms' : '+ Additional studios'"
WANT = {"Build Step 2": 1, "Build Change": 1, "Read Change": 1, "To Move": 1, "After Move": 1, "Note Toggle": 1, "Build Change C": 1}
for n in wf["nodes"]:
    c = n.get("parameters", {}).get("jsCode", "")
    k = c.count(OLD)
    assert k == WANT.get(n["name"], 0), (n["name"], k)
    if k:
        n["parameters"]["jsCode"] = c.replace(OLD, NEW + "   /* v80 (Howard): Additional studios */")
wf["name"] = "Jessie — Slack Interactions — v80 (Additional studios)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v80.json")
with open(out, "w") as fh:
    json.dump(wf, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
