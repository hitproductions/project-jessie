#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v34.json - "Jessie — Slack Interactions", v34 (the room note once), 20 Oct.

Howard, 20 Oct ~22:00: typed "book studio e for dilan …" (Post Processing), then picked Music Presentation in step 1. Step 2
said "Studio E isn't a room for Music Presentation. These are free:" (good - it spotted the change) with Studio F ticked; after a
problem the form came back with the same line although Studio F was picked. The line is now tagged (block_id pre_note) and the
form shown again after a problem (formAgain in After Prepare / After Book / After Prepare Series) leaves it out.
Also: NEED_SESSION_TYPE in words ("Couldn't tell which booking type this is. Go Back and pick it again.") - it showed as "Couldn't
book this" on 20 Oct 22:00; Book Session v119 fixes the cause (the most specific type named wins).
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
# NEED_SESSION_TYPE in words (20 Oct 22:00, execution 53049: "Couldn't book this" - Book Session v119 fixes the cause)
for n in ["After Prepare", "After Book", "After Prepare Series"]:
    js = by[n]["parameters"]["jsCode"]
    a1 = "  return { warn: 'Couldn’t book this. Che"
    assert js.count(a1) == 1, (n, js.count(a1))
    js = js.replace(a1, "  if (reason === 'NEED_SESSION_TYPE') return { warn: 'Couldn’t tell which booking type this is. Go *Back* and pick it again.' };   // v34\n" + a1)
    by[n]["parameters"]["jsCode"] = js
wf["name"] = "Jessie — Slack Interactions — v34 (the room note once)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
