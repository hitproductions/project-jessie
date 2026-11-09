#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v78.json - Jessie — Slack Interactions — v78 (🔗 GCal link), 9 Nov.

Howard, 9 Nov: "let's add 🔗 before 'Check your booking in Google Calendar'" -> "🔗 Check your booking in GCal". The Booked card's last
line reads 🔗 then the link "Check your booking in GCal". Includes v77 (no link preview; not imported on its own).
Built on workflows/slack-interactions-v77.json (v77 built on the v76 live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "slack-interactions-v77.json")))
by = {n["name"]: n for n in wf["nodes"]}
p = by["After Book"]["parameters"]
OLD = "'\\n\\n<' + _gl + '|Check your booking in Google Calendar>'"
assert p["jsCode"].count(OLD) == 1, p["jsCode"].count(OLD)
p["jsCode"] = p["jsCode"].replace(OLD, "'\\n\\n🔗 <' + _gl + '|Check your booking in GCal>'   /* v78 (Howard) */")
wf["name"] = "Jessie — Slack Interactions — v78 (🔗 GCal link)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v78.json")
with open(out, "w") as fh:
    json.dump(wf, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
