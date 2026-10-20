#!/usr/bin/env python3
"""Builds workflows/book-session-v116.json - "Jessie — Book Session", v116 (no client lookups without a client), 20 Oct.

Found 20 Oct 20:36 (execution 52774, a Localization Dubbing booking from the form): Client Aliases - an Airtable search - waited
2 min 9 s on a connection that never answered ("The connection to the server was closed unexpectedly"), then carried on; the
booking took 2 min 12 s instead of ~18 s. The booking had no client: Get Client and Client Aliases each asked Airtable a
question that could only come back empty (their formulas are FALSE() without a client).

Client Cache now answers "use" - the three Airtable client reads are skipped, exactly as for a booking run that reuses its
prepare run's lookups (v112) - when there is nothing to look up:
  - a booking type with no client (Howard, 20 Oct): Localization / QC (the project code is all they need), Post Processing,
    Meeting, Event, an M booth (no session type, room M1-M8) - whoever it is for, or
  - no client named (the client input, or the title's Client part) and not booked for someone ("(for X)").
Then gc / al / an are empty lists, which every reader already handles (Check Conflicts through the cache switch, Render Summary
and Prepared Out in try). A booking with a client still looks it up.
Built on workflows/imported/book-session-v115-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "book-session-v115-imported.json")
OUT = os.path.join(ROOT, "workflows", "book-session-v116.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:100], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


patch("Client Cache", [(
    "return [{ json: use ? { use: true, gc: c.gc, al: c.al || [], an: c.an || null } : { use: false } }];",
    "// v116 (20 Oct): nothing to look up -> skip the three Airtable client reads, as for a cached run (gc / al / an empty). Booking\n"
    "// types with no client (Howard, 20 Oct): Localization / QC (the project code is all they need), Post Processing, meetings,\n"
    "// events, M booths; and any booking with no client named that is not booked for someone. Their lookups could only come back\n"
    "// empty - and on 20 Oct 20:36 Client Aliases hung 2 min 9 s on a Localization Dubbing booking.\n"
    "const _sum = String(REQ.summary || '');\n"
    "const _cl = String(REQ.client || '').replace(/\\s*\\([^()]*\\)\\s*$/, '').trim()\n"
    "  || (_sum.split('/').length >= 3 ? _sum.split('/')[1].trim() : '') || (_sum.split(' / ').length >= 3 ? _sum.split(' / ')[1].trim() : '');\n"
    "const _st = String(REQ.session_type || '').trim(), _rm = String(REQ.rooms || '').trim();\n"
    "const _noClientType = /^(localization|qc|post processing|meeting|event)\\b/i.test(_st) || (!_st && /^M\\d+$/i.test(_rm));   // + M booths (no type)\n"
    "const _for = /\\(for\\s+[^)]+\\)/i.test(String(REQ.description || ''));\n"
    "if (!use && (_noClientType || (!_cl && !_for))) return [{ json: { use: true, gc: [], al: [], an: [], none: true } }];\n"
    "return [{ json: use ? { use: true, gc: c.gc, al: c.al || [], an: c.an || null } : { use: false } }];")])

wf["name"] = "Jessie — Book Session — v116 (no client lookups without a client)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
