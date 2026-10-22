#!/usr/bin/env python3
"""Builds the QA-roster change, 22 Oct: only Howard and Camy test now (Howard: "tara and genzo aren't in the testing group
anymore. just me and camy. tel isn't included anymore either, so please route those notifs to me and camy").

ALLOW (the ids that get their own message while testing) becomes Howard + Camy in every workflow that has it; anyone else's
message keeps going to Howard (DEV_REDIRECT), marked who it is for. Nothing else changes; the launch flip is unchanged
(DEV_REDIRECT = '' -> everyone gets their own, ALLOW no longer matters).
  - Slack Interactions v41 (Booked / Series / Change Notices)   <- workflows/imported/slack-interactions-v40-imported.json
  - Jessie — Reminders v5 (Build Reminders)                     <- reminders-v4-imported.json
  - Jessie — Request Messages v3 (Render)                       <- request-messages-v2-imported.json
  - Cancel Booking v29, Move Booking v35 (Build Recipients)     <- cancel-booking-v28 / move-booking-v34-imported.json
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OLD = "['U08V3CKDGJF','U098UFMKQHZ','U08JL17A50A','U0B4S0EKSAY','U098UFLG70B','U026N6E1R','U045A3VQER3']"
NEW = "['U08V3CKDGJF','U08JL17A50A']"
NOTES = [
    ("   // Howard, Trish, Camy, Jess, Tel, Tara, Genzo", "   // Howard, Camy (QA roster since 22 Oct)"),
    (" /* QA round 2 2026-09-24: Howard,Trish,Camy,Jess,Tel,Tara,Genzo. Launch bypass = DEV_REDIRECT='' (ALLOW then moot). */",
     " /* QA roster since 22 Oct: Howard, Camy. Launch bypass = DEV_REDIRECT='' (ALLOW then moot). */"),
]
JOBS = [
    ("slack-interactions-v40-imported.json", "slack-interactions-v41.json", "Jessie — Slack Interactions — v41 (QA roster: Howard + Camy)", 3),
    ("reminders-v4-imported.json", "reminders-v5.json", "Jessie — Reminders — v5 (QA roster: Howard + Camy)", 1),
    ("request-messages-v2-imported.json", "request-messages-v3.json", "Jessie — Request Messages — v3 (QA roster: Howard + Camy)", 1),
    ("cancel-booking-v28-imported.json", "cancel-booking-v29.json", "Jessie — Cancel Booking — v29 (QA roster: Howard + Camy)", 1),
    ("move-booking-v34-imported.json", "move-booking-v35.json", "Jessie — Move Booking — v35 (QA roster: Howard + Camy)", 1),
]
for src, out, name, want in JOBS:
    wf = json.load(open(os.path.join(ROOT, "workflows", "imported", src)))
    hits = 0
    for n in wf["nodes"]:
        js = n.get("parameters", {}).get("jsCode")
        if not js or OLD not in js:
            continue
        hits += js.count(OLD)
        js = js.replace(OLD, NEW)
        for a, b in NOTES:
            js = js.replace(a, b)
        n["parameters"]["jsCode"] = js
    assert hits == want, (src, hits)
    assert "U026N6E1R" not in json.dumps(wf["nodes"]), src
    wf["name"] = name
    with open(os.path.join(ROOT, "workflows", out), "w") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote workflows/" + out, "-", hits, "list(s)")
