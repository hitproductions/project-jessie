#!/usr/bin/env python3
"""Builds workflows/reminders-v11.json - Jessie — Reminders — v11 (hand-made bookings), 19 Nov (PENDING 155 follow-up).

Since 19 Nov a booking made by hand in Google Calendar belongs to whoever made it (the event's creator is one of their Bookers
emails, Email / Alt email): My bookings lists it, Cancel / Change accept it. Reminders still skipped every event without a `ref:`
("only bookings made through Jessie"), so those bookings got no 4 PM / Monday reminder. Build Reminders now also sends one to the
event's creator when that is one of a booker's emails - with or without a `ref:` (the same people My bookings shows it to).
Built on workflows/reminders-v10.json (== live).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "reminders-v10.json")))
by = {n["name"]: n for n in wf["nodes"]}
p = by["Build Reminders"]["parameters"]


def rep(old, new):
    assert p["jsCode"].count(old) == 1, (old[:70], p["jsCode"].count(old))
    p["jsCode"] = p["jsCode"].replace(old, new)


rep("  if (!ref) continue;   // only bookings made through Jessie\n",
    "  // v11 (PENDING 155): a booking made by hand belongs to its creator - one of a booker's emails (Email / Alt email)\n"
    "  const _cr = String((e.creator && e.creator.email) || '').trim().toLowerCase();\n"
    "  const _crF = _cr ? staff.find(f => [f.Email, f['Alt email']].some(x => String(x || '').trim().toLowerCase() === _cr)) : null;\n"
    "  const byCreator = _crF ? idOf(_crF) : '';\n"
    "  if (!ref && !byCreator) continue;   // made through Jessie, or by hand by a booker\n")
rep("  for (const id of [...new Set([ref].concat(team, named))]) {",
    "  for (const id of [...new Set([ref, byCreator].filter(Boolean).concat(team, named))]) {")   # v11: and its creator
wf["name"] = "Jessie — Reminders — v11 (hand-made bookings)"
out = os.path.join(ROOT, "workflows", "reminders-v11.json")
with open(out, "w") as fh:
    json.dump(wf, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
