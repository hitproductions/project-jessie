#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v43.json - Jessie — Slack Interactions v43 (QA fixes: fresh message, title kept), 26 Oct.

QA round 4 (Camy, 22 Oct sheet):
  Z1 - two cancels from one My bookings list, one right after the other: the first ended "❌ Cancelled.", then the second
       redrew the list from the copy Slack sent with its click - taken while the first was still "⏳ Cancelling…" - so the
       first went back to "⏳ Cancelling…" for good (both were deleted from the calendar). Every update of a message a button
       sits in now reads the message as it is first (conversations.history, as the Change flow already did) and changes only
       that booking's rows: Mark Cancelling, After Cancel, Keep Row, and a change that did not go through (Restore Message /
       Restore Asked put back that booking's row only, not the whole message as it was). The click's copy is the fallback
       when the read fails.
  Q3 - "Move my booking" (and Change from My bookings / reminders) opened with the Project title empty for
       "REQUEST-QA / AEG": a two-part title whose first part has a hyphen was read as a Localization project code. Now a
       code only for a Localization / QC booking (or one with no type), a Localization booking's code is filled even without
       a hyphen, and when the type is changed on the form the project and the code carry over to each other.
Built on workflows/imported/slack-interactions-v42-imported.json (the live download).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v42-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v43.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]


def sub(node, a, b, n=1):
    js = by[node]["parameters"]["jsCode"]
    assert js.count(a) == n, (node, js.count(a), a[:80])
    by[node]["parameters"]["jsCode"] = js.replace(a, b)


# ---- Z1: read the message as it is, right before each update
def reader(name, ch_expr, ts_expr, pos):
    tmpl = by["Get Message Before"]
    node = {"parameters": {"url": "=https://slack.com/api/conversations.history?channel={{ encodeURIComponent(" + ch_expr + ") }}&latest={{ encodeURIComponent(" + ts_expr + ") }}&inclusive=true&limit=1",
                           "authentication": "predefinedCredentialType", "nodeCredentialType": "slackApi", "options": {}},
            "type": tmpl["type"], "typeVersion": tmpl["typeVersion"], "position": pos, "id": str(uuid.uuid4()), "name": name,
            "credentials": tmpl["credentials"], "onError": "continueRegularOutput"}
    wf["nodes"].append(node)
    by[name] = node


def between(a, b, new, out=0):
    outs = C[a]["main"][out]
    hit = [i for i, c in enumerate(outs) if c["node"] == b]
    assert len(hit) == 1, (a, b)
    outs[hit[0]] = {"node": new, "type": "main", "index": 0}
    C[new] = {"main": [[{"node": b, "type": "main", "index": 0}]]}


P_CH = "(($('Read Request').first().json.payload || {}).container || {}).channel_id || ((($('Read Request').first().json.payload || {}).channel) || {}).id || ''"
P_TS = "(($('Read Request').first().json.payload || {}).container || {}).message_ts || ''"
M_CH = "($('Mark Changing').first().json || {}).channel || ''"
M_TS = "($('Mark Changing').first().json || {}).ts || ''"
reader("Get Message C", P_CH, P_TS, [143392, 15840]); between("Ack Cancel", "Mark Cancelling", "Get Message C")
reader("Get Message C2", P_CH, P_TS, [144232, 15840]); between("Cancel", "After Cancel", "Get Message C2")
reader("Get Message K", P_CH, P_TS, [143504, 16700]); between("Ack Keep", "Keep Row", "Get Message K")
reader("Get Message R", M_CH, M_TS, [145432, 16200]); between("Moved?", "Restore Message", "Get Message R", out=1)
reader("Get Message RA", M_CH, M_TS, [144712, 16320]); between("Ask Again", "Restore Asked", "Get Message RA")

FRESH = "const _now = ts => (((($input.first() || {}).json || {}).messages) || []).find(x => String(x.ts) === String(ts)) || null;   // v43: the message as it is now (Z1)\n"
sub("Mark Cancelling", "const blocks = processing((p.message || {}).blocks, b.id, 'Cancelling…');",
    FRESH + "const _m = _now((p.container && p.container.message_ts) || '');\n"
    "const blocks = processing(_m ? _m.blocks : (p.message || {}).blocks, b.id, 'Cancelling…');")
sub("Mark Cancelling", "blocks: blocks || [], text: (p.message && p.message.text) || 'Cancelling' } }];",
    "blocks: blocks || [], text: (_m && _m.text) || (p.message && p.message.text) || 'Cancelling' } }];")
sub("After Cancel", "const r = $input.first().json || {};", "let r = {}; try { r = $('Cancel').first().json || {}; } catch (e) { r = ($input.first() || {}).json || {}; }   // v43: the read of the message comes in between")
sub("After Cancel", "const msg = p.message || {};",
    FRESH + "const msg = _now((p.container && p.container.message_ts) || '') || p.message || {};   // v43: not the copy from the click - another booking in it may have changed since")
sub("Keep Row", "const msg = p.message || {}, ch = (p.container && p.container.channel_id) || (p.channel && p.channel.id) || '', ts = (p.container && p.container.message_ts) || msg.ts || '';",
    "const msg0 = p.message || {}, ch = (p.container && p.container.channel_id) || (p.channel && p.channel.id) || '', ts = (p.container && p.container.message_ts) || msg0.ts || '';\n"
    + FRESH + "const msg = _now(ts) || msg0;")
RESTORE = ("// v43 (Z1): put back this booking's rows only, into the message as it is now - another booking in it may have changed since\n"
           "function restoreRow(now, orig, id) {\n"
           "  const mine = x => ['bk_', 'bka_', 'bkw_', 'bkn_'].some(k => x.block_id === k + id);\n"
           "  const at = now.findIndex(mine), back = (orig || []).filter(mine);\n"
           "  if (at === -1 || !back.length) return orig;\n"
           "  const out = now.filter(x => !mine(x)); out.splice(at, 0, ...back); return out; }\n"
           "const _m = (((($input.first() || {}).json || {}).messages) || []).find(x => String(x.ts) === String(M.ts)) || null;\n"
           "let _id = ''; try { _id = String((($('Read Change').first().json || {}).b || {}).id || ''); } catch (e) { _id = ''; }\n")
sub("Restore Message", "return [{ json: { channel: M.channel, ts: M.ts, blocks: M.original, text: M.text } }];",
    RESTORE + "return [{ json: { channel: M.channel, ts: M.ts, blocks: _m && _id ? restoreRow(_m.blocks || [], M.original, _id) : M.original, text: M.text } }];")
sub("Restore Asked", "return [{ json: { channel: M.channel, ts: M.ts, blocks: M.original, text: M.text } }];",
    RESTORE + "return [{ json: { channel: M.channel, ts: M.ts, blocks: _m && _id ? restoreRow(_m.blocks || [], M.original, _id) : M.original, text: M.text } }];")

# ---- Q3: the project title kept (every copy of parseTitle / detBlocks)
REPS = [
    ("  if (segs.length === 2 && /^[A-Z0-9]+(?:-[A-Z0-9]+)+$/.test(segs[0])) return { kind: 'loc', code: segs[0], ei: ini[0] || '', ai: '' };",
     "  // v43 (Q3: \"REQUEST-QA / AEG\" opened Change with no project): a code only for a Localization / QC booking (or one with no type)\n"
     "  const _loc = /^(?:localization|qc)\\b/i.test(String(b.st || ''));\n"
     "  if (segs.length === 2 && (_loc || (!b.st && /^[A-Z0-9]+(?:-[A-Z0-9]+)+$/.test(segs[0])))) return { kind: 'loc', code: segs[0], ei: ini[0] || '', ai: '' };"),
    ("const T = String((vals && vals.st) || b.st || ''), K = typeKind(T) || O.kind;",
     "const T = String((vals && vals.st) || b.st || ''), K = typeKind(T) || O.kind;\n"
     "  // v43: the type changed on the form - the project and the code carry over to each other (nothing to type again)\n"
     "  if (K !== 'loc' && !V.project && O.code && !(vals && 'project' in vals)) V.project = O.code;\n"
     "  if (K === 'loc' && !V.code && O.project && !(vals && 'code' in vals)) V.code = O.project;"),
]
hits = [0] * len(REPS)
for n in wf["nodes"]:
    js = n.get("parameters", {}).get("jsCode")
    if not js:
        continue
    for i, (a, b) in enumerate(REPS):
        c = js.count(a)
        if c:
            js = js.replace(a, b)
            hits[i] += c
    n["parameters"]["jsCode"] = js
print("parseTitle / detBlocks copies:", hits)
assert hits[0] >= 6 and hits[1] >= 6, hits
wf["name"] = "Jessie — Slack Interactions — v43 (fresh message, title kept)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
