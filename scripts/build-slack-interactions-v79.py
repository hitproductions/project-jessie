#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v79.json - Jessie — Slack Interactions — v79 (booths not free), 9 Nov.

Howard, 9 Nov (Book a room, Localization Dubbing): "let's add 'Not free then:' under vocal booths as well." The studios list already
says which usual studios are taken ("Not free then: Studio 1, Studio 6"); the Vocal booths multi-select listed only the free booths,
so a taken booth was simply missing. Now the field's hint (the grey line under it) names the vocal booths taken then
("Not free then: Studio A, Studio D"), on a series those taken on any of the dates. No line when every booth is free; the
"No vocal booth is free then" line is unchanged.
- Build Step 2: BX (kept in the form's metadata as bx) gains `nf` (not free) - every vocal booth Room Availability has busy.
- boothBlocks (Build Step 1, Build Step 2, Note Toggle - the same function in each): the input gets `hint` from BX.nf. Note Toggle
  redraws the booths from the metadata's bx when the studio changes, so the line follows.
Built on workflows/slack-interactions-v78.json (== the v78 live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "slack-interactions-v78.json")))
by = {n["name"]: n for n in wf["nodes"]}

RET = "return [Object.assign({ type: 'input', block_id: bid, label: pt('Vocal booths'), element: el }, BX.need ? {} : { optional: true })];"
RET_NEW = ("return [Object.assign({ type: 'input', block_id: bid, label: pt('Vocal booths'), element: el }, BX.need ? {} : { optional: true },\n"
           "    [].concat(BX.nf || []).length ? { hint: pt('Not free then: ' + [].concat(BX.nf).join(', ')) } : {})];   // v79 (Howard): the taken booths named")
for name in ["Build Step 1", "Build Step 2", "Note Toggle"]:
    p = by[name]["parameters"]
    assert p["jsCode"].count(RET) == 1, (name, p["jsCode"].count(RET))
    p["jsCode"] = p["jsCode"].replace(RET, RET_NEW)

BX = "const BX = (needBooth || offerBooth) && ra.status === 'OK' ? { need: needBooth, list: vbooths, pair: {} } : null;"
BX_NEW = ("const BX = (needBooth || offerBooth) && ra.status === 'OK' ? { need: needBooth, list: vbooths, pair: {},\n"
          "  nf: allVB.filter(n => busyAny.has(n)).sort(_num) } : null;   // v79: the vocal booths taken then (on any date of a series)")
p = by["Build Step 2"]["parameters"]
assert p["jsCode"].count(BX) == 1
p["jsCode"] = p["jsCode"].replace(BX, BX_NEW)

wf["name"] = "Jessie — Slack Interactions — v79 (booths not free)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v79.json")
with open(out, "w") as fh:
    json.dump(wf, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
