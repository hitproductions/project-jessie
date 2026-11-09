#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v77.json - Jessie — Slack Interactions — v77 (no link preview), 9 Nov.

Howard, 9 Nov (v76 live, Slack test): the Booked DM showed Slack's own preview of the calendar link under the buttons ("Google
Workspace - Google Calendar - Easier Time Management…"). "is there a way to remove the Google Workspace insert underneath?" Yes: Slack
unfurls a link in a posted message unless the post says not to. v77: DM Booked posts with unfurl_links: false and unfurl_media: false.
Nothing else changes.
Built on workflows/imported/slack-interactions-v76-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v76-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}
p = by["DM Booked"]["parameters"]
OLD = "blocks: $('After Book').first().json.blocks })"
assert p["jsonBody"].count(OLD) == 1
p["jsonBody"] = p["jsonBody"].replace(OLD, "blocks: $('After Book').first().json.blocks, unfurl_links: false, unfurl_media: false })")
wf["name"] = "Jessie — Slack Interactions — v77 (no link preview)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v77.json")
with open(out, "w") as fh:
    json.dump(wf, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
