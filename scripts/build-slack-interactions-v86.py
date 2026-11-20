#!/usr/bin/env python3
"""Slack Interactions v86 (Howard, 20 Nov): picking M booth in step 1 ticks "All day booking" (and the Start / End times go, as when
the box is ticked by hand) - it no longer appears unticked. Untick it to set times. An Event still shows the box unticked.
The ticked box is drawn under a new block_id ("allday_toggle~<ms>"), so a box unticked earlier on the same form (an Event first)
cannot keep its old state (gotcha 47); Read Step 1 and Note Toggle's redraw find the box by its stem. Built on v85 (== live)."""
import json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
w = json.load(open(os.path.join(ROOT, "workflows", "slack-interactions-v85.json")))
def rep(nd, old, new):
    n = [x for x in w["nodes"] if x["name"] == nd][0]; c = n["parameters"]["jsCode"]
    assert c.count(old) == 1, (nd, old[:70], c.count(old)); n["parameters"]["jsCode"] = c.replace(old, new)
rep("Note Toggle",
    "    if (pv === '__booth') blocks.splice(at + 1, 0, JSON.parse(JSON.stringify(ALLDAY_BLOCK)));\n",
    "    if (pv === '__booth') {   // v86 (Howard, 20 Nov): an M booth is all day unless unticked - the box ticked, no Start / End\n"
    "      const _ab = JSON.parse(JSON.stringify(ALLDAY_BLOCK)); _ab.block_id = 'allday_toggle~' + Date.now(); _ab.elements[0].initial_options = _ab.elements[0].options;\n"
    "      blocks.splice(at + 1, 0, _ab);\n"
    "      for (let k = blocks.length - 1; k >= 0; k--) if (blocks[k].block_id === 'start' || blocks[k].block_id === 'end') blocks.splice(k, 1); }\n")
rep("Note Toggle", "const at = blocks.findIndex(b => (which === 'room_radio' || which === 'room_other_pick' ||",
    "const at = blocks.findIndex(b => (which === 'allday_toggle' || which === 'room_radio' || which === 'room_other_pick' ||")   # v86: the box by its stem
rep("Read Step 1",
    "const allDay = !!(v.allday_toggle && v.allday_toggle.allday_toggle && (v.allday_toggle.allday_toggle.selected_options || []).length)",
    "const __adK = Object.keys(v).find(k => k.split('~')[0] === 'allday_toggle');   // v86: \"allday_toggle~<ms>\" when M booth ticked it\n"
    "const allDay = !!(__adK && v[__adK].allday_toggle && (v[__adK].allday_toggle.selected_options || []).length)")
w["name"] = "Jessie — Slack Interactions — v86 (M booth ticks All day)"
with open(os.path.join(ROOT, "workflows", "slack-interactions-v86.json"), "w") as fh:
    json.dump(w, fh, indent=2, ensure_ascii=False); fh.write("\n")
print("wrote workflows/slack-interactions-v86.json", len(w["nodes"]), "nodes")
