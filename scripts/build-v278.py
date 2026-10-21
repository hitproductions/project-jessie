#!/usr/bin/env python3
"""Builds workflows/project-jessie-v278.json - main "Project Jessie", v278 (typed replies leave button requests alone), 21 Oct.

Pre-QA review (21 Oct): the typed Consent Router (consent engine, Sep) matched ANY pending request whose Approver is the person
typing. Since Open Consent Request v12 (slice 2, live 21 Oct ~17:10) the row holds the real approver, so a typed DM from them -
"ok thanks", "sure, is studio 7 free?", "no client" - was read as their answer: on a shared M booth "ok…" booked the requester
and deleted the holder's hold that day; "no…" rejected any request and DM'd the requester directly (no QA redirect); a priority
request's booker got the old "CONSENT CONTEXT" in the model's prompt. Requests made with buttons (they carry the row's Messages)
are answered only by their buttons now; the typed path stays for any request from before slice 2.
Built on workflows/imported/project-jessie-v277-imported.json (the live download). Only Consent Router changes.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v277-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v278.json")
wf = json.load(open(SRC))
n = next(x for x in wf["nodes"] if x["name"] == "Consent Router")
js = n["parameters"]["jsCode"]
a = "if(String(r['Approver']||'')!==s) continue;"
assert js.count(a) == 1, js.count(a)
js = js.replace(a, a + " if(String(r['Messages']||'').trim()) continue; /* v278: a request with buttons (slice 2) - answered by its buttons only */")
n["parameters"]["jsCode"] = js
wf["name"] = "Project Jessie — v278 (typed replies leave button requests alone)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT))
