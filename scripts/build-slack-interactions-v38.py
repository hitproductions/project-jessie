#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v38.json - "Jessie — Slack Interactions", v38 (cleared: the request checked), 21 Oct.

Pre-QA review (21 Oct): "I've cleared it with them" -> "They'll move it – I'll pick where" (route 18) opened the booker's Change
form, to be changed as its booker, without reading the request - after the booker had pressed Keep (REJECTED is final), or
from someone else's form, it still opened. The sheet is now read first on both choices (Read Requests C before Cleared Move?),
and Build Change C opens the Change form only for an open request and its requester (or Howard while testing); otherwise "That
request isn't open any more – nothing was changed." The "gave up" choice was already checked (Give Up Plan).
LAUNCH SWITCH: Build Change C carries DEV_REDIRECT ('' at launch). Built on workflows/imported/slack-interactions-v37-imported.json.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v37-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v38.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]
L = lambda a: {"main": [[{"node": a, "type": "main", "index": 0}]]}
assert C["Answer Cleared"]["main"][0][0]["node"] == "Cleared Move?" and C["Read Requests C"]["main"][0][0]["node"] == "Give Up Plan"
C["Answer Cleared"] = L("Read Requests C")
C["Read Requests C"] = L("Cleared Move?")
C["Cleared Move?"] = {"main": [[{"node": "Read Cache C", "type": "main", "index": 0}], [{"node": "Give Up Plan", "type": "main", "index": 0}]]}
by["Read Cache C"]["executeOnce"] = True
x, y = by["Cleared Move?"]["position"]
by["Read Requests C"]["position"], by["Cleared Move?"]["position"] = [x, y], [x + 240, y]
js = by["Build Change C"]["parameters"]["jsCode"]
a = "let b = Object.assign({}, RC.inc || {});"
assert js.count(a) == 1
js = js.replace(a, a + r"""
// v38: only an open request, and only its requester (or Howard while testing) - a request kept, withdrawn or done opens nothing
// LAUNCH SWITCH: '' at launch.
const DEV_REDIRECT = 'U08V3CKDGJF';
const _row = $('Read Requests C').all().map(i => i.json || {}).find(r => r['Request ID'] && String(r['Request ID']) === String(RC.rid || ''));
if (!_row || String(_row['Status'] || '').toUpperCase() !== 'PENDING' || !(c.user === String(_row['Requester'] || '') || (DEV_REDIRECT && c.user === DEV_REDIRECT)))
  return [{ json: { view_id: RC.viewId, view: { type: 'modal', title: { type: 'plain_text', text: 'Change booking' }, close: { type: 'plain_text', text: 'Close' },
    blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'That request isn’t open any more – nothing was changed.' } }] } } }];""")
by["Build Change C"]["parameters"]["jsCode"] = js
wf["name"] = "Jessie — Slack Interactions — v38 (cleared: the request checked)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
