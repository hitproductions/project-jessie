#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v1.json - "Jessie — Slack Interactions", v1: the hello-form test.

A new, separate workflow (it does not touch main or any live flow). It proves the parts the Slack-app build depends on:
  1. a click and a form submission reach n8n through Cloudflare (Slack Interactivity -> /webhook/jessie-interactions)
  2. Slack's signature can be checked (Webhook Raw Body + the Crypto node's HMAC-SHA256)
  3. n8n answers Slack within 3 seconds ("got it" at once, the slow part after)
  4. a form can be opened (views.open), updated after the answer (views.update), and a DM posted
  5. the date picker opens a year ahead during QA
Every run posts a diagnostics message to the tester's DM, because executions cannot be read from here.

The Slack signing secret is NOT in this file: paste it into the "Signature" node after importing (see
docs/design/slack-app-hello-form.md). Re-importing a later build means pasting it again.
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v1.json")

TESTER = "U08V3CKDGJF"  # the DEV_REDIRECT id: Howard
SLACK_CRED = {"slackApi": {"id": "EcX8szEJrOLYLUfl", "name": "Jessie Slack (signed)"}}
SECRET_PLACEHOLDER = "PASTE-THE-SLACK-SIGNING-SECRET-HERE"

nid = lambda: str(uuid.uuid4())


def slack_post(name, method, body_expr, pos, on_error=True):
    n = {"parameters": {"method": "POST", "url": "https://slack.com/api/" + method,
                        "authentication": "predefinedCredentialType", "nodeCredentialType": "slackApi",
                        "sendBody": True, "specifyBody": "json", "jsonBody": body_expr, "options": {}},
         "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": pos, "id": nid(), "name": name,
         "credentials": SLACK_CRED}
    if on_error:
        n["onError"] = "continueRegularOutput"
    return n


def code(name, js, pos):
    return {"parameters": {"jsCode": js}, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": pos, "id": nid(), "name": name}


def respond(name, pos, body=None, status=200):
    p = {"respondWith": "json", "responseBody": body, "options": {"responseCode": status}} if body else \
        {"respondWith": "noData", "options": {"responseCode": status}}
    return {"parameters": p, "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": pos, "id": nid(), "name": name}


READ_REQUEST = r"""// Read Request: the raw body (for the signature), the Slack headers and the interaction payload.
// Slack sends application/x-www-form-urlencoded: payload=<url-encoded JSON>. The signature is over the exact raw bytes,
// so the Webhook node's Raw Body option must be on; rawSource says which way the raw body was found.
const item = $input.first();
const j = item.json || {};
const h = j.headers || {};
let raw = '', rawSource = 'none';
try {
  if (item.binary && item.binary.data) {
    const buf = await this.helpers.getBinaryDataBuffer(0, 'data');
    raw = buf.toString('utf8'); rawSource = 'binary';
  }
} catch (e) { rawSource = 'binary-error: ' + String(e.message || e).slice(0, 80); }
if (!raw && typeof j.body === 'string') { raw = j.body; rawSource = 'body-string'; }
if (!raw && j.rawBody) { raw = String(j.rawBody); rawSource = 'rawBody'; }
let payload = null, payloadSource = 'none';
try { const p = new URLSearchParams(raw).get('payload'); if (p) { payload = JSON.parse(p); payloadSource = 'raw'; } } catch (e) {}
if (!payload && j.body && j.body.payload) {
  try { payload = typeof j.body.payload === 'string' ? JSON.parse(j.body.payload) : j.body.payload; payloadSource = 'parsed-body'; } catch (e) {}
}
return [{ json: {
  raw, rawSource, rawLength: raw.length,
  sig: String(h['x-slack-signature'] || ''),
  ts: String(h['x-slack-request-timestamp'] || ''),
  payload: payload || {}, payloadSource,
  receivedAt: Date.now()
} }];"""

CHECK = r"""// Check Signature: Slack signs 'v0:' + timestamp + ':' + raw body with the signing secret (HMAC-SHA256, hex).
// Also refuse a timestamp more than 5 minutes off (replay protection). Then pick the route.
const r = $('Read Request').first().json;
const computed = String($input.first().json.computed || '');
const sigOk = !!r.sig && ('v0=' + computed) === r.sig;
const ageSec = r.ts ? Math.round(Date.now() / 1000 - Number(r.ts)) : null;
const fresh = ageSec !== null && Math.abs(ageSec) <= 300;
const p = r.payload || {};
const action = (p.actions && p.actions[0] && p.actions[0].action_id) || '';
const cb = (p.view && p.view.callback_id) || '';
let route = 3;                                              // anything else: just acknowledge
if (!(sigOk && fresh)) route = 0;                           // refused
else if (p.type === 'block_actions' && action === 'hello_open') route = 1;
else if (p.type === 'view_submission' && cb === 'hello_submit') route = 2;
return [{ json: { route, sigOk, fresh, ageSec, type: p.type || '', action, cb,
  user: (p.user && p.user.id) || '', triggerId: p.trigger_id || '', viewId: (p.view && p.view.id) || '',
  rawSource: r.rawSource, rawLength: r.rawLength, payloadSource: r.payloadSource, receivedAt: r.receivedAt } }];"""

BUILD_FORM = r"""// Build Form: the hello form. The date picker opens a year ahead (the QA year shift), on Manila's today.
const c = $('Check Signature').first().json;
const m = new Date(Date.now() + 8 * 3600 * 1000);
const d = (m.getUTCFullYear() + 1) + '-' + String(m.getUTCMonth() + 1).padStart(2, '0') + '-' + String(m.getUTCDate()).padStart(2, '0');
const view = {
  type: 'modal', callback_id: 'hello_submit',
  title: { type: 'plain_text', text: 'Hello form' },
  submit: { type: 'plain_text', text: 'Send' }, close: { type: 'plain_text', text: 'Cancel' },
  private_metadata: JSON.stringify({ openedAt: Date.now(), clickAge: c.ageSec }),
  blocks: [
    { type: 'section', text: { type: 'mrkdwn', text: 'Test form for the Slack-app build. Pick a date, type anything, press *Send*.' } },
    { type: 'input', block_id: 'date', label: { type: 'plain_text', text: 'Date' },
      element: { type: 'datepicker', action_id: 'date_pick', initial_date: d } },
    { type: 'input', block_id: 'note', label: { type: 'plain_text', text: 'Say something' },
      element: { type: 'plain_text_input', action_id: 'note_in' } }
  ]
};
return [{ json: { trigger_id: c.triggerId, view } }];"""

READ_SUBMIT = r"""// Read Submission: what was entered, and the views for "working" (sent at once) and "done" (sent after).
const c = $('Check Signature').first().json;
const p = $('Read Request').first().json.payload || {};
const v = (p.view && p.view.state && p.view.state.values) || {};
const date = (v.date && v.date.date_pick && v.date.date_pick.selected_date) || '';
const note = (v.note && v.note.note_in && v.note.note_in.value) || '';
let meta = {}; try { meta = JSON.parse((p.view && p.view.private_metadata) || '{}'); } catch (e) {}
const view = (text) => ({ type: 'modal', title: { type: 'plain_text', text: 'Hello form' }, close: { type: 'plain_text', text: 'Close' },
  blocks: [{ type: 'section', text: { type: 'mrkdwn', text } }] });
return [{ json: {
  viewId: c.viewId, user: c.user || '__TESTER__', date, note, meta,
  working: { response_action: 'update', view: view('⏳ *Working…* (this is the 3-second answer)') },
  done: view('✅ *Done.* The form was updated after the answer. Details are in your DM.')
} }];""".replace("__TESTER__", TESTER)

REPORT_SUBMIT = r"""// Report: the diagnostics message for the tester's DM.
const s = $('Read Submission').first().json;
const c = $('Check Signature').first().json;
const done = Date.now();
const lines = [
  '*Hello form - result*',
  '• Signature check: ' + (c.sigOk ? 'OK' : 'FAILED') + ' · request age ' + c.ageSec + ' s',
  '• Raw body: ' + c.rawSource + ' (' + c.rawLength + ' chars) · payload from ' + c.payloadSource,
  '• Date picked: ' + (s.date || '(none)') + ' · note: ' + (s.note || '(empty)'),
  '• Form update after the answer: ' + ((done - c.receivedAt) / 1000).toFixed(1) + ' s after Send reached n8n',
  '• Update call: ' + ($('Update Form').first().json.ok === true ? 'OK' : 'FAILED ' + JSON.stringify($('Update Form').first().json).slice(0, 150))
];
return [{ json: { channel: s.user, text: lines.join('\n') } }];"""

REPORT_REFUSED = r"""// Refused: the signature or the timestamp did not check out - tell the tester why (nothing else happens).
const c = $('Check Signature').first().json;
const lines = ['*Hello form - a request was refused*',
  '• Signature: ' + (c.sigOk ? 'OK' : 'did not match') + ' · timestamp age ' + c.ageSec + ' s (allowed: 300)',
  '• Raw body: ' + c.rawSource + ' (' + c.rawLength + ' chars) · payload from ' + c.payloadSource + ' · type ' + (c.type || '?'),
  'If the signature did not match: check the secret pasted in the Signature node, and that the Webhook node has Raw Body on.'];
return [{ json: { channel: '__TESTER__', text: lines.join('\n') } }];""".replace("__TESTER__", TESTER)

REPORT_OPEN = r"""// Report Open: say if views.open failed (the trigger_id lasts 3 seconds).
const r = $input.first().json;
if (r.ok === true) return [];
return [{ json: { channel: '__TESTER__', text: '*Hello form - the form did not open:* ' + JSON.stringify(r).slice(0, 300) } }];""".replace("__TESTER__", TESTER)

POST_BUTTON_BODY = ("={{ JSON.stringify({ channel: '" + TESTER + "', text: 'Hello form test', blocks: ["
                    "{ type: 'section', text: { type: 'mrkdwn', text: '*Hello form test* - tap the button to open a test form.' } },"
                    "{ type: 'actions', elements: [ { type: 'button', style: 'primary', action_id: 'hello_open', value: 'hello',"
                    " text: { type: 'plain_text', text: 'Open test form' } } ] } ] }) }}")

nodes, conn = [], {}


def add(n):
    nodes.append(n)
    return n["name"]


def link(a, b, out=0):
    c = conn.setdefault(a, {"main": []})
    while len(c["main"]) <= out:
        c["main"].append([])
    c["main"][out].append({"node": b, "type": "main", "index": 0})


# 1. the test button, posted by hand
t = add({"parameters": {}, "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [0, -320], "id": nid(),
         "name": "Post Test Button"})
pb = add(slack_post("Send Button", "chat.postMessage", POST_BUTTON_BODY, [240, -320]))
link(t, pb)

# 2. every click and form submission
wh = add({"parameters": {"httpMethod": "POST", "path": "jessie-interactions", "responseMode": "responseNode",
                         "options": {"rawBody": True}},
          "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 0], "id": nid(), "name": "Slack Interactions",
          "webhookId": "6f1d2c1e-4a7b-4c0e-9a51-1e2f3a4b5c6d"})
rr = add(code("Read Request", READ_REQUEST, [240, 0]))
sg = add({"parameters": {"action": "hmac", "type": "SHA256", "value": "={{ 'v0:' + $json.ts + ':' + $json.raw }}",
                         "dataPropertyName": "computed", "secret": SECRET_PLACEHOLDER, "encoding": "hex"},
          "type": "n8n-nodes-base.crypto", "typeVersion": 1, "position": [480, 0], "id": nid(), "name": "Signature"})
ck = add(code("Check Signature", CHECK, [720, 0]))
rt = add({"parameters": {"mode": "expression", "numberOutputs": 4, "output": "={{ $json.route }}"},
          "type": "n8n-nodes-base.switch", "typeVersion": 3.2, "position": [960, 0], "id": nid(), "name": "Route"})
for a, b in [(wh, rr), (rr, sg), (sg, ck), (ck, rt)]:
    link(a, b)

# route 0: refused
r0 = add(respond("Refuse", [1200, -300], status=401))
r0b = add(code("Report Refused", REPORT_REFUSED, [1440, -300]))
r0c = add(slack_post("DM Refused", "chat.postMessage", "={{ JSON.stringify({ channel: $json.channel, text: $json.text }) }}", [1680, -300]))
link(rt, r0, 0); link(r0, r0b); link(r0b, r0c)

# route 1: the button -> open the form
r1 = add(respond("Ack Click", [1200, -100]))
r1b = add(code("Build Form", BUILD_FORM, [1440, -100]))
r1c = add(slack_post("Open Form", "views.open", "={{ JSON.stringify({ trigger_id: $json.trigger_id, view: $json.view }) }}", [1680, -100]))
r1d = add(code("Report Open", REPORT_OPEN, [1920, -100]))
r1e = add(slack_post("DM Open Failed", "chat.postMessage", "={{ JSON.stringify({ channel: $json.channel, text: $json.text }) }}", [2160, -100]))
link(rt, r1, 1); link(r1, r1b); link(r1b, r1c); link(r1c, r1d); link(r1d, r1e)

# route 2: the submission -> "working" at once, then the slow part
r2 = add(code("Read Submission", READ_SUBMIT, [1200, 100]))
r2b = add(respond("Answer Working", [1440, 100], body="={{ JSON.stringify($json.working) }}"))
r2c = add({"parameters": {"amount": 3}, "type": "n8n-nodes-base.wait", "typeVersion": 1.1, "position": [1680, 100], "id": nid(),
           "name": "Pretend Work", "webhookId": nid()})
r2d = add(slack_post("Update Form", "views.update",
                     "={{ JSON.stringify({ view_id: $('Read Submission').first().json.viewId, view: $('Read Submission').first().json.done }) }}",
                     [1920, 100]))
r2e = add(code("Report", REPORT_SUBMIT, [2160, 100]))
r2f = add(slack_post("DM Result", "chat.postMessage", "={{ JSON.stringify({ channel: $json.channel, text: $json.text }) }}", [2400, 100]))
link(rt, r2, 2); link(r2, r2b); link(r2b, r2c); link(r2c, r2d); link(r2d, r2e); link(r2e, r2f)

# route 3: anything else - acknowledge
r3 = add(respond("Ack Other", [1200, 300]))
link(rt, r3, 3)

nodes.append({"parameters": {"content": "## Hello form (Slack-app build, test)\nPaste the Slack **signing secret** into the **Signature** node "
                             "after importing - it is not in the file.\n\nRun **Post Test Button** by hand: a button appears in the tester's DM. "
                             "Every run DMs a diagnostics line.\n\nSlack Interactivity request URL: `https://signal.hitpromanila.net/webhook/jessie-interactions`",
                             "height": 300, "width": 420},
              "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [-40, -620], "id": nid(), "name": "About"})

wf = {"name": "Jessie — Slack Interactions — v1 (hello form)", "nodes": nodes, "connections": conn,
      "settings": {"executionOrder": "v1"}, "pinData": {}, "active": False}
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(nodes), "nodes")
