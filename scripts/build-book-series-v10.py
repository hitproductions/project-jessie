#!/usr/bin/env python3
"""Builds workflows/book-series-v10.json - Jessie — Book Series — v10 (v9 fixed), 4 Nov.

Howard's Slack test of v9 (~14:40): Mon 9 Nov, Studio 6 taken 9 AM - 10 PM -> the review offered "10:00 PM – 12:00 AM (later)".
That option ends at 24:00, which is not a time - booked, that date would have failed. The later option now ends at 11:59 PM at the
latest (Jessie's end of day, as the form's time lists): "10:00 PM – 11:59 PM (later)". Nothing else changes.
Built on workflows/imported/book-series-v9-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "book-series-v9-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


p = by["Aggregate"]["parameters"]
js = p["jsCode"]
js = sub(js, "      if (after !== null) opts.push({ v: 'b', start: mHM(after), end: mHM(after + dur), rooms: B.join(', '), label: t12(after) + ' – ' + t12(after + dur) + ' (later)' });",
    "      // v10 (v9 fixed): never past 11:59 PM - a slot to midnight ended at \"24:00\", which is not a time\n"
    "      if (after !== null) { const ae = Math.min(after + dur, 1439); opts.push({ v: 'b', start: mHM(after), end: mHM(ae), rooms: B.join(', '), label: t12(after) + ' – ' + t12(ae) + ' (later)' }); }")
js = sub(js, "      if (before !== null) opts.push({ v: 'a', start: mHM(before), end: mHM(before + dur), rooms: B.join(', '), label: t12(before) + ' – ' + t12(before + dur) + ' (earlier)' });",
    "      if (before !== null) { const be = Math.min(before + dur, 1439); opts.push({ v: 'a', start: mHM(before), end: mHM(be), rooms: B.join(', '), label: t12(before) + ' – ' + t12(be) + ' (earlier)' }); }")
p["jsCode"] = js
wf["name"] = "Jessie — Book Series — v10 (v9 fixed)"
out = os.path.join(ROOT, "workflows", "book-series-v10.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
