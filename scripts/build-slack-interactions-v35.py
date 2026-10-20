#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v35.json - "Jessie — Slack Interactions", v35 (reminder buttons), 20 Oct.

Jessie — Reminders (new) DMs each booking with Still on / Keep (rm_keep), Change (bk_change) and Free up the room (bk_cancel,
Slack's confirm pop-up) - Change and Cancel are the existing handlers (the rows use the same block ids, bk_<id> / bka_<id>).
New here: rm_keep (route 15) -> Ack Keep -> Keep Row (the row's buttons become "✓ Still on" / "✓ Keeping it") -> Update Kept
(chat.update). Nothing on the calendar changes.
Built on workflows/imported/slack-interactions-v34-imported.json (the live download).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v34-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v35.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:100], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


def copy(name, newname, pos, params=None):
    n = json.loads(json.dumps(by[name]))
    n.update({"id": str(uuid.uuid4()), "name": newname, "position": pos})
    if "webhookId" in n:
        n["webhookId"] = str(uuid.uuid4())
    if params is not None:
        n["parameters"] = params
    wf["nodes"].append(n)
    by[newname] = n
    return n


patch("Check Signature", [
    ("my_page: 12, series_confirm: 13, suggest: 14 }", "my_page: 12, series_confirm: 13, suggest: 14, rm_keep: 15 }"),
    ("else if (p.type === 'block_actions' && action === 'bk_change') route = ROUTES.bk_change;\n",
     "else if (p.type === 'block_actions' && action === 'bk_change') route = ROUTES.bk_change;\n"
     "else if (p.type === 'block_actions' && action === 'rm_keep') route = ROUTES.rm_keep;   // v35: a reminder's Still on / Keep\n"),
])
by["Route"]["parameters"]["numberOutputs"] = 16
x, y = by["Ack Cancel"]["position"]
copy("Ack Cancel", "Ack Keep", [x, y + 900])
KEEP = r"""// Keep Row (v35): a reminder's Still on / Keep (Jessie — Reminders) - the row's buttons become a small "✓ Still on" (the day before)
// or "✓ Keeping it" (the weekly message). Nothing on the calendar changes.
const p = $('Read Request').first().json.payload || {};
const a = (p.actions || [])[0] || {};
let v = {}; try { v = JSON.parse(a.value || '{}'); } catch (e) { v = { id: String(a.value || '') }; }
const id = String(v.id || '');
const msg = p.message || {}, ch = (p.container && p.container.channel_id) || (p.channel && p.channel.id) || '', ts = (p.container && p.container.message_ts) || msg.ts || '';
if (!id || !ch || !ts || !Array.isArray(msg.blocks)) return [];
const done = { type: 'context', block_id: 'bkd_' + id, elements: [{ type: 'mrkdwn', text: v.w === 'weekly' ? '✓ Keeping it' : '✓ Still on' }] };
const blocks = msg.blocks.map(b => b.block_id === 'bka_' + id ? done : b);
return [{ json: { channel: ch, ts, text: msg.text || 'Your bookings', blocks } }];"""
copy("Read Step 2", "Keep Row", [x + 224, y + 900], {"jsCode": KEEP})
by["Keep Row"].pop("onError", None)
copy("Update Source", "Update Kept", [x + 448, y + 900])
while len(C["Route"]["main"]) < 16:
    C["Route"]["main"].append([])
C["Route"]["main"][15] = [{"node": "Ack Keep", "type": "main", "index": 0}]
C["Ack Keep"] = {"main": [[{"node": "Keep Row", "type": "main", "index": 0}]]}
C["Keep Row"] = {"main": [[{"node": "Update Kept", "type": "main", "index": 0}]]}
C.pop("Update Kept", None)
# Howard, 20 Oct ~23:00: a Band Recording when Studio F and Studio C (its usual rooms) were both taken -> "Nothing that does Band
# Recording is free then", although other studios were free (they show under Choose a different room only when a usual room is
# free; its Last Resort rooms are conference rooms, which the studio list leaves out). Now the other free rooms of its kind are
# offered: "Available rooms:" + why, the first 6 to pick, the rest under Choose a different room - booked as asked (nu).
patch("Build Step 2", [
    ("const others = ra.status === 'OK' && !ONLY ? (data.rooms || [])", "let others = ra.status === 'OK' && !ONLY ? (data.rooms || [])"),
    ("if (!rooms.length) {\n",
     "// v35: none of the type's rooms is free -> the other free rooms of its kind, not a dead end (\"Available rooms:\" + why below)\n"
     "if (!rooms.length && others.length && s.kind !== 'booth' && !ONLY) { rooms = others.slice(0, 6).map(n => opt(n, n)); rooms.forEach(o => nu.push(o.value)); others = others.slice(6); }\n"
     "if (!rooms.length) {\n"),
])
wf["name"] = "Jessie — Slack Interactions — v35 (reminder buttons, other rooms)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
