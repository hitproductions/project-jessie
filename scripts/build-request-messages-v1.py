#!/usr/bin/env python3
"""Builds workflows/request-messages-v1.json - "Jessie — Request Messages", v1 (new, slice 2, 21 Oct).

Every message of a room request (a priority request or a shared M booth), written in one place
(docs/design/slice-2-approvals.md):
  - mode "open"  (Open Consent Request v12): the requester's card - ⏳ Requested, with I've cleared it with them / Withdraw
    request / Pick another room - and the request itself to the booker and engineer (Move my booking / Give it up / Keep my
    booking) or to the booth's holder (Let them use it / Keep it). Posted; where each went comes back (channel + ts) and is
    kept on the request's row (Messages).
  - mode "end" (Finalize Consent v11, Consent Sweep v3, Slack Interactions v37): every one of those messages updated in place
    to how the request ended - booked (the requester's card becomes the Booked card with Change / Cancel), kept, no answer,
    withdrawn, could not be placed. A request with no stored messages (from before slice 2) gets new ones.
LAUNCH SWITCH in Render: DEV_REDIRECT 'U08V3CKDGJF' -> '' (with ALL_TO_DEV = true every message goes to Howard during QA,
marked "Test: this is for X" - Howard, 21 Oct). scripts/check-launch-switches and flip-launch-switches read it.
Import into a NEW workflow and publish (it is only called, never triggered); then scripts/set-request-messages-id.py <id>.
"""
import json
import os
import uuid

from approvals_js import RENDER_JS, COLLECT_JS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SI = {n["name"]: n for n in json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v36-imported.json")))["nodes"]}
OUT = os.path.join(ROOT, "workflows", "request-messages-v1.json")


def node(name, ntype, ver, params, pos, extra=None):
    n = {"parameters": params, "id": str(uuid.uuid4()), "name": name, "type": ntype, "typeVersion": ver, "position": pos}
    n.update(extra or {})
    return n


send = json.loads(json.dumps(SI["DM Booked"]))
send.update({"id": str(uuid.uuid4()), "name": "Send", "position": [672, 0]})
send["parameters"]["url"] = "={{ $json.op === 'update' ? 'https://slack.com/api/chat.update' : 'https://slack.com/api/chat.postMessage' }}"
send["parameters"]["jsonBody"] = ("={{ JSON.stringify(Object.assign({ channel: $json.channel, text: $json.text, blocks: $json.blocks }, "
                                  "$json.op === 'update' ? { ts: $json.ts } : {})) }}")

nodes = [
    node("When Executed by Another Workflow", "n8n-nodes-base.executeWorkflowTrigger", 1.1,
         {"workflowInputs": {"values": [{"name": "mode"}, {"name": "row"}, {"name": "extra"}]}}, [0, 0]),
    node("Render", "n8n-nodes-base.code", 2, {"jsCode": RENDER_JS}, [336, 0]),
    send,
    node("Collect", "n8n-nodes-base.code", 2, {"jsCode": COLLECT_JS}, [1008, 0]),
    node("Note", "n8n-nodes-base.stickyNote", 1, {"content": (
        "## Jessie — Request Messages\nEvery message of a room request, in one place. **open**: the requester's card + the request "
        "to the booker and engineer (or the booth holder), posted; Collect returns where each went (kept on the row's Messages). "
        "**end**: each of them updated to how the request ended. Called by Open Consent Request, Finalize Consent, Consent Sweep and "
        "Slack Interactions.\n\nLAUNCH SWITCH: DEV_REDIRECT in Render ('' at launch)."), "height": 300, "width": 520}, [0, -360]),
]
conn = {
    "When Executed by Another Workflow": {"main": [[{"node": "Render", "type": "main", "index": 0}]]},
    "Render": {"main": [[{"node": "Send", "type": "main", "index": 0}]]},
    "Send": {"main": [[{"node": "Collect", "type": "main", "index": 0}]]},
}
wf = {"name": "Jessie — Request Messages — v1 (slice 2)", "nodes": nodes, "connections": conn, "pinData": {}, "active": False,
      "settings": {"executionOrder": "v1"}, "meta": {}, "tags": []}
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(nodes), "nodes")
