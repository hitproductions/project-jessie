#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v5.json - "Jessie — Slack Interactions", v4: slice 1 step A (menu + booking form,
dry run).

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
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v5.json")

TESTER = "U08V3CKDGJF"
SLACK_CRED = {"slackApi": {"id": "EcX8szEJrOLYLUfl", "name": "Jessie Slack (signed)"}}
SIGNATURE_WF = "R06CBQNhFK0x4ZuO"
ROOM_AVAIL_WF = "e7tBQB458nstrqei"
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
const ROUTES = { refused: 0, hello_open: 1, hello_submit: 2, other: 3, open_book: 4, book_step1: 5, book_step2: 6, my_bookings: 7 };
let route = ROUTES.other;
if (!(sigOk && fresh)) route = ROUTES.refused;
else if (p.type === 'block_actions' && action === 'hello_open') route = ROUTES.hello_open;
else if (p.type === 'view_submission' && cb === 'hello_submit') route = ROUTES.hello_submit;
else if (p.type === 'block_actions' && action === 'open_book') route = ROUTES.open_book;
else if (p.type === 'block_actions' && action === 'my_bookings') route = ROUTES.my_bookings;
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
  options: NOT_SESSION.filter(t => types.indexOf(t) !== -1).map(t => opt(t)).concat([opt('Booth time (M booth)', '__booth')]) });
const m = new Date(Date.now() + 8 * 3600 * 1000);
const today = (m.getUTCFullYear() + YEAR_SHIFT) + '-' + String(m.getUTCMonth() + 1).padStart(2, '0') + '-' + String(m.getUTCDate()).padStart(2, '0');
const view = {
  type: 'modal', callback_id: 'book_step1',
  title: { type: 'plain_text', text: 'Book a room' },
  submit: { type: 'plain_text', text: 'Find rooms' }, close: { type: 'plain_text', text: 'Cancel' },
  private_metadata: JSON.stringify({ requester: c.user, channel: c.channel }),
  blocks: [
    { type: 'context', elements: [{ type: 'mrkdwn', text: '*Step 1 of 2* · when, and what for' }] },
    { type: 'input', block_id: 'date', label: { type: 'plain_text', text: 'Date' },
      element: { type: 'datepicker', action_id: 'date_pick', initial_date: today } },
    { type: 'input', block_id: 'start', label: { type: 'plain_text', text: 'Start' },
      element: { type: 'timepicker', action_id: 'start_pick', timezone: 'Asia/Manila' } },
    { type: 'input', block_id: 'end', label: { type: 'plain_text', text: 'End' },
      element: { type: 'timepicker', action_id: 'end_pick', timezone: 'Asia/Manila' } },
    { type: 'input', block_id: 'purpose', label: { type: 'plain_text', text: "What's it for?" },
      hint: { type: 'plain_text', text: 'Jessie offers the rooms that can do this, the usual ones first.' },
      element: { type: 'static_select', action_id: 'purpose_pick', placeholder: { type: 'plain_text', text: 'Choose' }, option_groups: groups } }
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
const t0 = (v.start && v.start.start_pick && v.start.start_pick.selected_time) || '';
const t1 = (v.end && v.end.end_pick && v.end.end_pick.selected_time) || '';
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
const label = s.kind === 'booth' ? 'Booth time' : s.purpose;
let rooms = [], note = '';
if (ra.status !== 'OK') {
  note = '⚠️ The calendar could not be checked (' + (ra.status || 'no answer') + '). Go Back and try again.';
} else if (s.kind === 'booth') {
  rooms = (ra.free_rooms || []).filter(r => /^M\d+$/i.test(r)).map((r, i) => opt(r, r, i === 0 ? 'Free then' : undefined));
} else {
  const pri = ra.free_priority || [], last = ra.free_last_resort || [];
  rooms = pri.map((r, i) => opt(r, r, (i === 0 ? 'Recommended · ' : '') + 'usual for ' + label));
  if (!rooms.length) rooms = last.map((r, i) => opt(r, r, (i === 0 ? 'Recommended · ' : '') + 'can do ' + label + ' · not a usual room'));
  const st = (data.sessionTypes || []).find(r => String((r.fields || {}).Type || '').trim() === s.purpose);
  const nameOf = {}; for (const r of data.rooms || []) nameOf[r.id] = String((r.fields || {})['Room Name'] || '').trim();
  const usual = st ? [].concat((st.fields || {}).Priority || []).map(id => nameOf[id]).filter(Boolean) : [];
  const taken = usual.filter(r => pri.indexOf(r) === -1);
  if (taken.length && rooms.length) note = 'Not free then: ' + taken.join(', ');
}
rooms = rooms.slice(0, 10);
const blocks = [ctx('*Step 2 of 2* · room and details'), { type: 'section', text: md('🗓️ *' + when + ' · ' + label + '*') }];
if (!rooms.length) {
  blocks.push({ type: 'section', text: md(note || ('Nothing that does ' + label + ' is free then. Go *Back* and try another time.')) });
} else {
  blocks.push(input('room', 'Room', { type: 'radio_buttons', action_id: 'room_radio', options: rooms, initial_option: rooms[0] }));
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
  if (me) engEl.initial_option = popt(me);
  const engineer = input('engineer', 'Engineer', engEl,
    { hint: { type: 'plain_text', text: me ? 'Set to you. Change it if someone else is engineering.' : 'Only engineers are listed (from Bookers).' } });
  const arrs = people.filter(p => /\bmusic arranger\b/i.test(p.info)).sort((a, b) => a.name.localeCompare(b.name));
  const meArr = arrs.find(p => p.slack === s.requester);
  const arrEl = { type: 'static_select', action_id: 'arranger_pick', placeholder: { type: 'plain_text', text: 'Choose' }, options: arrs.slice(0, 100).map(popt) };
  if (meArr) arrEl.initial_option = popt(meArr);
  const notes = input('notes', 'Notes', { type: 'plain_text_input', action_id: 'notes_in', multiline: true }, { optional: true });
  if (s.kind === 'meeting') {
    blocks.push(input('title', 'Meeting title', { type: 'plain_text_input', action_id: 'title_in' }), notes);
  } else if (s.kind === 'booth') {
    blocks.push(notes);
  } else if (s.kind === 'loc') {
    blocks.push(input('code', 'Project code', { type: 'plain_text_input', action_id: 'code_in' },
      { hint: { type: 'plain_text', text: 'As in Localization Projects. The client and the title come from it.' } }), engineer, notes);
  } else {
    blocks.push(input('project', 'Project', { type: 'plain_text_input', action_id: 'project_in' }),
      input('client', 'Client', { type: 'plain_text_input', action_id: 'client_in' },
        { optional: true, hint: { type: 'plain_text', text: "Leave empty if there's no client. A new name is fine." } }),
      engineer);
    if (/music|band/i.test(s.purpose))
      if (arrs.length) blocks.push(input('arranger', 'Arranger', arrEl, { optional: true }));
    blocks.push(notes);
  }
}
const view = { type: 'modal', callback_id: 'book_step2', title: { type: 'plain_text', text: 'Book a room' },
  close: { type: 'plain_text', text: 'Back' }, private_metadata: JSON.stringify(Object.assign({}, s, { when, label })), blocks };
if (rooms.length) view.submit = { type: 'plain_text', text: 'Book' };
return [{ json: { external_id: s.ext, view } }];"""

READ_STEP2 = CACHE_JS + r"""
// Read Step 2: the details, checked at once, and the calendar title built by code (no AI). STEP A = DRY RUN: the form
// answers with what would be booked; nothing is written to the calendar (step B: Book Session).
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
const arrangerId = val('arranger', 'arranger_pick');
const notes = String(val('notes', 'notes_in')).trim();
const errors = {};
if (!room) errors.room = 'Pick a room.';
if (s.kind === 'studio' && !project) errors.project = 'What is the project called?';
if (s.kind === 'loc' && !code) errors.code = 'Type the project code.';
if (s.kind === 'meeting' && !title) errors.title = 'Give the meeting a title.';
if ((s.kind === 'studio' || s.kind === 'loc') && !engineerId) errors.engineer = 'Pick the engineer.';
const data = readCache($('Read Cache 3').all().map(i => i.json || {})) || { bookers: [] };
const bySlack = {};
for (const b of data.bookers || []) { const f = b.fields || {}; String(f['Slack User ID'] || '').split(/[\s,]+/).filter(Boolean).forEach(id => { bySlack[id] = f; }); }
const who = id => bySlack[id] || null;
const ini = id => { const f = who(id); return f ? String(f.Initials || '').trim() : ''; };
if (engineerId && !who(engineerId)) errors.engineer = "That person isn't in Bookers yet - pick someone who is, or ask for them to be added.";
const first = id => { const f = who(id); return f ? String(f.Name || '').trim().split(/\s+/)[0] : ''; };
let calTitle = '';
if (s.kind === 'meeting') calTitle = room.toUpperCase() + ' - ' + title;
else if (s.kind === 'booth') calTitle = room.toUpperCase() + ' - ' + first(s.requester);
else if (s.kind === 'loc') calTitle = code + ' / ' + ini(engineerId);
else calTitle = [project.toUpperCase(), client, [ini(engineerId), ini(arrangerId)].filter(Boolean).join(' x ')].filter(Boolean).join(' / ');
const valid = Object.keys(errors).length === 0;
const lines = ['🧪 *Test run - nothing was booked.* This is what would be booked:', '',
  '*' + calTitle + '*', room + ' · ' + s.when, s.label,
  (engineerId ? 'Engineer: ' + ((who(engineerId) || {}).Name || engineerId) : ''),
  (arrangerId ? 'Arranger: ' + ((who(arrangerId) || {}).Name || arrangerId) : ''),
  (client && s.kind === 'studio' ? 'Client: ' + client + ' (checked against Clients when booking for real)' : ''),
  (notes ? 'Notes: ' + notes : '')].filter(x => x !== '');
const done = { type: 'modal', clear_on_close: true, title: { type: 'plain_text', text: 'Book a room' }, close: { type: 'plain_text', text: 'Done' },
  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: lines.join('\n') } },
           { type: 'context', elements: [{ type: 'mrkdwn', text: 'Step A of the Slack-app build: the real booking comes in step B.' }] }] };
return [{ json: { valid, calTitle, channel: s.requester || c.user, text: lines.join('\n'),
  answer: valid ? { response_action: 'update', view: done } : { response_action: 'errors', errors } } }];"""

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
rt = add({"parameters": {"mode": "expression", "numberOutputs": 8, "output": "={{ $json.route }}"},
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
# 6 step 2 submitted -> dry run
a = read_cache("Read Cache 3", [X, 260]); b = code("Read Step 2", READ_STEP2, [X + 240, 260])
c_ = respond("Answer Step 2", [X + 480, 260], body="={{ JSON.stringify($json.answer) }}")
v_ = iff("Step 2 OK?", "={{ $('Read Step 2').first().json.valid }}", [X + 720, 260])
d = slack("DM Test Run", "chat.postMessage", "={{ JSON.stringify({ channel: $('Read Step 2').first().json.channel, text: $('Read Step 2').first().json.text }) }}", [X + 960, 240])
link(rt, a, 6); chain(a, b, c_, v_); link(v_, d, 0)
# 7 My bookings -> not yet
a = respond("Ack My Bookings", [X, 440]); b = code("My Bookings", MY_BOOKINGS, [X + 240, 440]); c_ = slack("DM My Bookings", "chat.postMessage", DM, [X + 480, 440])
link(rt, a, 7); chain(a, b, c_)

nodes.append({"parameters": {"content": "## Jessie — Slack Interactions\nEvery Slack button click and form submission. The signature comes from "
                             "**Jessie — Slack Signature** (nothing to paste).\n\n**v5 = slice 1 step A:** the menu's Book a room opens the two-step "
                             "booking form; Book is a dry run (nothing written). My bookings: next build.\n\nRequest URL: "
                             "`https://signal.hitpromanila.net/webhook/jessie-interactions`", "height": 320, "width": 460},
              "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [-40, -820], "id": nid(), "name": "About"})

wf = {"name": "Jessie — Slack Interactions — v5 (engineers A to Z)", "nodes": nodes, "connections": conn,
      "settings": {"executionOrder": "v1"}, "pinData": {}, "active": False}
with open(OUT, "w") as fh:
    json.dump(wf, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(nodes), "nodes")
