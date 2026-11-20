#!/usr/bin/env python3
"""Slack Interactions v85 (Howard, 20 Nov): no Department field on the meeting form - "they can just input everything in the
title". The meeting still carries the booker's own department behind the scenes (what the field was set to unless changed),
so My bookings for coordinators, the Log and the description's "Dept:" read as before. Events never had the field.
Built on v84 (unimported; includes v84's Other guests hint) - import v85 only."""
import json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
w = json.load(open(os.path.join(ROOT, "workflows", "slack-interactions-v84.json")))
def rep(nd, old, new):
    n = [x for x in w["nodes"] if x["name"] == nd][0]; c = n["parameters"]["jsCode"]
    assert c.count(old) == 1, (nd, old[:60], c.count(old)); n["parameters"]["jsCode"] = c.replace(old, new)
rep("Build Step 2",
    "    if (s.purpose !== 'Event' && dOpts.length) blocks.push(input('department', 'Department', Object.assign({ type: 'static_select', action_id: 'department_pick',\n"
    "      placeholder: { type: 'plain_text', text: 'Select a department' }, options: dOpts }, dIni ? { initial_option: dIni } : {})));\n",
    "    // v85 (Howard, 20 Nov): no Department field - the title says it (\"BD x Marketing\"); Read Step 2 keeps the booker's own\n")
rep("Read Step 2", "const req = who(s.requester) || {};\n",
    "const req = who(s.requester) || {};\n"
    "// v85 (Howard, 20 Nov): a meeting has no Department field - the booker's own, as the field defaulted to (an older form still open sends its pick)\n"
    "if (!dept && s.kind === 'meeting' && s.purpose !== 'Event') dept = [].concat(req.Department || []).map(x => String((x && x.name) || x).trim()).filter(Boolean)[0] || '';\n")
w["name"] = "Jessie — Slack Interactions — v85 (no meeting department)"
with open(os.path.join(ROOT, "workflows", "slack-interactions-v85.json"), "w") as fh:
    json.dump(w, fh, indent=2, ensure_ascii=False); fh.write("\n")
print("wrote workflows/slack-interactions-v85.json", len(w["nodes"]), "nodes")
