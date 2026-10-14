#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v10.json - "Jessie — Slack Interactions", v10: form polish from the v9 Slack test.

v10 (15 Oct, from the Slack test 01:30-01:40; fixes v9 / v8 wording): only the top room carries a note ("Recommended ·
usual for VO Recording"; the rest just the name); the not-usual rooms are remembered in the form (private_metadata "nu")
instead of read from each room's note; "Booking Studio 7…" says only "This takes a few seconds."; the Booked screen
has no "A copy is in your DM" line; a blank line after "✅ Booked." (form and DM); Notes sits behind a small
"Add a note" checkbox - ticking it adds the field (route 8, note_toggle: answered at once, then views.update with the
entries kept), unticking removes it. Built on v9 (live; download workflows/imported/slack-interactions-v9-imported.json).

v9 (typed booking -> form):

v9 (typed booking -> form, 15 Oct; with main v263): main answers a typed booking request with what it read and a Book a
room button whose value carries it ({d, s, e, p, r, pj, c, cd, en, ar}). The button opens step 1 with the date, times and
session type already chosen (an off-half-hour time is added to the list); step 2 then has the room asked for chosen when
it is free (a free room that is not a usual one is offered as "not a usual room", booked as asked), says so when it is
taken, and has the project, client, code, engineer and arranger filled in. The menu's button (value "menu") opens an empty
form as before. Built on v8 (live; download workflows/imported/slack-interactions-v8-imported.json).

v8 (step B fixes, 15 Oct, from the step B test; fixes v7): the Booked result (form and DM) is the card's format - title,
then Date, Time and Room lines, nothing else; Start and End are a list of half-hour times that opens at 8:00 AM and runs
round to 7:30 AM (every time still bookable); the "Did you mean …?" notice showed "" and ** because Book Session's
Return Rejection dropped the typed name and the suggestions - Book Session v110 passes them on, and the form also reads
them from Book Session's own sentence (and the form's client field) if they are missing, so a notice is never blank.
Built on v7 (live; download workflows/imported/slack-interactions-v7-imported.json).

v7 (slice 1 step B, 14 Oct): Book really books. Step 2's Book answers "Booking…" at once, then calls Book Session in prepare
mode (every check and question the chat has) and, when it is prepared, books exactly what prepare returned - the same two
steps as the chat's card and yes. A question or a problem (Did you mean …?, department, kind of booking, arranger, the room
just taken or declined) comes back on the form with the entries kept. The engineer's and arranger's Slack ids ride on the
event ("team:"), for the who-can-change rule. Built on v6 (live; download workflows/imported/slack-interactions-v6-imported.json).
v6 (14 Oct, from the step A test): no "Time zone: Beijing…" note under the times - the time pickers carry no time zone
and every time is read as Philippine Time (+08:00); "Booth time (M booth)" is just "M booth"; the booth list has no
"Free then" note (every booth listed is free). Built on v5 (live; download workflows/imported/slack-interactions-v5-imported.json).
v5 (one alphabetical engineer list, 14 Oct): the Engineer field is one list of every engineer, A to Z (v4 grouped the
session type's required role first). v4 (engineers from Bookers): the Engineer and Arranger fields list only Bookers whose
role (Info) is an engineer / a music arranger - not everyone in Slack. Built on v4 (live; download
workflows/imported/slack-interactions-v4-imported.json), on v3 (live; download
workflows/imported/slack-interactions-v3-imported.json). v3 added:
  - the menu's buttons (main v262 posts the menu): Book a room -> step 1; My bookings -> "coming next" for now
  - step 1 (date, start, end, what it's for; session types from the Jessie Reference Cache data table) -> Find rooms
  - step 2 pushed on top (so Back returns to step 1): free rooms that fit, ranked (Room Availability), then the details
  - Book -> a DRY RUN: the form shows exactly what would be booked (title built by code); nothing is written. Step B
    replaces it with the real booking through Book Session.
The hello-form routes stay (diagnostics). Every answer to Slack goes out at once; slow work (Room Availability) follows
and updates the form by its external_id.
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v10.json")

TESTER = "U08V3CKDGJF"
SLACK_CRED = {"slackApi": {"id": "EcX8szEJrOLYLUfl", "name": "Jessie Slack (signed)"}}
SIGNATURE_WF = "R06CBQNhFK0x4ZuO"
ROOM_AVAIL_WF = "e7tBQB458nstrqei"
BOOK_SESSION_WF = "EUG3sGXkfsJSYIMz"
CACHE_TABLE = "CsdJhgDxCsqq9K9j"
WEBHOOK_ID = "6f1d2c1e-4a7b-4c0e-9a51-1e2f3a4b5c6d"   # same as v1/v2: the live webhook

nid = lambda: str(uuid.uuid4())
nodes, conn = [], {}


def add(n):
    nodes.append(n)
    return n["name"]


def link(a, b, out=0):
    c = conn.setdefault(a, {"main": []})
    while len(c["main"]) <= out:
        c["main"].append([])
    c["main"][out].append({"node": b, "type": "main", "index": 0})


def chain(*names):
    for a, b in zip(names, names[1:]):
        link(a, b)


def slack(name, method, body_expr, pos):
    return add({"parameters": {"method": "POST", "url": "https://slack.com/api/" + method,
                               "authentication": "predefinedCredentialType", "nodeCredentialType": "slackApi",
                               "sendBody": True, "specifyBody": "json", "jsonBody": body_expr, "options": {}},
                "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": pos, "id": nid(), "name": name,
                "credentials": SLACK_CRED, "onError": "continueRegularOutput"})


def code(name, js, pos):
    return add({"parameters": {"jsCode": js}, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": pos, "id": nid(), "name": name})


def respond(name, pos, body=None, status=200):
    p = {"respondWith": "json", "responseBody": body, "options": {"responseCode": status}} if body else \
        {"respondWith": "noData", "options": {"responseCode": status}}
    return add({"parameters": p, "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1, "position": pos, "id": nid(), "name": name})


def run_wf(name, wf_id, label, pos):
    return add({"parameters": {"source": "database", "mode": "each",
                               "workflowId": {"__rl": True, "mode": "list", "value": wf_id, "cachedResultName": label}, "options": {}},
                "type": "n8n-nodes-base.executeWorkflow", "typeVersion": 1.2, "position": pos, "id": nid(), "name": name})


def iff(name, expr, pos):
    return add({"parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
                                              "conditions": [{"id": nid(), "leftValue": expr, "rightValue": True,
                                                              "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                                              "combinator": "and"}, "options": {}},
                "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": pos, "id": nid(), "name": name})


DM = "={{ JSON.stringify({ channel: $json.channel, text: $json.text }) }}"

# ------------------------------------------------------------------------------------------------- shared JS helpers
CACHE_JS = r"""
// The newest valid row of the Jessie Reference Cache data table (same check as main's Reference Snapshot).
function readCache(rows) {
  let best = null;
  for (const r of rows || []) {
    if (!r || r.cache_key !== 'jessie-reference') continue;
    let d; try { d = JSON.parse(r.payload); } catch (e) { continue; }
    if (!d || !Array.isArray(d.rooms) || !Array.isArray(d.sessionTypes) || !Array.isArray(d.bookers)) continue;
    const at = Date.parse(r.refreshed_at || '') || 0;
    if (!best || at > best.at) best = { at, d };
  }
  return best ? best.d : null;
}
"""

READ_REQUEST = r"""// Read Request: the raw body (for the signature), the Slack headers and the interaction payload.
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
let payload = null, payloadSource = 'none';
if (j.body && j.body.payload) {
  try { payload = typeof j.body.payload === 'string' ? JSON.parse(j.body.payload) : j.body.payload; payloadSource = 'parsed-body'; } catch (e) {}
}
if (!payload) {
  try { const m = raw.match(/(?:^|&)payload=([^&]*)/); if (m) { payload = JSON.parse(decodeURIComponent(m[1].replace(/\+/g, ' '))); payloadSource = 'raw'; } } catch (e) {}
}
return [{ json: {
  raw, rawSource, rawLength: raw.length,
  sig: String(h['x-slack-signature'] || ''),
  ts: String(h['x-slack-request-timestamp'] || ''),
  payload: payload || {}, payloadSource,
  receivedAt: Date.now()
} }];"""

TO_SIGN = r"""// To Sign: the string Slack signs - 'v0:' + timestamp + ':' + raw body - for Jessie — Slack Signature.
const r = $input.first().json;
return [{ json: { base: 'v0:' + r.ts + ':' + r.raw } }];"""

CHECK = r"""// Check Signature: Slack signs 'v0:' + timestamp + ':' + raw body (HMAC-SHA256, hex). Refuse a timestamp more than
// 5 minutes off. Then pick the route.
const r = $('Read Request').first().json;
const computed = String($input.first().json.computed || '');
const sigOk = !!r.sig && ('v0=' + computed) === r.sig;
const ageSec = r.ts ? Math.round(Date.now() / 1000 - Number(r.ts)) : null;
const fresh = ageSec !== null && Math.abs(ageSec) <= 300;
const p = r.payload || {};
const action = (p.actions && p.actions[0] && p.actions[0].action_id) || '';
const cb = (p.view && p.view.callback_id) || '';
const ROUTES = { refused: 0, hello_open: 1, hello_submit: 2, other: 3, open_book: 4, book_step1: 5, book_step2: 6, my_bookings: 7, note_toggle: 8 };
let route = ROUTES.other;
if (!(sigOk && fresh)) route = ROUTES.refused;
else if (p.type === 'block_actions' && action === 'hello_open') route = ROUTES.hello_open;
else if (p.type === 'view_submission' && cb === 'hello_submit') route = ROUTES.hello_submit;
else if (p.type === 'block_actions' && action === 'open_book') route = ROUTES.open_book;
else if (p.type === 'block_actions' && action === 'my_bookings') route = ROUTES.my_bookings;
else if (p.type === 'block_actions' && action === 'note_toggle') route = ROUTES.note_toggle;   // v10
else if (p.type === 'view_submission' && cb === 'book_step1') route = ROUTES.book_step1;
else if (p.type === 'view_submission' && cb === 'book_step2') route = ROUTES.book_step2;
return [{ json: { route, sigOk, fresh, ageSec, type: p.type || '', action, cb,
  user: (p.user && p.user.id) || '', triggerId: p.trigger_id || '', viewId: (p.view && p.view.id) || '',
  channel: (p.channel && p.channel.id) || (p.container && p.container.channel_id) || '',
  rawSource: r.rawSource, rawLength: r.rawLength, payloadSource: r.payloadSource, receivedAt: r.receivedAt } }];"""

# hello form (kept from v2)
BUILD_HELLO = r"""// Build Form: the hello form (diagnostics). The date picker opens a year ahead (the QA year shift).
const c = $('Check Signature').first().json;
const m = new Date(Date.now() + 8 * 3600 * 1000);
const d = (m.getUTCFullYear() + 1) + '-' + String(m.getUTCMonth() + 1).padStart(2, '0') + '-' + String(m.getUTCDate()).padStart(2, '0');
const view = { type: 'modal', callback_id: 'hello_submit', title: { type: 'plain_text', text: 'Hello form' },
  submit: { type: 'plain_text', text: 'Send' }, close: { type: 'plain_text', text: 'Cancel' },
  blocks: [
    { type: 'section', text: { type: 'mrkdwn', text: 'Test form for the Slack-app build. Pick a date, type anything, press *Send*.' } },
    { type: 'input', block_id: 'date', label: { type: 'plain_text', text: 'Date' }, element: { type: 'datepicker', action_id: 'date_pick', initial_date: d } },
    { type: 'input', block_id: 'note', label: { type: 'plain_text', text: 'Say something' }, element: { type: 'plain_text_input', action_id: 'note_in' } } ] };
return [{ json: { trigger_id: c.triggerId, view } }];"""

READ_HELLO = r"""// Read Submission (hello form).
const c = $('Check Signature').first().json;
const p = $('Read Request').first().json.payload || {};
const v = (p.view && p.view.state && p.view.state.values) || {};
const date = (v.date && v.date.date_pick && v.date.date_pick.selected_date) || '';
const note = (v.note && v.note.note_in && v.note.note_in.value) || '';
const view = (text) => ({ type: 'modal', title: { type: 'plain_text', text: 'Hello form' }, close: { type: 'plain_text', text: 'Close' },
  blocks: [{ type: 'section', text: { type: 'mrkdwn', text } }] });
return [{ json: { viewId: c.viewId, user: c.user || '__TESTER__', date, note,
  working: { response_action: 'update', view: view('⏳ *Working…*') },
  done: view('✅ *Done.* Details are in your DM.') } }];""".replace("__TESTER__", TESTER)

REPORT_HELLO = r"""// Report (hello form).
const s = $('Read Submission').first().json;
const c = $('Check Signature').first().json;
const lines = ['*Hello form - result*',
  '• Signature check: ' + (c.sigOk ? 'OK' : 'FAILED') + ' · request age ' + c.ageSec + ' s',
  '• Raw body: ' + c.rawSource + ' (' + c.rawLength + ' chars) · payload from ' + c.payloadSource,
  '• Date picked: ' + (s.date || '(none)') + ' · note: ' + (s.note || '(empty)'),
  '• Update call: ' + ($('Update Form').first().json.ok === true ? 'OK' : 'FAILED ' + JSON.stringify($('Update Form').first().json).slice(0, 150))];
return [{ json: { channel: s.user, text: lines.join('\n') } }];"""

REPORT_REFUSED = r"""// Refused: the signature or the timestamp did not check out - tell the tester why (nothing else happens).
const c = $('Check Signature').first().json;
const lines = ['*Slack Interactions - a request was refused*',
  '• Signature: ' + (c.sigOk ? 'OK' : 'did not match') + ' · timestamp age ' + c.ageSec + ' s (allowed: 300)',
  '• Raw body: ' + c.rawSource + ' (' + c.rawLength + ' chars) · payload from ' + c.payloadSource + ' · type ' + (c.type || '?'),
  'If the signature did not match: check the secret in the Sign node of Jessie — Slack Signature, and that the Webhook node has Raw Body on.'];
return [{ json: { channel: '__TESTER__', text: lines.join('\n') } }];""".replace("__TESTER__", TESTER)

REPORT_OPEN = r"""// Report Open: say if views.open failed (the trigger_id lasts 3 seconds).
const r = $input.first().json;
if (r.ok === true) return [];
const c = $('Check Signature').first().json;
return [{ json: { channel: c.user || '__TESTER__', text: '⚠️ The form did not open: ' + JSON.stringify(r).slice(0, 300) } }];""".replace("__TESTER__", TESTER)

# ------------------------------------------------------------------------------------------------- step 1
BUILD_STEP1 = CACHE_JS + r"""
// Build Step 1: date, start, end, what it's for. Session types from the reference cache; the date picker opens on
// Manila's today a year ahead (QA year shift - at launch: YEAR_SHIFT = 0).
const YEAR_SHIFT = 1;
const c = $('Check Signature').first().json;
const data = readCache($('Read Cache').all().map(i => i.json || {}));
const types = data ? data.sessionTypes.map(r => String((r.fields || {}).Type || '').trim()).filter(Boolean) : [];
const NOT_SESSION = ['Meeting', 'Event'];
const sessions = types.filter(t => NOT_SESSION.indexOf(t) === -1).sort();
const opt = (t, v) => ({ text: { type: 'plain_text', text: t }, value: v || t });
const groups = [];
if (sessions.length) groups.push({ label: { type: 'plain_text', text: 'Sessions' }, options: sessions.slice(0, 100).map(t => opt(t)) });
groups.push({ label: { type: 'plain_text', text: 'Not a session' },
  options: NOT_SESSION.filter(t => types.indexOf(t) !== -1).map(t => opt(t)).concat([opt('M booth', '__booth')]) });
// Start / End: half-hour times, the list opening at 8:00 AM and running round to 7:30 AM (all bookable, read as PHT).
const times = [];
for (let i = 0; i < 48; i++) { const mins = (8 * 60 + i * 30) % (24 * 60), h = Math.floor(mins / 60), mm = mins % 60;
  times.push({ text: { type: 'plain_text', text: ((h % 12) || 12) + ':' + String(mm).padStart(2, '0') + ' ' + (h < 12 ? 'AM' : 'PM') },
               value: String(h).padStart(2, '0') + ':' + String(mm).padStart(2, '0') }); }
const timeEl = (id, o) => Object.assign({ type: 'static_select', action_id: id, placeholder: { type: 'plain_text', text: 'Choose a time' }, options: times }, o ? { initial_option: o } : {});
// v9: what main read from a typed request rides on the button's value (the menu's button says "menu": nothing to fill in)
let pre = {};
try { const a = ((($('Read Request').first().json.payload || {}).actions) || [])[0] || {}; if (/^\{/.test(String(a.value || ''))) pre = JSON.parse(a.value) || {}; } catch (e) { pre = {}; }
const hm = x => /^([01]\d|2[0-3]):[0-5]\d$/.test(String(x || '')) ? String(x) : '';
const tOpt = v => { let o = times.find(x => x.value === v); if (o) return o;
  const [h, mm] = v.split(':').map(Number); o = { text: { type: 'plain_text', text: ((h % 12) || 12) + ':' + String(mm).padStart(2, '0') + ' ' + (h < 12 ? 'AM' : 'PM') }, value: v };
  const key = x => (Number(x.split(':')[0]) * 60 + Number(x.split(':')[1]) - 480 + 1440) % 1440;   // the list's order: from 8:00 AM round
  const at = times.findIndex(x => key(x.value) > key(v)); times.splice(at === -1 ? times.length : at, 0, o); return o; };
const preS = hm(pre.s), preE = hm(pre.e);
const startOpt = preS ? tOpt(preS) : null, endOpt = preE ? tOpt(preE) : null;
const allPurpose = [].concat(...groups.map(gr => gr.options));
const purposeOpt = pre.p ? allPurpose.find(o => o.value === pre.p) || null : null;
const m = new Date(Date.now() + 8 * 3600 * 1000);
const today = (m.getUTCFullYear() + YEAR_SHIFT) + '-' + String(m.getUTCMonth() + 1).padStart(2, '0') + '-' + String(m.getUTCDate()).padStart(2, '0');
const view = {
  type: 'modal', callback_id: 'book_step1',
  title: { type: 'plain_text', text: 'Book a room' },
  submit: { type: 'plain_text', text: 'Find rooms' }, close: { type: 'plain_text', text: 'Cancel' },
  private_metadata: JSON.stringify(Object.assign({ requester: c.user, channel: c.channel }, Object.keys(pre).length ? { pre } : {})),
  blocks: [
    { type: 'context', elements: [{ type: 'mrkdwn', text: '*Step 1 of 2* · when, and what for' }] },
    { type: 'input', block_id: 'date', label: { type: 'plain_text', text: 'Date' },
      element: { type: 'datepicker', action_id: 'date_pick', initial_date: /^\d{4}-\d{2}-\d{2}$/.test(String(pre.d || '')) ? pre.d : today } },
    { type: 'input', block_id: 'start', label: { type: 'plain_text', text: 'Start' },
      element: timeEl('start_pick', startOpt) },
    { type: 'input', block_id: 'end', label: { type: 'plain_text', text: 'End' },
      element: timeEl('end_pick', endOpt) },
    { type: 'input', block_id: 'purpose', label: { type: 'plain_text', text: "What's it for?" },
      hint: { type: 'plain_text', text: 'Jessie offers the rooms that can do this, the usual ones first.' },
      element: Object.assign({ type: 'static_select', action_id: 'purpose_pick', placeholder: { type: 'plain_text', text: 'Choose' }, option_groups: groups }, purposeOpt ? { initial_option: purposeOpt } : {}) }
  ]
};
return [{ json: { trigger_id: c.triggerId, view, cacheOk: !!data } }];"""

READ_STEP1 = CACHE_JS + r"""
// Read Step 1: the values, checked at once (Slack shows errors next to the fields only in this first answer).
// Valid -> push a "Finding rooms…" view (external_id, so it can be updated after Room Availability answers).
const c = $('Check Signature').first().json;
const p = $('Read Request').first().json.payload || {};
const v = (p.view && p.view.state && p.view.state.values) || {};
const date = (v.date && v.date.date_pick && v.date.date_pick.selected_date) || '';
const pickT = (b, a) => (v[b] && v[b][a] && ((v[b][a].selected_option && v[b][a].selected_option.value) || v[b][a].selected_time)) || '';
const t0 = pickT('start', 'start_pick');
const t1 = pickT('end', 'end_pick');
const purpose = (v.purpose && v.purpose.purpose_pick && v.purpose.purpose_pick.selected_option && v.purpose.purpose_pick.selected_option.value) || '';
let meta = {}; try { meta = JSON.parse((p.view && p.view.private_metadata) || '{}'); } catch (e) {}
const errors = {};
if (!date) errors.date = 'Pick a date.';
if (!t0) errors.start = 'Pick a start time.';
if (!t1) errors.end = 'Pick an end time.';
if (t0 && t1 && t1 <= t0) errors.end = 'The end has to be after the start.';
if (!purpose) errors.purpose = "Pick what it's for.";
const valid = Object.keys(errors).length === 0;
const ext = 's2-' + (c.user || 'x') + '-' + Date.now();
const kind = purpose === '__booth' ? 'booth' : (purpose === 'Meeting' || purpose === 'Event') ? 'meeting'
  : /^localization/i.test(purpose) ? 'loc' : 'studio';
const s = { date, t0, t1, purpose, kind, requester: meta.requester || c.user, channel: meta.channel || '', ext };
if (meta.pre && typeof meta.pre === 'object') s.pre = meta.pre;   // v9: what main read, for step 2
const loading = { type: 'modal', external_id: ext, callback_id: 'book_step2',
  title: { type: 'plain_text', text: 'Book a room' }, close: { type: 'plain_text', text: 'Back' },
  private_metadata: JSON.stringify(s),
  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: '⏳ *Finding free rooms…*' } }] };
return [{ json: { valid, s,
  answer: valid ? { response_action: 'push', view: loading } : { response_action: 'errors', errors } } }];"""

TO_RA = CACHE_JS + r"""
// To Room Availability: the window, the session type (none for booth time) and the reference data built the same way as
// main's Room Table (rooms with booth / common flags; session types with Priority / Last Resort record ids).
const s = $('Read Step 1').first().json.s;
const data = readCache($('Read Cache 2').all().map(i => i.json || {})) || { rooms: [], sessionTypes: [] };
const refRooms = [];
for (const r of data.rooms) {
  const f = r.fields || {};
  if (!r.id || !f['Room Name']) continue;
  const kinds = [].concat(f['Room Type'] || []).map(x => String(x).toLowerCase());
  refRooms.push({ id: r.id, name: String(f['Room Name']).trim(), vocalBooth: f['Vocal Booth'] === true,
    booth: f['Vocal Booth'] === true || kinds.indexOf('recording booth') !== -1,
    common: kinds.indexOf('conference room') !== -1 || kinds.indexOf('lobby') !== -1 });
}
const refTypes = []; const preemptionRanks = {};
for (const r of data.sessionTypes) {
  const f = r.fields || {}; const t = String(f['Type'] || '').trim();
  if (!t) continue;
  refTypes.push({ type: t, min: f['Min Duration (mins)'] || null, max: f['Max Duration (mins)'] || null, typical: f['Typical Duration'] || null,
    roles: [].concat(f['Engineer Role Required'] || []), req: String(f['Room Requirements'] || ''),
    priority: [].concat(f['Priority'] || []), last: [].concat(f['Last Resort'] || []) });
  const rk = Number(f['Preemption Rank']); if (Number.isFinite(rk)) preemptionRanks[t] = rk;
}
return [{ json: {
  // Always Philippine Time: the pickers carry no time zone, so the picked hh:mm is taken as Manila time (+08:00).
  start_iso: s.date + 'T' + s.t0 + ':00+08:00', end_iso: s.date + 'T' + s.t1 + ':00+08:00',
  session_type: s.kind === 'booth' ? '' : s.purpose, room: '', scope: '', hours: '',
  reference_data: JSON.stringify({ rooms: refRooms, types: refTypes, preemptionRanks })
} }];"""

BUILD_STEP2 = CACHE_JS + r"""
// Build Step 2: the free rooms that fit (ranked; usual first, others only when no usual room is free), then the details
// for this kind of booking. Replaces the "Finding free rooms…" view by its external_id.
const s = $('Read Step 1').first().json.s;
const ra = $input.first().json || {};
const data = readCache($('Read Cache 2').all().map(i => i.json || {})) || { rooms: [], sessionTypes: [], bookers: [] };
const opt = (t, v, d) => Object.assign({ text: { type: 'plain_text', text: t }, value: v || t }, d ? { description: { type: 'plain_text', text: d } } : {});
const md = t => ({ type: 'mrkdwn', text: t });
const ctx = t => ({ type: 'context', elements: [md(t)] });
const input = (bid, label, element, o) => Object.assign({ type: 'input', block_id: bid, label: { type: 'plain_text', text: label }, element }, o || {});
const fmtT = hm => { let [h, m] = hm.split(':').map(Number); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(m).padStart(2, '0') + ' ' + ap; };
const dt = new Date(s.date + 'T00:00:00Z');
const DOW = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'], MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const when = DOW[dt.getUTCDay()] + ', ' + MON[dt.getUTCMonth()] + ' ' + dt.getUTCDate() + ' · ' + fmtT(s.t0) + '–' + fmtT(s.t1);
const label = s.kind === 'booth' ? 'M booth' : s.purpose;
let rooms = [], note = '';
const nu = [];   // v10: rooms offered that are not usual for this session (booked as asked)
if (ra.status !== 'OK') {
  note = '⚠️ The calendar could not be checked (' + (ra.status || 'no answer') + '). Go Back and try again.';
} else if (s.kind === 'booth') {
  rooms = (ra.free_rooms || []).filter(r => /^M\d+$/i.test(r)).map(r => opt(r, r));
} else {
  const pri = ra.free_priority || [], last = ra.free_last_resort || [];
  // v10: only the top room carries a note; the not-usual rooms are remembered in the form (nu), not read from the notes
  rooms = pri.map((r, i) => i === 0 ? opt(r, r, 'Recommended · usual for ' + label) : opt(r, r));
  if (!rooms.length) { rooms = last.map((r, i) => i === 0 ? opt(r, r, 'Recommended · can do ' + label + ' · not a usual room') : opt(r, r)); nu.push(...last); }
  const st = (data.sessionTypes || []).find(r => String((r.fields || {}).Type || '').trim() === s.purpose);
  const nameOf = {}; for (const r of data.rooms || []) nameOf[r.id] = String((r.fields || {})['Room Name'] || '').trim();
  const usual = st ? [].concat((st.fields || {}).Priority || []).map(id => nameOf[id]).filter(Boolean) : [];
  const taken = usual.filter(r => pri.indexOf(r) === -1);
  if (taken.length && rooms.length) note = 'Not free then: ' + taken.join(', ');
}
// v9: the room the requester typed - chosen when it is free and fits; a free room that is not a usual one is offered as
// such (booked as asked); otherwise say it is taken, or that it is not a room for this.
const pre = (s.pre && typeof s.pre === 'object') ? s.pre : {};
let preRoom = null, preNote = '';
if (pre.r && ra.status === 'OK') {
  const i = rooms.findIndex(o => o.value === pre.r);
  if (i !== -1) { preRoom = rooms[i]; if (i >= 10) { rooms.splice(i, 1); rooms.unshift(preRoom); } }
  else if (s.kind !== 'booth' && [].concat(ra.free_last_resort || []).indexOf(pre.r) !== -1) {
    preRoom = opt(pre.r, pre.r, 'can do ' + label + ' · not a usual room'); rooms.unshift(preRoom); nu.push(pre.r); }
  else if ([].concat(ra.free_rooms || []).indexOf(pre.r) !== -1) preNote = pre.r + ' isn’t a room for ' + label + '.';
  else preNote = pre.r + ' is taken then.';
  if (preNote && rooms.length) preNote += ' These are free:';
}
rooms = rooms.slice(0, 10);
const blocks = [ctx('*Step 2 of 2* · room and details'), { type: 'section', text: md('🗓️ *' + when + ' · ' + label + '*') }];
if (!rooms.length) {
  if (preNote) blocks.push({ type: 'section', text: md('⚠️ ' + preNote) });
  blocks.push({ type: 'section', text: md(note || ('Nothing that does ' + label + ' is free then. Go *Back* and try another time.')) });
} else {
  if (preNote) blocks.push({ type: 'section', text: md('⚠️ ' + preNote) });
  blocks.push(input('room', 'Room', { type: 'radio_buttons', action_id: 'room_radio', options: rooms, initial_option: preRoom || rooms[0] }));
  if (note) blocks.push(ctx(note));
  blocks.push({ type: 'divider' });
  // Engineers and arrangers come from Bookers (Info names the role), never from everyone in Slack - one list, A to Z.
  const people = (data.bookers || []).map(b => { const f = b.fields || {};
    return { name: String(f.Name || '').trim(), info: String(f.Info || ''),
             slack: String(f['Slack User ID'] || '').split(/[\s,]+/).filter(Boolean)[0] || '' }; }).filter(p => p.name && p.slack);
  const isEng = p => /\bengineer\b/i.test(p.info);
  const engs = people.filter(isEng).sort((a, b) => a.name.localeCompare(b.name));
  const popt = p => ({ text: { type: 'plain_text', text: p.name }, value: p.slack });
  const me = engs.find(p => p.slack === s.requester);
  const engEl = { type: 'static_select', action_id: 'engineer_pick', placeholder: { type: 'plain_text', text: "Who's engineering?" }, options: engs.slice(0, 100).map(popt) };
  const preEng = engs.find(p => p.slack === pre.en);   // v9: the engineer named in the typed request
  if (preEng) engEl.initial_option = popt(preEng); else if (me) engEl.initial_option = popt(me);
  const engineer = input('engineer', 'Engineer', engEl,
    { hint: { type: 'plain_text', text: preEng ? 'As you typed it.' : me ? 'Set to you. Change it if someone else is engineering.' : 'Only engineers are listed (from Bookers).' } });
  const arrs = people.filter(p => /\bmusic arranger\b/i.test(p.info)).sort((a, b) => a.name.localeCompare(b.name));
  const meArr = arrs.find(p => p.slack === s.requester);
  const arrEl = { type: 'static_select', action_id: 'arranger_pick', placeholder: { type: 'plain_text', text: 'Choose' },
    options: [{ text: { type: 'plain_text', text: 'No arranger' }, value: 'none' }].concat(arrs.slice(0, 99).map(popt)) };
  const preArr = arrs.find(p => p.slack === pre.ar);
  if (preArr) arrEl.initial_option = popt(preArr); else if (meArr) arrEl.initial_option = popt(meArr);
  const iv = (el, v) => { v = String(v || '').trim().slice(0, 150); if (v) el.initial_value = v; return el; };   // v9: typed values
  // v10: Notes sits behind a small checkbox; ticking it adds the field (route 8)
  const notes = { type: 'actions', block_id: 'note_toggle', elements: [{ type: 'checkboxes', action_id: 'note_toggle',
    options: [{ text: { type: 'plain_text', text: 'Add a note' }, value: 'note' }] }] };
  if (s.kind === 'meeting') {
    blocks.push(input('title', 'Meeting title', { type: 'plain_text_input', action_id: 'title_in' }), notes);
  } else if (s.kind === 'booth') {
    blocks.push(notes);
  } else if (s.kind === 'loc') {
    blocks.push(input('code', 'Project code', iv({ type: 'plain_text_input', action_id: 'code_in' }, pre.cd),
      { hint: { type: 'plain_text', text: 'As in Localization Projects. The client and the title come from it.' } }), engineer, notes);
  } else {
    blocks.push(input('project', 'Project', iv({ type: 'plain_text_input', action_id: 'project_in' }, pre.pj)),
      input('client', 'Client', iv({ type: 'plain_text_input', action_id: 'client_in' }, pre.c),
        { optional: true, hint: { type: 'plain_text', text: "Leave empty if there's no client. A new name is fine." } }),
      engineer);
    if (/music|band/i.test(s.purpose))
      if (arrs.length) blocks.push(input('arranger', 'Arranger', arrEl, { optional: true }));
    blocks.push(notes);
  }
}
const view = { type: 'modal', callback_id: 'book_step2', title: { type: 'plain_text', text: 'Book a room' },
  close: { type: 'plain_text', text: 'Back' }, private_metadata: JSON.stringify(Object.assign({}, s, { when, label }, nu.length ? { nu } : {})), blocks };
if (rooms.length) view.submit = { type: 'plain_text', text: 'Book' };
return [{ json: { external_id: s.ext, view } }];"""

READ_STEP2 = CACHE_JS + r"""
// Read Step 2 (v7): the details, checked at once (errors next to the fields), the calendar title built by code, and Book
// Session's prepare inputs. Valid -> the form shows "Booking…" at once; prepare and book follow.
const c = $('Check Signature').first().json;
const p = $('Read Request').first().json.payload || {};
const v = (p.view && p.view.state && p.view.state.values) || {};
let s = {}; try { s = JSON.parse((p.view && p.view.private_metadata) || '{}'); } catch (e) {}
const val = (b, a) => (v[b] && v[b][a] && (v[b][a].value || v[b][a].selected_user || (v[b][a].selected_option && v[b][a].selected_option.value))) || '';
const room = val('room', 'room_radio');
const project = String(val('project', 'project_in')).trim().replace(/^(project|proj)\s+/i, '');
const client = String(val('client', 'client_in')).trim();
const code = String(val('code', 'code_in')).trim();
const title = String(val('title', 'title_in')).trim();
const engineerId = val('engineer', 'engineer_pick');
const arrPick = val('arranger', 'arranger_pick');
const arrangerId = arrPick === 'none' ? '' : arrPick;
const notes = String(val('notes', 'notes_in')).trim();
const dept = val('department', 'department_pick');
const kind = val('kind', 'kind_pick');
const errors = {};
if (!room) errors.room = 'Pick a room.';
if (s.kind === 'studio' && !project) errors.project = 'What is the project called?';
if (s.kind === 'loc' && !code) errors.code = 'Type the project code.';
if (s.kind === 'meeting' && !title) errors.title = 'Give the meeting a title.';
if ((s.kind === 'studio' || s.kind === 'loc') && !engineerId) errors.engineer = 'Pick the engineer.';
const data = readCache($('Read Cache 3').all().map(i => i.json || {})) || { bookers: [], rooms: [], sessionTypes: [] };
const bySlack = {};
for (const b of data.bookers || []) { const f = b.fields || {}; String(f['Slack User ID'] || '').split(/[\s,]+/).filter(Boolean).forEach(id => { bySlack[id] = f; }); }
const who = id => bySlack[id] || null;
const nm = id => { const f = who(id); return f ? String(f.Name || '').trim() : ''; };
const ini = id => { const f = who(id); return f ? String(f.Initials || '').trim() : ''; };
if (engineerId && !who(engineerId)) errors.engineer = "That person isn't in Bookers yet - pick someone who is, or ask for them to be added.";
const first = id => nm(id).split(/\s+/)[0] || '';
let calTitle = '';
if (s.kind === 'meeting') calTitle = room.toUpperCase() + ' - ' + title;
else if (s.kind === 'booth') calTitle = room.toUpperCase() + ' - ' + first(s.requester);
else if (s.kind === 'loc') calTitle = code + ' / ' + ini(engineerId);
else calTitle = [project.toUpperCase(), client, [ini(engineerId), ini(arrangerId)].filter(Boolean).join(' x ')].filter(Boolean).join(' / ');
const valid = Object.keys(errors).length === 0;
// the room offered as "not a usual room" (only when no usual room was free) is booked as asked - no second question
let notUsual = false;
try { for (const bl of (p.view.blocks || [])) if (bl.block_id === 'room') for (const o of (bl.element.options || []))
  if (o.value === room && o.description && /not a usual room/i.test(o.description.text || '')) notUsual = true; } catch (e) {}
if ([].concat(s.nu || []).indexOf(room) !== -1) notUsual = true;   // v10: remembered by step 2
const req = who(s.requester) || {};
const fmt = hm => { let [h, m] = String(hm).split(':').map(Number); const ap = h >= 12 ? 'pm' : 'am'; h = h % 12 || 12; return h + ':' + String(m).padStart(2, '0') + ' ' + ap; };
const KIND_WORDS = { Advertising: 'client work', Entertainment: 'client work', Internal: 'internal', Personal: 'personal project' };
// What the requester "typed", for Book Session's checks that read the requester's words: every value comes from the form.
const said = [
  (s.kind === 'booth' ? 'M booth' : s.purpose) + ' in ' + room + ' on ' + s.date + ' ' + fmt(s.t0) + '-' + fmt(s.t1),
  project ? 'project ' + project : '', code ? 'project code ' + code : '', title ? title : '',
  (s.kind === 'studio') ? (client ? 'client ' + client : 'no client') : '',
  engineerId ? 'engineer ' + nm(engineerId) : '',
  /music|band/i.test(s.purpose || '') ? (arrangerId ? 'arranger ' + nm(arrangerId) : (arrPick === 'none' ? 'no arranger' : '')) : '',
  kind ? (KIND_WORDS[kind] || kind) : '', dept ? dept : '', notes ? 'notes: ' + notes : ''
].filter(Boolean).join(', ');
const team = [engineerId, arrangerId].filter(Boolean).join(' ');
const descParts = [engineerId ? 'Engineer: ' + nm(engineerId) : '', arrangerId ? 'Arranger: ' + nm(arrangerId) : '',
  'Booked by: ' + (req.Name || ''), 'ref: ' + s.requester, team ? 'team: ' + team : '', notes ? 'Notes: ' + notes.replace(/\|/g, '/') : ''].filter(Boolean);
const staff = (data.bookers || []).map(b => b.fields || {}).filter(f => f.Name).map(f => ({ Name: f.Name, Initials: f.Initials || '', Info: f.Info || '',
  Department: f.Department || [], 'Default Type': f['Default Type'] || [] }));
const prep = {
  mode: 'prepare', summary: calTitle, start_iso: s.date + 'T' + s.t0 + ':00+08:00', end_iso: s.date + 'T' + s.t1 + ':00+08:00',
  rooms: room, description: descParts.join(' | '), all_day: false, exclude_event_id: '', confirmed: false,
  session_type: s.kind === 'booth' ? '' : s.purpose, client: s.kind === 'studio' ? client : '', room_override: notUsual,
  engineer: engineerId ? nm(engineerId) : '', bookingType: kind || '', series: false, department: dept || '',
  authority: [].concat(req.Authority || []).map(a => (a && a.name) || a).join(', '), expected_date: s.date,
  requester_text: said, require_prepared: false, prepared_ok: false, start_only: false, staff_data: JSON.stringify(staff),
  asked_text: s.asked || '', move_instead: '', series_alt: false, reference_data: ''
};
const working = { type: 'modal', clear_on_close: true, title: { type: 'plain_text', text: 'Book a room' }, close: { type: 'plain_text', text: 'Close' },
  private_metadata: JSON.stringify(s),
  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: '⏳ *Booking ' + room + '…*\n' + s.when } },
           { type: 'context', elements: [{ type: 'mrkdwn', text: 'This takes a few seconds.' }] }] };
return [{ json: { valid, calTitle, room, s, prep, team, descTail: descParts.filter(x => !/^(Engineer|Arranger):/.test(x)).join(' | '),
  viewId: (p.view && p.view.id) || '', channel: s.requester || c.user,
  answer: valid ? { response_action: 'update', view: working } : { response_action: 'errors', errors } } }];"""

TO_PREPARE = CACHE_JS + r"""
// To Prepare: Book Session's inputs for prepare mode, with the reference data built like main's Room Table.
const r = $('Read Step 2').first().json;
const data = readCache($('Read Cache 3').all().map(i => i.json || {})) || { rooms: [], sessionTypes: [] };
const refRooms = [];
for (const x of data.rooms || []) { const f = x.fields || {}; if (!x.id || !f['Room Name']) continue;
  const k = [].concat(f['Room Type'] || []).map(y => String(y).toLowerCase());
  refRooms.push({ id: x.id, name: String(f['Room Name']).trim(), vocalBooth: f['Vocal Booth'] === true,
    booth: f['Vocal Booth'] === true || k.indexOf('recording booth') !== -1, common: k.indexOf('conference room') !== -1 || k.indexOf('lobby') !== -1 }); }
const refTypes = []; const ranks = {};
for (const x of data.sessionTypes || []) { const f = x.fields || {}; const t = String(f['Type'] || '').trim(); if (!t) continue;
  refTypes.push({ type: t, min: f['Min Duration (mins)'] || null, max: f['Max Duration (mins)'] || null, typical: f['Typical Duration'] || null,
    roles: [].concat(f['Engineer Role Required'] || []), req: String(f['Room Requirements'] || ''), priority: [].concat(f['Priority'] || []), last: [].concat(f['Last Resort'] || []) });
  const rk = Number(f['Preemption Rank']); if (Number.isFinite(rk)) ranks[t] = rk; }
return [{ json: Object.assign({}, r.prep, { reference_data: JSON.stringify({ rooms: refRooms, types: refTypes, preemptionRanks: ranks }) }) }];"""

PROBLEM_JS = r"""
// The step-2 form again, as it was submitted (values kept), with the problem on top and, when Book Session needs one, an
// extra field (department, kind of booking). Shown by views.update on the same view.
function formAgain(warn, extra, asked) {
  const p = $('Read Request').first().json.payload || {};
  const V = p.view || {};
  const st = (V.state && V.state.values) || {};
  let meta = {}; try { meta = JSON.parse(V.private_metadata || '{}'); } catch (e) {}
  if (asked !== undefined) meta.asked = asked;
  const extraIds = (extra || []).map(b => b.block_id);
  const blocks = JSON.parse(JSON.stringify(V.blocks || [])).filter(b => b.block_id !== 'problem' && b.block_id !== 'problem_div' && extraIds.indexOf(b.block_id) === -1);
  for (const b of blocks) {
    if (b.type !== 'input' || !b.element) continue;
    const e = b.element, sv = (st[b.block_id] || {})[e.action_id] || {};
    if (e.type === 'plain_text_input') { if (sv.value) e.initial_value = sv.value; else delete e.initial_value; }
    else if (e.type === 'static_select' || e.type === 'radio_buttons') {
      const want = sv.selected_option && sv.selected_option.value;
      const all = (e.options || []).concat(...((e.option_groups || []).map(g => g.options || [])));
      const o = all.find(x => x.value === want);
      if (o) e.initial_option = o; else delete e.initial_option;
    }
  }
  // v10: the note checkbox keeps its tick
  for (const b of blocks) if (b.type === 'actions') for (const e of b.elements || []) if (e.type === 'checkboxes') {
    const sv = (st[b.block_id] || {})[e.action_id] || {};
    const on = (sv.selected_options || e.initial_options || []).map(o => o.value);
    const o = (e.options || []).filter(x => on.indexOf(x.value) !== -1);
    if (o.length) e.initial_options = o; else delete e.initial_options;
  }
  let at = blocks.findIndex(b => b.block_id === 'notes');
  if (at === -1) at = blocks.findIndex(b => b.block_id === 'note_toggle');
  if (extra && extra.length) blocks.splice(at === -1 ? blocks.length : at, 0, ...extra);
  blocks.unshift({ type: 'section', block_id: 'problem', text: { type: 'mrkdwn', text: '⚠️ ' + warn } }, { type: 'divider', block_id: 'problem_div' });
  return { type: 'modal', callback_id: 'book_step2', title: { type: 'plain_text', text: 'Book a room' }, submit: { type: 'plain_text', text: 'Book' },
           close: { type: 'plain_text', text: 'Back' }, private_metadata: JSON.stringify(meta), blocks };
}
const radioBlock = (bid, label, opts) => { const o = opts.map(x => ({ text: { type: 'plain_text', text: String(x) }, value: String(x) }));
  return { type: 'input', block_id: bid, label: { type: 'plain_text', text: label }, element: { type: 'radio_buttons', action_id: bid + '_pick', options: o } }; };
// Book Session's refusal -> words for the form (its own texts are written for the chat's AI, never shown as they are)
// v8: Book Session v110 passes the question's fields (typed, suggestions, options); before it, only its sentence (human)
// came through, so they are read from that sentence too, and the typed client from the form - a notice is never blank.
function formClient() { const st = ((($('Read Request').first().json.payload || {}).view || {}).state || {}).values || {};
  return String((st.client && st.client.client_in && st.client.client_in.value) || '').trim(); }
function problemFor(r) {
  const reason = r.reason || r.status || '';
  const human = String(r.human || '');
  const typed = String(r.typed || (human.match(/"([^"]+)" is not in the client list/) || [])[1] || formClient() || '').trim();
  if (reason === 'CLIENT_CHECK') {
    let sug = [].concat(r.suggestions || []).map(String).filter(Boolean);
    if (!sug.length) { const m = human.match(/close to (.+?)\. Ask the requester/); if (m) sug = m[1].split(/,\s*/).filter(Boolean); }
    if (!typed || !sug.length) return { warn: (typed ? '"' + typed + '"' : 'That client') + ' isn’t in the client list. Check the spelling, or press *Book* again to keep it as a new client.',
      asked: typed ? 'Is ' + typed + ' a new client?' : undefined };
    return { warn: '"' + typed + '" isn’t in the client list. Did you mean *' + sug.join('* or *') + '*? Change the client, or press *Book* again to keep "' + typed + '" as a new client.',
             asked: 'Did you mean ' + sug.join(' or ') + ', or is ' + typed + ' a new client?' };
  }
  if (reason === 'CLIENT_AMBIGUOUS') { const o = [].concat(r.options || []);
    return { warn: 'More than one client matches that name' + (o.length ? ': ' + o.join(', ') : '') + '. Type the full name.' }; }
  if (reason === 'AMBIGUOUS_PERSON') return { warn: (typed ? '"' + typed + '"' : 'That name') + ' is both a client' + (r.client ? ' (' + r.client + ')' : '') + ' and a staff member' + (r.staff ? ' (' + r.staff + ')' : '') + '. If it is the client, type their full name.' };
  if (reason === 'NEED_DEPARTMENT') { let o = [].concat(r.options || []).map(String).filter(Boolean);
    if (!o.length) { const m = human.match(/can be (.+?)\. Ask the requester/); if (m) o = m[1].split(/\s+or\s+/).filter(Boolean); }
    if (!o.length) o = ['Advertising', 'Entertainment', 'Localization', 'Music', 'Post Production'];
    return { warn: 'Which department is this session for?', extra: [radioBlock('department', 'Department', o.slice(0, 10))] }; }
  if (reason === 'NEED_BOOKING_TYPE') return { warn: 'What kind of booking is this?' + (r.askClient ? ' And who’s the client (or leave it empty for none)?' : ''),
    extra: [radioBlock('kind', 'Kind of booking', [].concat(r.options || []).length ? [].concat(r.options) : ['Advertising', 'Entertainment', 'Internal', 'Personal'])] };
  if (reason === 'NEED_CLIENT') return { warn: 'Who’s the client? Type the name, or leave it empty for no client.' };
  if (reason === 'NEED_ARRANGER') return { warn: 'Who’s the arranger? Pick one, or *No arranger*.' };
  if (reason === 'NEED_MEETING_TITLE') return { warn: 'Give the meeting a title.' };
  if (reason === 'ROOM_OCCUPIED') return { warn: 'That room was just booked by someone else for that time. Pick another room, or go *Back* to change the time.' };
  if (reason === 'ROOM_DECLINED' || r.status === 'ROOM_DECLINED') return { warn: 'The room turned the booking down - its own calendar shows it is taken then' + (r.removed === false ? '' : ', so it was taken off the calendar') + '. Pick another room, or go *Back* to change the time.' };
  if (reason === 'ROOM_UNSUITABLE' || reason === 'ROOM_NOT_PRIORITY' || reason === 'NO_ROOM' || reason === 'UNKNOWN_ROOM') return { warn: 'That room can’t be booked for this session. Pick another room.' };
  if (reason === 'ENGINEER_UNKNOWN' || reason === 'ENGINEER_UNVERIFIED' || reason === 'AMBIGUOUS_ENGINEER') return { warn: 'The engineer couldn’t be matched in Bookers. Pick the engineer again.' };
  if (reason === 'DURATION_INVALID') return { warn: 'That time doesn’t work - check the start and end.' };
  return { warn: 'This couldn’t be booked (' + (reason || 'no answer') + '). Check the details and press *Book* again, or go *Back*.' };
}
"""

AFTER_PREPARE = PROBLEM_JS + r"""
// After Prepare: PREPARED -> Book Session's inputs for the booking, read from what prepare returned (the same fields the
// chat's card shows - main's Prepared Booking does the same at the yes). Anything else -> the form again, with the question.
const r = $input.first().json || {};
const R = $('Read Step 2').first().json;
const T = $('To Prepare').first().json;
if (r.status !== 'PREPARED') {
  const pr = problemFor(r);
  return [{ json: { go: false, view_id: R.viewId, view: formAgain(pr.warn, pr.extra, pr.asked), reason: r.reason || r.status || '' } }];
}
let F = {}; try { F = (JSON.parse(r.prep_payload || '{}') || {}).F || {}; } catch (e) {}
const M = ['january','february','march','april','may','june','july','august','september','october','november','december'];
const dm = String(F['Date'] || '').match(/([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})/);
const mo = dm ? M.indexOf(dm[1].toLowerCase()) : -1;
const ymd = mo >= 0 ? dm[3] + '-' + String(mo + 1).padStart(2, '0') + '-' + String(+dm[2]).padStart(2, '0') : '';
const hhmm = x => { const m = String(x).match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i); if (!m) return null; return String((+m[1] % 12) + (/pm/i.test(m[3]) ? 12 : 0)).padStart(2, '0') + ':' + m[2]; };
const parts = String(F['Time'] || '').split(/\s*[–—-]\s*(?=\d)/);
const a = hhmm(parts[0]), b = hhmm(parts[1] || '');
let start_iso = r.final_start || T.start_iso, end_iso = r.final_end || T.end_iso;
if (ymd && a && b) { start_iso = ymd + 'T' + a + ':00+08:00'; end_iso = ymd + 'T' + b + ':00+08:00'; }
const engDesc = F['Engineer'] ? 'Engineer: ' + F['Engineer'] + (F['Arranger'] ? ' | Arranger: ' + F['Arranger'] : '') : '';
const book = Object.assign({}, T, {
  mode: '', confirmed: true, summary: F['Title'] || r.title || T.summary, start_iso, end_iso,
  rooms: F['Room'] || r.final_rooms || T.rooms, session_type: F['Session Type'] || T.session_type,
  client: /^none$/i.test(F['Client'] || '') ? '' : (F['Client'] || T.client), engineer: F['Engineer'] || T.engineer,
  department: F['Department'] || T.department, bookingType: F['Booking Type'] || T.bookingType,
  room_override: T.room_override || F['Override'] === 'yes',
  description: [engDesc, R.descTail].filter(Boolean).join(' | ')
});
return [{ json: { go: true, book, F } }];"""

AFTER_BOOK = PROBLEM_JS + r"""
// After Book: CREATED -> the form says Booked (Done closes it) and the DM gets the result; anything else -> the form again.
const r = $input.first().json || {};
const R = $('Read Step 2').first().json;
const A = $('After Prepare').first().json;
const F = A.F || {};
if (r.status !== 'CREATED') {
  const pr = problemFor(r);
  return [{ json: { ok: false, view_id: R.viewId, view: formAgain(pr.warn, pr.extra, pr.asked), channel: R.channel, text: '' } }];
}
const title = r.title || F['Title'] || R.calTitle;
// v8: the card's format - title, then Date, Time and Room (the chat's summary), on the form and in the DM. v10: a blank line after Booked.
const when = String((R.s && R.s.when) || '').split(' · ');
const card = '✅ *Booked.*\n\n*' + title + '*\n*Date:* ' + (F['Date'] || when[0] || '') + '\n*Time:* ' + (F['Time'] || when[1] || '')
  + '\n*Room:* ' + (F['Room'] || R.room);
const view = { type: 'modal', clear_on_close: true, title: { type: 'plain_text', text: 'Book a room' }, close: { type: 'plain_text', text: 'Done' },
  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: card } }] };
const text = card + (r.duration_note ? '\n' + r.duration_note : '');
return [{ json: { ok: true, view_id: R.viewId, view, channel: R.channel, text } }];"""

NOTE_TOGGLE = r"""// Note Toggle (v10): "Add a note" ticked -> the Notes field appears under it; unticked -> it goes. The form is rebuilt
// as it stands (entries kept) and replaced by views.update.
const p = $('Read Request').first().json.payload || {};
const V = p.view || {};
const st = (V.state && V.state.values) || {};
const a = (p.actions || [])[0] || {};
const on = (a.selected_options || []).length > 0;
const blocks = JSON.parse(JSON.stringify(V.blocks || [])).filter(b => b.block_id !== 'notes');
for (const b of blocks) {
  if (b.type !== 'input' || !b.element) continue;
  const e = b.element, sv = (st[b.block_id] || {})[e.action_id] || {};
  if (e.type === 'plain_text_input') { if (sv.value) e.initial_value = sv.value; else delete e.initial_value; }
  else if (e.type === 'static_select' || e.type === 'radio_buttons') {
    const want = sv.selected_option && sv.selected_option.value;
    const all = (e.options || []).concat(...((e.option_groups || []).map(g => g.options || [])));
    const o = all.find(x => x.value === want);
    if (o) e.initial_option = o; else delete e.initial_option;
  }
}
const at = blocks.findIndex(b => b.block_id === 'note_toggle');
if (at !== -1) {
  const cb = blocks[at].elements[0];
  if (on) cb.initial_options = cb.options; else delete cb.initial_options;
  if (on) blocks.splice(at + 1, 0, { type: 'input', block_id: 'notes', optional: true, label: { type: 'plain_text', text: 'Note' },
    element: { type: 'plain_text_input', action_id: 'notes_in', focus_on_load: true, placeholder: { type: 'plain_text', text: 'Anything the session needs' } } });
}
const view = { type: 'modal', callback_id: V.callback_id || 'book_step2', title: V.title, close: V.close, private_metadata: V.private_metadata || '', blocks };
if (V.submit) view.submit = V.submit;
return [{ json: { view_id: V.id || '', hash: V.hash || '', view, ok: at !== -1 && !!V.id } }];"""

MY_BOOKINGS = r"""// My bookings: step C. For now, say so.
const c = $('Check Signature').first().json;
return [{ json: { channel: c.user, text: 'My bookings comes in the next build. Until then, ask me "what do I have booked this week?"' } }];"""

# ------------------------------------------------------------------------------------------------- wiring
t = add({"parameters": {}, "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [0, -480], "id": nid(), "name": "Post Test Button"})
pb = slack("Send Button", "chat.postMessage",
           "={{ JSON.stringify({ channel: '" + TESTER + "', text: 'Hello form test', blocks: ["
           "{ type: 'section', text: { type: 'mrkdwn', text: '*Hello form test* - tap the button to open a test form.' } },"
           "{ type: 'actions', elements: [ { type: 'button', style: 'primary', action_id: 'hello_open', value: 'hello',"
           " text: { type: 'plain_text', text: 'Open test form' } } ] } ] }) }}", [240, -480])
link(t, pb)

wh = add({"parameters": {"httpMethod": "POST", "path": "jessie-interactions", "responseMode": "responseNode", "options": {"rawBody": True}},
          "type": "n8n-nodes-base.webhook", "typeVersion": 2, "position": [0, 0], "id": nid(), "name": "Slack Interactions", "webhookId": WEBHOOK_ID})
rr = code("Read Request", READ_REQUEST, [220, 0])
ts = code("To Sign", TO_SIGN, [420, 0])
sg = run_wf("Signature", SIGNATURE_WF, "Jessie — Slack Signature — v1", [620, 0])
ck = code("Check Signature", CHECK, [820, 0])
rt = add({"parameters": {"mode": "expression", "numberOutputs": 9, "output": "={{ $json.route }}"},
          "type": "n8n-nodes-base.switch", "typeVersion": 3.2, "position": [1040, 0], "id": nid(), "name": "Route"})
chain(wh, rr, ts, sg, ck, rt)

X = 1280
# 0 refused
a = respond("Refuse", [X, -700], status=401); b = code("Report Refused", REPORT_REFUSED, [X + 240, -700])
c_ = slack("DM Refused", "chat.postMessage", DM, [X + 480, -700])
link(rt, a, 0); chain(a, b, c_)
# 1 hello open
a = respond("Ack Click", [X, -560]); b = code("Build Form", BUILD_HELLO, [X + 240, -560])
c_ = slack("Open Form", "views.open", "={{ JSON.stringify({ trigger_id: $json.trigger_id, view: $json.view }) }}", [X + 480, -560])
d = code("Report Open", REPORT_OPEN, [X + 720, -560]); e = slack("DM Open Failed", "chat.postMessage", DM, [X + 960, -560])
link(rt, a, 1); chain(a, b, c_, d, e)
# 2 hello submit
a = code("Read Submission", READ_HELLO, [X, -420]); b = respond("Answer Working", [X + 240, -420], body="={{ JSON.stringify($json.working) }}")
w = add({"parameters": {"amount": 3}, "type": "n8n-nodes-base.wait", "typeVersion": 1.1, "position": [X + 480, -420], "id": nid(), "name": "Pretend Work", "webhookId": nid()})
u = slack("Update Form", "views.update", "={{ JSON.stringify({ view_id: $('Read Submission').first().json.viewId, view: $('Read Submission').first().json.done }) }}", [X + 720, -420])
rp = code("Report", REPORT_HELLO, [X + 960, -420]); dm = slack("DM Result", "chat.postMessage", DM, [X + 1200, -420])
link(rt, a, 2); chain(a, b, w, u, rp, dm)
# 3 other
link(rt, respond("Ack Other", [X, -280]), 3)


def read_cache(name, pos):
    return add({"parameters": {"operation": "get",
                               "dataTableId": {"__rl": True, "value": CACHE_TABLE, "mode": "list", "cachedResultName": "Jessie Reference Cache"},
                               "matchType": "allConditions", "filters": {"conditions": [{"keyName": "cache_key", "keyValue": "jessie-reference"}]},
                               "returnAll": True},
                "type": "n8n-nodes-base.dataTable", "typeVersion": 1, "position": pos, "id": nid(), "name": name,
                "executeOnce": True, "alwaysOutputData": True, "onError": "continueRegularOutput"})


# 4 Book a room -> step 1
a = respond("Ack Book", [X, -100]); b = read_cache("Read Cache", [X + 240, -100]); c_ = code("Build Step 1", BUILD_STEP1, [X + 480, -100])
d = slack("Open Step 1", "views.open", "={{ JSON.stringify({ trigger_id: $json.trigger_id, view: $json.view }) }}", [X + 720, -100])
e = code("Report Open 1", REPORT_OPEN, [X + 960, -100]); f = slack("DM Open 1 Failed", "chat.postMessage", DM, [X + 1200, -100])
link(rt, a, 4); chain(a, b, c_, d, e, f)
# 5 step 1 submitted -> push "finding rooms", then Room Availability, then update step 2
a = code("Read Step 1", READ_STEP1, [X, 80]); b = respond("Answer Step 1", [X + 240, 80], body="={{ JSON.stringify($json.answer) }}")
v_ = iff("Step 1 OK?", "={{ $('Read Step 1').first().json.valid }}", [X + 480, 80])
c_ = read_cache("Read Cache 2", [X + 720, 60]); d = code("To Room Availability", TO_RA, [X + 960, 60])
e = run_wf("Room Availability", ROOM_AVAIL_WF, "Jessie — Room Availability", [X + 1200, 60])
f = code("Build Step 2", BUILD_STEP2, [X + 1440, 60])
g = slack("Show Step 2", "views.update", "={{ JSON.stringify({ external_id: $json.external_id, view: $json.view }) }}", [X + 1680, 60])
link(rt, a, 5); chain(a, b, v_); link(v_, c_, 0); chain(c_, d, e, f, g)
# 6 step 2 submitted -> "Booking…" at once, then Book Session prepare, then book (or the form again with the question)
a = read_cache("Read Cache 3", [X, 260]); b = code("Read Step 2", READ_STEP2, [X + 240, 260])
c_ = respond("Answer Step 2", [X + 480, 260], body="={{ JSON.stringify($json.answer) }}")
v_ = iff("Step 2 OK?", "={{ $('Read Step 2').first().json.valid }}", [X + 720, 260])
tp = code("To Prepare", TO_PREPARE, [X + 960, 240])
pr = run_wf("Prepare", BOOK_SESSION_WF, "Jessie — Book Session", [X + 1200, 240])
ap = code("After Prepare", AFTER_PREPARE, [X + 1440, 240])
gp = iff("Prepared?", "={{ $json.go }}", [X + 1680, 240])
tb = code("To Book", "return [{ json: $('After Prepare').first().json.book }];", [X + 1920, 200])
bk = run_wf("Book", BOOK_SESSION_WF, "Jessie — Book Session", [X + 2160, 200])
ab = code("After Book", AFTER_BOOK, [X + 2400, 200])
sv = slack("Show Result", "views.update", "={{ JSON.stringify({ view_id: $json.view_id, view: $json.view }) }}", [X + 2640, 200])
ok_ = iff("Booked?", "={{ $('After Book').first().json.ok }}", [X + 2880, 200])
dmr = slack("DM Booked", "chat.postMessage", "={{ JSON.stringify({ channel: $('After Book').first().json.channel, text: $('After Book').first().json.text }) }}", [X + 3120, 180])
sp = slack("Show Question", "views.update", "={{ JSON.stringify({ view_id: $json.view_id, view: $json.view }) }}", [X + 1920, 320])
link(rt, a, 6); chain(a, b, c_, v_); link(v_, tp, 0); chain(tp, pr, ap, gp); link(gp, tb, 0); link(gp, sp, 1)
chain(tb, bk, ab, sv, ok_); link(ok_, dmr, 0)
# 7 My bookings -> not yet
a = respond("Ack My Bookings", [X, 440]); b = code("My Bookings", MY_BOOKINGS, [X + 240, 440]); c_ = slack("DM My Bookings", "chat.postMessage", DM, [X + 480, 440])
link(rt, a, 7); chain(a, b, c_)
# 8 Add a note (v10) -> answered at once, then the form again with or without the Notes field
a = respond("Ack Note", [X, 600]); b = code("Note Toggle", NOTE_TOGGLE, [X + 240, 600])
c_ = slack("Show Note", "views.update", "={{ JSON.stringify({ view_id: $json.view_id, hash: $json.hash, view: $json.view }) }}", [X + 480, 600])
link(rt, a, 8); chain(a, b, c_)

nodes.append({"parameters": {"content": "## Jessie — Slack Interactions\nEvery Slack button click and form submission. The signature comes from "
                             "**Jessie — Slack Signature** (nothing to paste).\n\n**v10 = slice 1 step B + typed requests + polish:** the menu's Book a room opens the two-step "
                             "booking form; Book books through Book Session (prepare, then book). My bookings: next build.\n\nRequest URL: "
                             "`https://signal.hitpromanila.net/webhook/jessie-interactions`", "height": 320, "width": 460},
              "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [-40, -820], "id": nid(), "name": "About"})

wf = {"name": "Jessie — Slack Interactions — v10 (form polish)", "nodes": nodes, "connections": conn,
      "settings": {"executionOrder": "v1"}, "pinData": {}, "active": False}
with open(OUT, "w") as fh:
    json.dump(wf, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(nodes), "nodes")
