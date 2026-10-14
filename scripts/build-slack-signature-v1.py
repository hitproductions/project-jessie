#!/usr/bin/env python3
"""Builds workflows/slack-signature-v1.json - "Jessie — Slack Signature": the one place the Slack signing secret lives.

Slack Interactions (and any later Slack-app workflow) calls it with the string to sign; it returns only the computed
HMAC-SHA256, so the secret never leaves this workflow and never appears in another workflow's saved executions. Its own
executions are not saved. It is imported once, the secret pasted once into its "Sign" node, and it is never re-imported -
so new builds of Slack Interactions need no paste step. (Decided 14 Oct: an n8n environment variable needs IT; this is
the do-it-yourself version.)
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "workflows", "slack-signature-v1.json")

wf = {
    "name": "Jessie — Slack Signature — v1",
    "nodes": [
        {"id": "sig-trigger", "name": "When Executed by Another Workflow", "type": "n8n-nodes-base.executeWorkflowTrigger",
         "typeVersion": 1.1, "position": [0, 0], "parameters": {"workflowInputs": {"values": [{"name": "base"}]}}},
        {"id": "sig-sign", "name": "Sign", "type": "n8n-nodes-base.crypto", "typeVersion": 1, "position": [240, 0],
         "parameters": {"action": "hmac", "type": "SHA256", "value": "={{ $json.base }}", "dataPropertyName": "computed",
                        "secret": "PASTE-THE-SLACK-SIGNING-SECRET-HERE", "encoding": "hex"}},
        {"id": "sig-out", "name": "Signature Only", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [480, 0],
         "parameters": {"jsCode": "// Return only the computed signature - never the input or the secret.\n"
                                  "return [{ json: { computed: String($input.first().json.computed || '') } }];"}},
        {"id": "sig-note", "name": "About", "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [-40, -300],
         "parameters": {"width": 460, "height": 240,
                        "content": "## Holds the Slack signing secret\nPaste it once into **Sign** (Secret). Never re-import this "
                                   "workflow - a re-import erases the secret.\n\nCalled by Jessie — Slack Interactions with the string "
                                   "to sign; returns only the signature. Executions are not saved, so the secret never lands in a log."}},
    ],
    "connections": {
        "When Executed by Another Workflow": {"main": [[{"node": "Sign", "type": "main", "index": 0}]]},
        "Sign": {"main": [[{"node": "Signature Only", "type": "main", "index": 0}]]},
    },
    "settings": {"executionOrder": "v1", "saveDataSuccessExecution": "none", "saveDataErrorExecution": "none",
                 "saveManualExecutions": False, "callerPolicy": "workflowsFromSameOwner"},
    "pinData": {}, "active": False,
}
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT))
