#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v68.json - Jessie — Slack Interactions — v68 (skip step 1), 4 Nov.

PENDING 152 (the Localization feedback, exploratory; Howard: "go ahead with skip step 1"). A Book a room button that already carries
everything step 1 asks - the date, a start and an end time (or all day for an M booth / an Event) and the booking type, and no
Repeats - goes straight to the free rooms: the typed request's offer, a skipped series date's Find another time, a "Not booked yet"
DM. It is the Continue booking path (v45): Read Step 1 builds the booking from the button and the step-2 window opens on its own.
That window has "Change date or time" at the top: it swaps the window for step 1, filled in as the button was (Build Step 1 ->
Open Step 1 by views.update, the same window). Anything incomplete, a series, or the menu's Book a room: step 1, as before.
Built on workflows/imported/slack-interactions-v67-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v67-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:160])
    return js.replace(a, b)


def code(name, f):
    p = by[name]["parameters"]
    p["jsCode"] = f(p["jsCode"])


COMPLETE = r"""// v68 (PENDING 152): a Book a room button carrying everything step 1 asks (date, start + end or all day, booking type; no Repeats)
function __stepOneDone(value) {
  let g = null; try { g = JSON.parse(String(value || '')); } catch (e) { return false; }
  if (!g || typeof g !== 'object' || g.rep) return false;
  const p = String(g.p || ''), hm = x => /^([01]\d|2[0-3]):[0-5]\d$/.test(String(x || ''));
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(g.d || '')) || !p) return false;
  if (g.ad && (p === '__booth' || p === 'Event')) return true;
  return hm(g.s) && hm(g.e) && String(g.e) > String(g.s);
}
"""
code("Check Signature", lambda js: COMPLETE + sub(js,
    "else if (p.type === 'block_actions' && (action === 'open_book' || action === 'cr_pick')) route = ROUTES.open_book;   // v37: Pick another room",
    "else if (p.type === 'block_actions' && action === 'open_book' && __stepOneDone(((p.actions || [])[0] || {}).value)) route = ROUTES.book_step1;   // v68: straight to the free rooms\n"
    "else if (p.type === 'block_actions' && (action === 'open_book' || action === 'cr_pick' || action === 'step1_back')) route = ROUTES.open_book;   // v37: Pick another room; v68: Change date or time"))

code("Read Step 1", lambda js: sub(sub(js,
    "  if (p.type === 'block_actions' && _a.action_id === 'book_continue') {",
    "  if (p.type === 'block_actions' && (_a.action_id === 'book_continue' || _a.action_id === 'open_book')) {   // v68: a complete Book a room too (Check Signature)"),
    "    if (allDay) s.allDay = true;\n    const ch = (p.container",
    "    if (allDay) s.allDay = true;\n    s.skip = 1;   // v68: step 1 was skipped - step 2 offers Change date or time\n    const ch = (p.container"))

code("Build Step 2", lambda js: sub(js, "pickedLines(blocks, null, null);   // v64\n",
    "// v68 (PENDING 152): step 1 was skipped (a complete Book a room, or Continue booking) - a way back to it, filled in as it was\n"
    "if (s.skip) { const g = Object.assign({}, pre, { d: s.date, s: s.allDay ? '' : s.t0, e: s.allDay ? '' : s.t1, ad: s.allDay ? 1 : 0, p: s.kind === 'booth' ? '__booth' : s.purpose });\n"
    "  Object.keys(g).forEach(k => { if (!g[k]) delete g[k]; }); let gv = JSON.stringify(g); if (gv.length > 1900) { delete g.nt; gv = JSON.stringify(g); }\n"
    "  if (gv.length <= 1900) blocks.splice(2, 0, { type: 'actions', block_id: 'step1_back', elements: [{ type: 'button', action_id: 'step1_back', value: gv,\n"
    "    text: { type: 'plain_text', text: 'Change date or time' } }] }); }\n"
    "pickedLines(blocks, null, null);   // v64\n"))

code("Build Step 1", lambda js: sub(js, "return [{ json: { trigger_id: c.triggerId, view, cacheOk: !!data } }];",
    "// v68: Change date or time (a button in step 2's window) - step 1 replaces that window instead of opening a new one\n"
    "let _vid = ''; try { const _P = $('Read Request').first().json.payload || {}; if (((_P.actions || [])[0] || {}).action_id === 'step1_back' && _P.view && _P.view.id) _vid = _P.view.id; } catch (e) { _vid = ''; }\n"
    "return [{ json: Object.assign({ trigger_id: c.triggerId, view, cacheOk: !!data }, _vid ? { view_id: _vid } : {}) }];"))

o1 = by["Open Step 1"]["parameters"]
assert o1["url"] == "https://slack.com/api/views.open"
o1["url"] = "={{ $json.view_id ? 'https://slack.com/api/views.update' : 'https://slack.com/api/views.open' }}"
assert o1["jsonBody"] == "={{ JSON.stringify({ trigger_id: $json.trigger_id, view: $json.view }) }}"
o1["jsonBody"] = "={{ JSON.stringify($json.view_id ? { view_id: $json.view_id, view: $json.view } : { trigger_id: $json.trigger_id, view: $json.view }) }}"

wf["name"] = "Jessie — Slack Interactions — v68 (skip step 1)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v68.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
