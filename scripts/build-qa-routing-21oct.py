#!/usr/bin/env python3
"""Builds workflows/request-messages-v2.json and workflows/reminders-v4.json - "QA testers get their own" (21 Oct).

Howard, 21 Oct (QA on 22 Oct, Camy testing): room-request messages and reminders go to the people on the QA roster (ALLOW) the way
they will at launch - Camy gets hers, Howard his - and everyone else's still come to Howard, marked "Test: this is for X". One
message, one recipient: nothing is duplicated. ALL_TO_DEV true -> false in Request Messages (Render) and Reminders (Build
Reminders); still inert at launch (DEV_REDIRECT ''). Built on the live downloads; only those two lines change.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for src, out, node, name in (("request-messages-v1-imported.json", "request-messages-v2.json", "Render", "Jessie — Request Messages — v2 (QA testers get their own)"),
                             ("reminders-v3-imported.json", "reminders-v4.json", "Build Reminders", "Jessie — Reminders — v4 (QA testers get their own)")):
    wf = json.load(open(os.path.join(ROOT, "workflows", "imported", src)))
    n = next(x for x in wf["nodes"] if x["name"] == node)
    js = n["parameters"]["jsCode"]
    assert js.count("const ALL_TO_DEV = true;") == 1, src
    n["parameters"]["jsCode"] = js.replace("const ALL_TO_DEV = true;",
        "const ALL_TO_DEV = false;   // 21 Oct (QA, Camy testing): the QA roster (ALLOW) gets its own; everyone else still to DEV_REDIRECT")
    wf["name"] = name
    with open(os.path.join(ROOT, "workflows", out), "w") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote workflows/" + out)
