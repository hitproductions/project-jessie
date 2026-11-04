#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v65.json - Jessie — Slack Interactions — v65 (taken booths said), 4 Nov.

Howard's Slack test of v64 / main v289, 4 Nov ~1:45 PM: "book studios a and 1 for tomorrow 2-4pm" -> step 2 said only "Studio 1 is
taken then", and Studio A was simply missing from Vocal booths (a booking 11 AM - 5 PM holds Studio 1 + Studio A). Step 2 leaves
taken rooms out of its lists, and only the room (pre.r) had a line. Now every room typed with it (its vocal booths, pre.bo, and its
other studios, pre.mr) that is taken is named on the same line: "Studio 1 and Studio A are taken then. These are free:", or, with the
room free, "Studio A is taken then." Nothing else changes.
Built on workflows/imported/slack-interactions-v64-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v64-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


p = by["Build Step 2"]["parameters"]
p["jsCode"] = sub(p["jsCode"],
    "  else preNote = pre.r + ' isn’t a room for ' + label + '.';\n  if (preNote && rooms.length) preNote += ' These are free:';\n}",
    "  else preNote = pre.r + ' isn’t a room for ' + label + '.';\n"
    "  // v65 (Howard's Slack test, 4 Nov): the booths / studios typed with it that are taken are named too - they were left out of the\n"
    "  // lists without a word (\"studios a and 1\": only \"Studio 1 is taken then\", Studio A missing from Vocal booths)\n"
    "  const _tk = [].concat(String(pre.bo || '').split(','), String(pre.mr || '').split(',')).map(x => x.trim())\n"
    "    .filter((n, i, a) => n && n !== pre.r && a.indexOf(n) === i && busyAny.has(n));\n"
    "  if (_tk.length) { const _and = a => a.length <= 1 ? a.join('') : a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1];\n"
    "    if (busyAny.has(pre.r)) preNote = _and([pre.r].concat(_tk)) + ' are taken then.';\n"
    "    else preNote = (preNote ? preNote + ' ' : '') + _and(_tk) + (_tk.length > 1 ? ' are' : ' is') + ' taken then.'; }\n"
    "  if (preNote && rooms.length && !preRoom) preNote += ' These are free:';\n}")

wf["name"] = "Jessie — Slack Interactions — v65 (taken booths said)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v65.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
