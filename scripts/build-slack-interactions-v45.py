#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v45.json - Jessie — Slack Interactions v45 (Continue booking), 27 Oct.

Howard (27 Oct, phone): "i closed the window after step 2 … there was no way to access the pre-filled form again. if i press
book a room it restarts to step one … maybe there should be a 'continue booking' button? this happens if you close the
window". The "Not booked yet" / "Not booked" message (sent when the window was gone - a question, a near-miss client, a taken
room) carried "Book a room", which opens step 1 (filled in) - so it looked like starting over.
  - That message now carries **Continue booking** (+ My bookings): it opens "⏳ Finding free rooms…" at once and then step 2,
    rooms checked again, with everything that was filled in (room, project, client, engineer, arranger, note-less).
  - Read Step 1 takes the click (route 5) and builds the booking from the button instead of step 1's answers; a new IF
    ("Continue?") and views.open ("Open Continue") show the waiting window, then the usual Room Availability -> step 2.
  - Booked from it: that message becomes "Your booking details: … ✅ Booked." (it counts as a source message, like an offer).
  - A repeating booking's message keeps "Book a room" (its dates are not on the button).
Built on workflows/imported/slack-interactions-v44-imported.json (the live download).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v44-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v45.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]


def sub(node, a, b, n=1):
    js = by[node]["parameters"]["jsCode"]
    assert js.count(a) == n, (node, js.count(a), a[:80])
    by[node]["parameters"]["jsCode"] = js.replace(a, b)


# 1. the route: Continue booking goes where step 1's answers go
sub("Check Signature", "else if (p.type === 'block_actions' && (action === 'open_book' || action === 'cr_pick')) route = ROUTES.open_book;",
    "else if (p.type === 'block_actions' && action === 'book_continue') route = ROUTES.book_step1;   // v45: Continue booking - straight to step 2\n"
    "else if (p.type === 'block_actions' && (action === 'open_book' || action === 'cr_pick')) route = ROUTES.open_book;")

# 2. Read Step 1: the booking from the button
sub("Read Step 1", "const p = $('Read Request').first().json.payload || {};",
    """const p = $('Read Request').first().json.payload || {};
// v45 (27 Oct, Howard): "Continue booking" on a "Not booked yet" message (the window was closed) - the booking from the button,
// not from step 1's answers; then the usual Room Availability -> step 2, opened in a new window (Open Continue).
{ const _a = ((p.actions || [])[0]) || {};
  if (p.type === 'block_actions' && _a.action_id === 'book_continue') {
    let g = {}; try { g = JSON.parse(_a.value || '{}') || {}; } catch (e) { g = {}; }
    const purpose = String(g.p || ''), allDay = !!g.ad && (purpose === '__booth' || purpose === 'Event');
    const kind = purpose === '__booth' ? 'booth' : (purpose === 'Meeting' || purpose === 'Event') ? 'meeting'
      : /^(?:localization|qc)\\b/i.test(purpose) ? 'loc' : /^post processing$/i.test(purpose) ? 'post' : 'studio';
    const hmOk = x => /^([01]\\d|2[0-3]):[0-5]\\d$/.test(String(x || ''));
    const s = { date: String(g.d || ''), t0: allDay ? '00:00' : String(g.s || ''), t1: allDay ? '23:59' : String(g.e || ''), purpose, kind,
      requester: c.user, channel: c.channel || c.user || '', ext: 's2-' + (c.user || 'x') + '-' + Date.now(), pre: g };
    if (allDay) s.allDay = true;
    const ch = (p.container && p.container.channel_id) || (p.channel && p.channel.id) || '', ts = (p.container && p.container.message_ts) || '';
    if (ch && ts) s.msg = { ch, ts };   // booked -> that message says so
    const valid = /^\\d{4}-\\d{2}-\\d{2}$/.test(s.date) && !!purpose && hmOk(s.t0) && hmOk(s.t1) && s.t1 > s.t0;
    let _tr2 = []; try { _tr2 = $('Timings 1').all().map(i => i.json || {}); } catch (e) { _tr2 = []; }
    const open = { type: 'modal', external_id: s.ext, callback_id: 'book_step2', title: { type: 'plain_text', text: 'Book a room' }, close: { type: 'plain_text', text: 'Close' },
      private_metadata: JSON.stringify(s), blocks: [{ type: 'section', text: { type: 'mrkdwn', text: '⏳ *Finding free rooms…*' } },
        { type: 'context', elements: [{ type: 'mrkdwn', text: waitLine(_tr2, 'rooms', 1, 10) }] }] };
    return [{ json: { valid, s, cont: true, trigger_id: c.triggerId, open, answer: {} } }];
  }
}""")

# 3. a new IF + views.open between "Step 1 OK?" (true) and "Read Cache 2"
ifn = json.loads(json.dumps(by["Step 1 OK?"]))
ifn["name"] = "Continue?"; ifn["id"] = str(uuid.uuid4()); ifn["position"] = [by["Step 1 OK?"]["position"][0] + 100, by["Step 1 OK?"]["position"][1] + 200]
ifn["parameters"]["conditions"]["conditions"][0]["id"] = str(uuid.uuid4())
ifn["parameters"]["conditions"]["conditions"][0]["leftValue"] = "={{ $('Read Step 1').first().json.cont === true }}"
op = json.loads(json.dumps(by["Show Step 2"]))
op["name"] = "Open Continue"; op["id"] = str(uuid.uuid4()); op["position"] = [ifn["position"][0] + 200, ifn["position"][1] + 100]
op["parameters"]["url"] = "https://slack.com/api/views.open"
op["parameters"]["jsonBody"] = "={{ JSON.stringify({ trigger_id: $('Read Step 1').first().json.trigger_id, view: $('Read Step 1').first().json.open }) }}"
wf["nodes"] += [ifn, op]
outs = C["Step 1 OK?"]["main"][0]
assert [x["node"] for x in outs] == ["Read Cache 2"], outs
C["Step 1 OK?"]["main"][0] = [{"node": "Continue?", "type": "main", "index": 0}]
C["Continue?"] = {"main": [[{"node": "Open Continue", "type": "main", "index": 0}], [{"node": "Read Cache 2", "type": "main", "index": 0}]]}
C["Open Continue"] = {"main": [[{"node": "Read Cache 2", "type": "main", "index": 0}]]}

# 4. the "Not booked yet" / "Not booked" messages: Continue booking
OLD_BTN = "const bookBtn = (R) => ({ type: 'actions', elements: [{ type: 'button', style: 'primary', action_id: 'open_book', value: again(R), text: { type: 'plain_text', text: 'Book a room' } },"
NEW_BTN = ("// v45 (27 Oct): Continue booking - step 2 again with what was filled in (rooms checked again); Book a room only when the answers are not on it\n"
           "const _cont = R => { const g = (R && R.again) || {}; return !!(g.d && g.p && ((g.s && g.e) || g.ad)); };\n"
           "const bookBtn = (R) => ({ type: 'actions', elements: [{ type: 'button', style: 'primary', action_id: _cont(R) ? 'book_continue' : 'open_book', value: again(R), text: { type: 'plain_text', text: _cont(R) ? 'Continue booking' : 'Book a room' } },")
for nm in ["Question DM", "Result DM"]:
    sub(nm, OLD_BTN, NEW_BTN)
# 5. booked from it -> that message says so (it counts as a source message, like an offer)
n_src = 0
for n in wf["nodes"]:
    js = n.get("parameters", {}).get("jsCode") or ""
    a = "function srcIsOffer(blocks) { return (blocks || []).some(b => (b.elements || []).some(e => e.action_id === 'open_book' && /^\\{/.test(String(e.value || '')))); }"
    if a in js:
        n["parameters"]["jsCode"] = js.replace(a, "function srcIsOffer(blocks) { return (blocks || []).some(b => (b.elements || []).some(e => (e.action_id === 'open_book' || e.action_id === 'book_continue') && /^\\{/.test(String(e.value || '')))); }   // v45: Continue booking too")
        n_src += 1
assert n_src == 4, n_src
wf["name"] = "Jessie — Slack Interactions — v45 (Continue booking)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
