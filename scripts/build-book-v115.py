#!/usr/bin/env python3
"""Builds workflows/book-session-v115.json - "Jessie — Book Session", v115 (project code to Log Booking), round 12 item 8 (20 Oct).

Build Log Row adds a third row, `project`, for a Localization / QC booking (session type starting "Localization" or "QC" -
Slack Interactions' typeKind 'loc'): the project code is the title's first segment ("NET-MALAS / JT"). The Log Booking call
passes it on; Log Booking v2 checks it against Airtable Localization Projects after the reply and writes a New Projects row
(For Review) when the table does not have it. Any other booking: project '' (nothing looked up).
Built on workflows/imported/book-session-v114-imported.json (the live download). Import Log Booking v2 first (it takes the
new input), then this.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "book-session-v114-imported.json")
OUT = os.path.join(ROOT, "workflows", "book-session-v115.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:100], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


patch("Build Log Row", [(
    "return [{ json: { log: JSON.stringify(log), client: client && client['Client'] ? JSON.stringify(client) : '' } }];",
    "// v115 (round 12): a Localization / QC booking's project code (the title's first segment), for Log Booking to check against\n"
    "// Airtable Localization Projects after the reply - a code it does not know goes to the New Projects tab (For Review)\n"
    "let project = null;\n"
    "if (/^(localization|qc)\\b/i.test(String(REQ.session_type || '').trim())) {\n"
    "  const code = String(String(CC.final_summary || V.title || REQ.summary || '').split(' / ')[0] || '').trim().toUpperCase();\n"
    "  if (code) project = { 'Code': code, 'Status': 'For Review', 'Booked by': booker, 'Session Type': String(REQ.session_type || ''),\n"
    "    'Department': String(REQ.department || ''), 'Booking Date': (CC.final_start || REQ.start_iso) ? manila(CC.final_start || REQ.start_iso).slice(0, 10) : '',\n"
    "    'Room(s)': rooms, 'Calendar Title': String(V.title || REQ.summary || ''), 'Event ID': String(V.event_id || ''), 'Added': manila() };\n"
    "}\n"
    "return [{ json: { log: JSON.stringify(log), client: client && client['Client'] ? JSON.stringify(client) : '', project: project ? JSON.stringify(project) : '' } }];")])

lb = by["Log Booking"]["parameters"]["workflowInputs"]
assert set(lb["value"]) == {"log", "client"}, lb["value"]
lb["value"]["project"] = "={{ $json.project }}"

wf["name"] = "Jessie — Book Session — v115 (project code to Log Booking)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
