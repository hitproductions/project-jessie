#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v75.json - Jessie — Slack Interactions — v75 (no Picked: lines), 6 Nov.

Howard, 6 Nov (after v74): "remove picked: also for vocal booths and holding rooms. i noticed after picking one in multiselect, the form
loads. is that caused by the picked: ?" - yes: since v64 every pick in a multi-select was sent to n8n (dispatch_action) only so Note Toggle
could redraw the Picked: line, and that redraw is the loading. v75 draws no Picked: line anywhere and Vocal booths / Holding rooms (Book a
room and Change) no longer send each pick - as before v64. The picks are read on submit, as always.
Built on workflows/slack-interactions-v74.json (v74 built on the v73 live download; v75 includes it).
"""
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "slack-interactions-v74.json")))
by = {n["name"]: n for n in wf["nodes"]}
CHANGE_NODES = ("Build Change", "Read Change", "To Move", "After Move", "Note Toggle", "Build Change C")


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:160])
    return js.replace(a, b)


def code(name, f):
    p = by[name]["parameters"]
    p["jsCode"] = f(p["jsCode"])


ACT_OLD = "const ACT = ['booth_pick', 'holding_pick', 'booth_c_pick', 'holding_c_pick'];"
ACT_NEW = "const ACT = [];   // v75 (Howard): no Picked: line anywhere - each one cost a round trip to n8n on every pick"
BOOTH_OLD = "return [Object.assign({ type: 'input', dispatch_action: true, block_id: bid, label: pt('Vocal booths')"
BOOTH_NEW = "return [Object.assign({ type: 'input', block_id: bid, label: pt('Vocal booths')"
for name in ("Build Step 2",) + CHANGE_NODES:
    code(name, lambda js: sub(js, ACT_OLD, ACT_NEW))
for name in ("Build Step 1", "Build Step 2", "Note Toggle"):
    code(name, lambda js: sub(js, BOOTH_OLD, BOOTH_NEW))
code("Build Step 2", lambda js: sub(js, "{ type: 'input', dispatch_action: true, block_id: 'holding', optional: true,", "{ type: 'input', block_id: 'holding', optional: true,"))
for name in CHANGE_NODES:
    def f(js):
        js = sub(js, "out.push({ type: 'input', dispatch_action: true, block_id: 'booth_c',", "out.push({ type: 'input', block_id: 'booth_c',")
        js = sub(js, "out.push({ type: 'input', dispatch_action: true, block_id: 'holding_c',", "out.push({ type: 'input', block_id: 'holding_c',")
        js = sub(js, ",\n    el && el.type === 'multi_static_select' && /^(?:booth|holding)_c_pick$/.test(String(el.action_id)) ? { dispatch_action: true } : {}   /* v74: only where a Picked: line is drawn */);",
                 ");   /* v75: no multi-select sends its picks (no Picked: line) */")
        return js
    code(name, f)

# nothing left that sends a multi-select's picks
for n in wf["nodes"]:
    js = n["parameters"].get("jsCode", "")
    for m in re.finditer(r"dispatch_action: true", js):
        near = js[m.start() - 40:m.start() + 400]
        assert "multi_static_select" not in near.split("}, {")[0] or "rep_" in near, (n["name"], near[:300])

wf["name"] = "Jessie — Slack Interactions — v75 (no Picked: lines)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v75.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
