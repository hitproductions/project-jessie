#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v34.json - "Jessie — Slack Interactions", v34 (the room note once), 20 Oct.

Howard, 20 Oct ~22:00: typed "book studio e for dilan …" (Post Processing), then picked Music Presentation in step 1. Step 2
said "Studio E isn't a room for Music Presentation. These are free:" (good - it spotted the change) with Studio F ticked; after a
problem the form came back with the same line although Studio F was picked. The line is now tagged (block_id pre_note) and the
form shown again after a problem (formAgain in After Prepare / After Book / After Prepare Series) leaves it out.
Built on workflows/imported/slack-interactions-v33-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v33-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v34.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:100], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


_js = by["Build Step 2"]["parameters"]["jsCode"]
_a = "if (preNote) blocks.push({ type: 'section', text: md('⚠️ ' + preNote) });"
assert _js.count(_a) == 2, _js.count(_a)   # single dates and a series
by["Build Step 2"]["parameters"]["jsCode"] = _js.replace(_a, "if (preNote) blocks.push({ type: 'section', block_id: 'pre_note', text: md('⚠️ ' + preNote) });   // v34: tagged - not repeated after a problem")
for n in ["After Prepare", "After Book", "After Prepare Series"]:
    patch(n, [("filter(b => b.block_id !== 'problem' && b.block_id !== 'problem_div' && extraIds.indexOf(b.block_id) === -1)",
               "filter(b => b.block_id !== 'problem' && b.block_id !== 'problem_div' && b.block_id !== 'pre_note' && extraIds.indexOf(b.block_id) === -1)   // v34: the room note only once")])
wf["name"] = "Jessie — Slack Interactions — v34 (the room note once)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
