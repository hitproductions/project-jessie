#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v20.json - "Jessie — Slack Interactions", v20 (v19 fixed): hotfix.

v19 put the "⏳ Your booking is being processed…" steps (Get Source -> Mark Source -> Source Shown? -> Show Source) between
To Prepare / Series? and the Prepare call. Prepare (Execute Workflow, no explicit inputs) passes on the item it receives, so
from v19 Book Session got Slack's chat.update answer (or Mark Source's) instead of the booking: every single booking from the
form came back MISSING_DETAILS ("a title, a start time, an end time, a room") and the form said "This couldn't be booked"
(Slack 15 Oct 17:09, M2; execution 44331). Series were not affected (Read Saved Series names its source).
Fix: a "Prepare Input" Code node right before Prepare returns To Prepare's output.
Built on workflows/imported/slack-interactions-v19-imported.json (the live download).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v19-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v20.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]

prep = by["Prepare"]
x, y = prep["position"]
node = {"parameters": {"jsCode": "// v20: Book Session gets the booking - To Prepare's output - whatever the ⏳ steps before this returned (v19 sent Slack's answer)\nreturn [{ json: $('To Prepare').first().json }];"},
        "id": str(uuid.uuid4()), "name": "Prepare Input", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [x - 180, y + 120]}
wf["nodes"].append(node)
n_re = 0
for src, v in C.items():
    for outs in v.get("main", []):
        for c in outs:
            if c["node"] == "Prepare":
                c["node"] = "Prepare Input"; n_re += 1
assert n_re == 2, n_re   # Source Shown? (false) and Show Source
C["Prepare Input"] = {"main": [[{"node": "Prepare", "type": "main", "index": 0}]]}

wf["name"] = "Jessie — Slack Interactions — v20 (v19 fixed)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes; rewired", n_re)
