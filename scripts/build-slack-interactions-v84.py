#!/usr/bin/env python3
"""Slack Interactions v84 (Howard, 20 Nov): the Other guests (emails) hint reads
"For guests outside Hit. They get the GCal invite. Separate emails with commas." Built on v83 (== live)."""
import json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
w = json.load(open(os.path.join(ROOT, "workflows", "slack-interactions-v83.json")))
n = [x for x in w["nodes"] if x["name"] == "Build Step 2"][0]
old = "'Anyone else, inside or outside Hit. Separate emails with commas. They get the Google Calendar invite.'"
new = "'For guests outside Hit. They get the GCal invite. Separate emails with commas.'   /* v84 (Howard) */"
c = n["parameters"]["jsCode"]; assert c.count(old) == 1
n["parameters"]["jsCode"] = c.replace(old, new)
w["name"] = "Jessie — Slack Interactions — v84 (outside guests hint)"
with open(os.path.join(ROOT, "workflows", "slack-interactions-v84.json"), "w") as fh:
    json.dump(w, fh, indent=2, ensure_ascii=False); fh.write("\n")
print("wrote workflows/slack-interactions-v84.json", len(w["nodes"]), "nodes")
