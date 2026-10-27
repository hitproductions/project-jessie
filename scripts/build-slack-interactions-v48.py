#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v48.json - Jessie — Slack Interactions — v48 (department on Change rows), 27 Oct.

Howard's Slack test of v47 (PENDING 133): the New Clients row of a client kept through Change had an empty Department - the
Change form does not ask it. New Client C now reads it from the changed event's first line ("Dept: …", the replacement's
description Move Booking hands back since v38). Nothing else reads the row; the booking's own department is unchanged.
Built on workflows/imported/slack-interactions-v47-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v47-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}
js = by["New Client C"]["parameters"]["jsCode"]
a = "'Department': '',"
assert js.count(a) == 1
js = js.replace(a, "'Department': (() => { try {   // v48: from the changed event's first line (Move Booking hands back its description)\n"
    "    const d = String((($('Move').first() || {}).json || {}).description || '').split(/\\n|<br\\s*\\/?>/i)[0];\n"
    "    return ((d.match(/Dept:\\s*([^|\\n]+)/) || [])[1] || '').trim(); } catch (e) { return ''; } })(),")
by["New Client C"]["parameters"]["jsCode"] = js
wf["name"] = "Jessie — Slack Interactions — v48 (department on Change rows)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v48.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
