#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v17.json - "Jessie — Slack Interactions", v17: build A - wording, cards, buttons.

v17 (15 Oct, build A of the notes from the slice 1 Slack test; with main v269): the Booking… screen says "Your booking is
being processed. This takes a few seconds."; the Change form's bottom note is gone; a cancel or a change started from a
message shows "⏳ Your cancellation / change is being processed…" under that booking (its buttons hidden) until it is done -
a change that fails puts the row back; Cancelled and Changed are the card (like Booked) and a one-booking reply loses its
"Here's…" line once done; "Or until": 'Only applies if "How many times" is empty.'; the series screens say "Checking
availability for each date. This takes a few seconds." and "Processing your series of bookings. This may take a while, so
you can close this window for now. You will be notified once finished."; the series result DM has Book a room / My
bookings. Built on v16 (live; download workflows/imported/slack-interactions-v16-imported.json).

v16 (My bookings shows - fixes v11):

v16 (15 Oct, Slack test: "clicking My bookings doesn't do anything"): the week's message never arrived - its Previous /
Next 7 days buttons shared one action_id (my_page), which Slack refuses (action_ids must differ within a block), so
chat.postMessage failed and nothing said so. They are my_page_prev / my_page_next now (routed as before), and if Slack
refuses the My bookings message the person gets a DM with Slack's reason (Report List). Built on v15 (live; download
workflows/imported/slack-interactions-v15-imported.json).

v15 (series fixes from the Slack test):

v15 (15 Oct, from the series test; fixes v13 / v14): booking a confirmed series failed on every date with NO_REFERENCE_DATA
- To Book Series passed Book Series an empty room list (and no staff list / authority); it now builds them from the
reference cache, as the prepare step does. No refusal code reaches the requester any more: the series result and the
single-booking, Change and Cancel messages say it in words (an unknown code gets a plain line). Repeats: "How many times"
wins when it is set and "Or until" is used only when it is empty (a picked date cannot be cleared in Slack); "Or until"
starts four weeks after the first date, so its picker opens in the right year (it opened on the real 2026 during QA).
Step 1: "A room will be recommended to you based on your session details."; the purpose groups are "Sessions" and
"Other bookings". Built on v14 (live; download workflows/imported/slack-interactions-v14-imported.json).

v14 (Repeats filled in from a typed series):

v14 (typed series -> form, 15 Oct; with main v268): main's reply to a typed repeating booking puts the pattern on the Book a
room button (rep: {f: weekly / weekdays / daily, days, n, u}); step 1 then opens with Repeats ticked and How often, On,
How many times and Or until filled in. The Repeats fields are built by one function for both the ticked box and the
filled-in form. Built on v13 (live; download workflows/imported/slack-interactions-v13-imported.json).

v13 (series - Repeats in the form):

v13 (series, 15 Oct): step 1 has a small **Repeats** box on every booking. Ticking it (route 8, answered at once, then the
form again with the entries kept) adds How often (every week / every weekday / every day), On (the days, for weekly; the
date's weekday ticked), How many times (2-16) and an optional end date. Find rooms checks every date (Room Availability
once per date) and step 2 says on how many dates each room is free. Its button checks the dates: Book Series in prepare
mode runs every date through Book Session's checks (a taken date gets another room or time where one is free, or is left
out) and stores the series; the form shows the dates and what changed, with "Book N dates" (route 13, series_confirm).
That books exactly the stored series through Book Series - a few minutes for a batch - and the result (booked / not
booked) comes to the form and the DM. Built on v12 (live; download workflows/imported/slack-interactions-v12-imported.json).

v12 (step C2: Change opens at the time typed):

v12 (step C2, 15 Oct; with main v265): main's reply to a typed change ("make it 3-5pm", "move it to friday") puts the new
values on the Change button ({..., n: {d, s, e, r}}). The Change form then starts at them (a start alone keeps the
booking's length) - "Now:" still shows the booking as it is, and "Nothing changed" still compares with that.
Built on v11 (live; download workflows/imported/slack-interactions-v11-imported.json).

v11 (step C1 - My bookings, Change, Cancel):

v11 (step C1, 15 Oct): every booking shown in a message carries **Change** and **Cancel** buttons (the Booked DM and My
bookings). Cancel asks first with Slack's own pop-up ("Cancel this booking?"), then Cancel Booking (v27: the booker, the
engineer or the arranger may) and the message updates in place ("❌ Cancelled: …", or why not). Change opens a form at
the booking's current date, times and room (rooms of the same kind); pressing Change with nothing changed says so on the
form; otherwise Move Booking (v30) checks the new time and moves it - the form says Changed (or the problem, entries
kept, with the room's free times that day) and the message's row updates to the new time. My bookings: the next 7 days
of bookings the person made or engineers / arranges, each with Change / Cancel, and Previous / Next 7 days buttons that
update the same message. Routes 9 bk_cancel, 10 bk_change, 11 change_booking (submit), 12 my_page; 7 my_bookings is real.
Typed cancel / change (step C2, main) comes next. Built on v10 (live; download workflows/imported/slack-interactions-v10-imported.json).

v10 (form polish from the v9 Slack test):

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
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v17.json")

TESTER = "U08V3CKDGJF"
SLACK_CRED = {"slackApi": {"id": "EcX8szEJrOLYLUfl", "name": "Jessie Slack (signed)"}}
SIGNATURE_WF = "R06CBQNhFK0x4ZuO"
ROOM_AVAIL_WF = "e7tBQB458nstrqei"
BOOK_SESSION_WF = "EUG3sGXkfsJSYIMz"
CANCEL_WF = "bAyDw7udhmY0NL38"
MOVE_WF = "t7lwR2km4tfN8DbM"
SERIES_WF = "UAwFoifgkfL1xNP2"
CAL = "c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com"
GCAL_CRED = {"googleCalendarOAuth2Api": {"id": "6D1r3kaq6KaFdL0a", "name": "Google Calendar account"}}
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

REP_JS = r"""
// The Repeats fields (v13; one function since v14 - the ticked box and a typed series both use it): How often, On (the
// days, for every week), How many times, Or until. rep = {f, days, n, u} fills them in; otherwise every week on the
// first date's day.
function repBlocks(date, rep) {
  rep = rep || {};
  const pt = x => ({ type: 'plain_text', text: x });
  const K = ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'], NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const dayOpts = [1, 2, 3, 4, 5, 6, 0].map(i => ({ text: pt(NAMES[i]), value: K[i] }));
  const wd = /^\d{4}-\d{2}-\d{2}$/.test(String(date || '')) ? new Date(date + 'T12:00:00Z').getUTCDay() : 1;
  const freq = [{ text: pt('Every week'), value: 'weekly' }, { text: pt('Every weekday (Mon–Fri)'), value: 'weekdays' }, { text: pt('Every day'), value: 'daily' }];
  const counts = []; for (let i = 2; i <= 16; i++) counts.push({ text: pt(i + ' times'), value: String(i) });
  const days = [].concat(rep.days || []).filter(k => K.indexOf(k) !== -1);
  const dIni = dayOpts.filter(o => (days.length ? days : [K[wd]]).indexOf(o.value) !== -1);
  const cIni = counts.find(o => o.value === String(rep.n || ''));
  // v15: "Or until" starts four weeks after the first date - the picker opens in the right year (QA runs a year ahead)
  const u0 = /^\d{4}-\d{2}-\d{2}$/.test(String(rep.u || '')) ? rep.u
    : (/^\d{4}-\d{2}-\d{2}$/.test(String(date || '')) ? new Date(Date.parse(date + 'T12:00:00Z') + 28 * 86400000).toISOString().slice(0, 10) : '');
  const until = Object.assign({ type: 'datepicker', action_id: 'rep_until_pick' }, u0 ? { initial_date: u0 } : {});
  return [
    { type: 'input', block_id: 'rep_freq', label: pt('How often'), element: { type: 'static_select', action_id: 'rep_freq_pick', options: freq, initial_option: freq.find(o => o.value === rep.f) || freq[0] } },
    { type: 'input', block_id: 'rep_days', optional: true, label: pt('On'), hint: pt('For every week. The first date’s day is ticked.'),
      element: { type: 'checkboxes', action_id: 'rep_days_pick', options: dayOpts, initial_options: dIni } },
    { type: 'input', block_id: 'rep_count', optional: true, label: pt('How many times'), element: Object.assign({ type: 'static_select', action_id: 'rep_count_pick', placeholder: pt('Choose'), options: counts }, cIni ? { initial_option: cIni } : {}) },
    { type: 'input', block_id: 'rep_until', optional: true, label: pt('Or until'), hint: pt('Only applies if "How many times" is empty.'), element: until },
    { type: 'context', block_id: 'rep_note', elements: [{ type: 'mrkdwn', text: 'Up to 16 dates. Each one is checked before anything is booked.' }] }];
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
const ROUTES = { refused: 0, hello_open: 1, hello_submit: 2, other: 3, open_book: 4, book_step1: 5, book_step2: 6, my_bookings: 7, note_toggle: 8, bk_cancel: 9, bk_change: 10, change_booking: 11, my_page: 12, series_confirm: 13 };
let route = ROUTES.other;
if (!(sigOk && fresh)) route = ROUTES.refused;
else if (p.type === 'block_actions' && action === 'hello_open') route = ROUTES.hello_open;
else if (p.type === 'view_submission' && cb === 'hello_submit') route = ROUTES.hello_submit;
else if (p.type === 'block_actions' && action === 'open_book') route = ROUTES.open_book;
else if (p.type === 'block_actions' && action === 'my_bookings') route = ROUTES.my_bookings;
else if (p.type === 'block_actions' && (action === 'note_toggle' || action === 'repeat_toggle')) route = ROUTES.note_toggle;   // v10; v13 Repeats
else if (p.type === 'view_submission' && cb === 'series_confirm') route = ROUTES.series_confirm;   // v13
else if (p.type === 'block_actions' && action === 'bk_cancel') route = ROUTES.bk_cancel;   // v11
else if (p.type === 'block_actions' && action === 'bk_change') route = ROUTES.bk_change;
else if (p.type === 'block_actions' && /^my_page/.test(action)) route = ROUTES.my_page;   // v16: my_page_prev / my_page_next
else if (p.type === 'view_submission' && cb === 'change_booking') route = ROUTES.change_booking;
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
BUILD_STEP1 = CACHE_JS + REP_JS + r"""
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
groups.push({ label: { type: 'plain_text', text: 'Other bookings' },
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
      hint: { type: 'plain_text', text: 'A room will be recommended to you based on your session details.' },
      element: Object.assign({ type: 'static_select', action_id: 'purpose_pick', placeholder: { type: 'plain_text', text: 'Choose' }, option_groups: groups }, purposeOpt ? { initial_option: purposeOpt } : {}) },
    // v13: a small Repeats box on every booking; ticking it adds the series fields (route 8)
    { type: 'actions', block_id: 'repeat_toggle', elements: [{ type: 'checkboxes', action_id: 'repeat_toggle',
      options: [{ text: { type: 'plain_text', text: 'Repeats' }, value: 'rep' }] }] }
  ]
};
// v14: a typed series (main v268) - Repeats ticked and filled in
if (pre.rep && typeof pre.rep === 'object') {
  const i = view.blocks.findIndex(b => b.block_id === 'repeat_toggle');
  if (i !== -1) { const cb = view.blocks[i].elements[0]; cb.initial_options = cb.options;
    view.blocks.splice(i + 1, 0, ...repBlocks(/^\d{4}-\d{2}-\d{2}$/.test(String(pre.d || '')) ? pre.d : today, pre.rep)); }
}
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
// v13: Repeats ticked -> the dates, worked out here (as Book Series' Expand Dates does): weekly on the days ticked, every
// weekday, or every day; from the date, a number of times or until an end date; 2 to 16 dates.
const repOn = !!(v.repeat_toggle && v.repeat_toggle.repeat_toggle && (v.repeat_toggle.repeat_toggle.selected_options || []).length) && !!v.rep_freq;
let series = null;
if (repOn && date) {
  const freq = (v.rep_freq.rep_freq_pick && v.rep_freq.rep_freq_pick.selected_option && v.rep_freq.rep_freq_pick.selected_option.value) || 'weekly';
  const DOWK = { SU: 0, MO: 1, TU: 2, WE: 3, TH: 4, FR: 5, SA: 6 };
  let days = ((v.rep_days && v.rep_days.rep_days_pick && v.rep_days.rep_days_pick.selected_options) || []).map(o => o.value);
  if (freq === 'weekdays') days = ['MO', 'TU', 'WE', 'TH', 'FR'];
  const count = Number((v.rep_count && v.rep_count.rep_count_pick && v.rep_count.rep_count_pick.selected_option && v.rep_count.rep_count_pick.selected_option.value) || 0);
  // v15: How many times wins when set; Or until only when it is empty (a picked date cannot be cleared in Slack)
  const until = count ? '' : ((v.rep_until && v.rep_until.rep_until_pick && v.rep_until.rep_until_pick.selected_date) || '');
  if (freq === 'weekly' && !days.length) errors.rep_days = 'Pick at least one day.';
  else if (!count && !until) errors.rep_count = 'How many times - or pick an end date.';
  else if (until && until <= date) errors.rep_until = 'The end date has to be after the first date.';
  else {
    const want = new Set(days.map(d => DOWK[d]));
    const dates = []; const cur = new Date(date + 'T12:00:00Z');
    for (let g = 0; g < 400 && dates.length < 17; g++) {
      const d = cur.toISOString().slice(0, 10);
      if (until && d > until) break;
      if (freq === 'daily' || want.has(cur.getUTCDay())) dates.push(d);
      if (count && dates.length >= count) break;
      cur.setUTCDate(cur.getUTCDate() + 1);
    }
    if (dates.length > 16) errors.rep_until = 'That is more than 16 dates - pick an earlier end date, or a number.';
    else if (dates.length < 2) errors[until ? 'rep_until' : 'rep_count'] = 'That gives only one date - untick Repeats for a single booking.';
    else series = { freq, days, dates };
  }
}
const valid = Object.keys(errors).length === 0;
const ext = 's2-' + (c.user || 'x') + '-' + Date.now();
const kind = purpose === '__booth' ? 'booth' : (purpose === 'Meeting' || purpose === 'Event') ? 'meeting'
  : /^localization/i.test(purpose) ? 'loc' : 'studio';
const s = { date, t0, t1, purpose, kind, requester: meta.requester || c.user, channel: meta.channel || '', ext };
if (meta.pre && typeof meta.pre === 'object') s.pre = meta.pre;   // v9: what main read, for step 2
if (series) s.series = series;   // v13
const loading = { type: 'modal', external_id: ext, callback_id: 'book_step2',
  title: { type: 'plain_text', text: 'Book a room' }, close: { type: 'plain_text', text: 'Back' },
  private_metadata: JSON.stringify(s),
  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: series ? '⏳ *Checking ' + series.dates.length + ' dates…*' : '⏳ *Finding free rooms…*' } }] };
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
// v13: a series -> one Room Availability call per date (Build Step 2 counts on how many dates each room is free)
const ref = JSON.stringify({ rooms: refRooms, types: refTypes, preemptionRanks });
const days = (s.series && Array.isArray(s.series.dates) && s.series.dates.length) ? s.series.dates : [s.date];
return days.map(d => ({ json: {
  // Always Philippine Time: the pickers carry no time zone, so the picked hh:mm is taken as Manila time (+08:00).
  start_iso: d + 'T' + s.t0 + ':00+08:00', end_iso: d + 'T' + s.t1 + ':00+08:00',
  session_type: s.kind === 'booth' ? '' : s.purpose, room: '', scope: '', hours: '', reference_data: ref
} }));"""

BUILD_STEP2 = CACHE_JS + r"""
// Build Step 2: the free rooms that fit (ranked; usual first, others only when no usual room is free), then the details
// for this kind of booking. Replaces the "Finding free rooms…" view by its external_id.
const s = $('Read Step 1').first().json.s;
// v13: a series - Room Availability answered once per date; a room is offered when it is free on at least one date,
// those free on more dates first
const RAS = $input.all().map(i => i.json || {});
const SER = (s.series && Array.isArray(s.series.dates) && s.series.dates.length > 1) ? s.series : null;
const cnt = {};
let ra = RAS[0] || {};
if (SER) {
  const pri = [], last = [], fr = [], add = (a, r) => { if (a.indexOf(r) === -1) a.push(r); };
  for (const x of RAS) {
    const here = new Set([].concat(x.free_priority || [], x.free_last_resort || [], s.kind === 'booth' ? (x.free_rooms || []) : []));
    for (const r of x.free_priority || []) add(pri, r);
    for (const r of x.free_last_resort || []) add(last, r);
    for (const r of x.free_rooms || []) add(fr, r);
    here.forEach(r => { cnt[r] = (cnt[r] || 0) + 1; });
  }
  const byCount = a => a.map((r, i) => ({ r, i })).sort((x, y) => (cnt[y.r] || 0) - (cnt[x.r] || 0) || x.i - y.i).map(x => x.r);
  const bad = RAS.find(x => x.status !== 'OK');
  ra = { status: bad ? bad.status : 'OK', free_priority: byCount(pri), free_last_resort: byCount(last.filter(r => pri.indexOf(r) === -1)), free_rooms: byCount(fr) };
}
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
  note = '⚠️ The calendar couldn’t be checked just now. Go *Back* and try again.';   // v15: no code shown
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
// v13: a series - each room says on how many of the dates it is free
if (SER) { const N = SER.dates.length;
  rooms = rooms.map(o => { const k = cnt[o.value] || 0, tail = k >= N ? 'free on all ' + N + ' dates' : 'free on ' + k + ' of ' + N + ' dates';
    const d = o.description ? o.description.text + ' · ' + tail : (k >= N ? '' : tail);
    return d ? Object.assign({}, o, { description: { type: 'plain_text', text: d.slice(0, 75) } }) : o; });
  if (preRoom) preRoom = rooms.find(o => o.value === preRoom.value) || preRoom; }
const _DS2 = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
const serShort = d => { const x = new Date(d + 'T12:00:00Z'); return _DS2[x.getUTCDay()] + ' ' + MON[x.getUTCMonth()] + ' ' + x.getUTCDate(); };
const blocks = [ctx('*Step 2 of 2* · room and details'), { type: 'section', text: md(SER
  ? '🗓️ *' + SER.dates.length + ' dates · ' + fmtT(s.t0) + '–' + fmtT(s.t1) + ' · ' + label + '*'
  : '🗓️ *' + when + ' · ' + label + '*') }];
if (SER) blocks.push(ctx(SER.dates.map(serShort).join(' · ')));
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
if (rooms.length) view.submit = { type: 'plain_text', text: SER ? 'Check ' + SER.dates.length + ' dates' : 'Book' };   // v13
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
  blocks: (s.series && (s.series.dates || []).length > 1)
    ? [{ type: 'section', text: { type: 'mrkdwn', text: '⏳ *Checking ' + s.series.dates.length + ' dates in ' + room + '…*' } },
       { type: 'context', elements: [{ type: 'mrkdwn', text: 'Checking availability for each date. This takes a few seconds.' }] }]
    : [{ type: 'section', text: { type: 'mrkdwn', text: '⏳ *Booking ' + room + '…*\n' + s.when } },
       { type: 'context', elements: [{ type: 'mrkdwn', text: 'Your booking is being processed. This takes a few seconds.' }] }] };
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

ROW_JS = r"""
// Booking rows (v11): a booking in a message is a section (block_id bk_<id>) and its Change / Cancel buttons (bka_<id>).
// The buttons carry the booking: {id, d: YYYY-MM-DD, s / e: HH:MM (Manila), r: room, t: title}.
const _DS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'], _MS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const _DL = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'], _ML = ['January','February','March','April','May','June','July','August','September','October','November','December'];
function t12(hm) { if (!hm) return ''; let [h, m] = String(hm).split(':').map(Number); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(m).padStart(2, '0') + ' ' + ap; }
function dayShort(d) { const x = new Date(d + 'T12:00:00Z'); return _DS[x.getUTCDay()] + ', ' + _MS[x.getUTCMonth()] + ' ' + x.getUTCDate(); }
function dayLong(d) { const x = new Date(d + 'T12:00:00Z'); return _DL[x.getUTCDay()] + ', ' + _ML[x.getUTCMonth()] + ' ' + x.getUTCDate() + ', ' + x.getUTCFullYear(); }
function addDays(d, n) { return new Date(Date.parse(d + 'T12:00:00Z') + n * 86400000).toISOString().slice(0, 10); }
function whenLine(b) { return dayShort(b.d) + ' · ' + (b.s ? t12(b.s) + ' – ' + t12(b.e) : 'all day') + (b.r ? ' · ' + b.r : ''); }
function bkValue(b) { return JSON.stringify({ id: b.id, d: b.d, s: b.s || '', e: b.e || '', r: b.r || '', t: String(b.t || '').slice(0, 150) }); }
function bkButtons(b) {
  const pt = x => ({ type: 'plain_text', text: x });
  return { type: 'actions', block_id: 'bka_' + b.id, elements: [
    { type: 'button', action_id: 'bk_change', value: bkValue(b), text: pt('Change') },
    { type: 'button', action_id: 'bk_cancel', style: 'danger', value: bkValue(b), text: pt('Cancel'),
      confirm: { title: pt('Cancel this booking?'), text: { type: 'mrkdwn', text: ('*' + b.t + '*\n' + whenLine(b)).slice(0, 290) },
                 confirm: pt('Cancel booking'), deny: pt('Keep it'), style: 'danger' } } ] };
}
function bkCard(b, head) { return head + '\n\n*' + b.t + '*\n*Date:* ' + dayLong(b.d) + '\n*Time:* ' + (b.s ? t12(b.s) + ' – ' + t12(b.e) : 'All day') + '\n*Room:* ' + (b.r || '-'); }
// a Google event -> a booking (Manila times; the room from its room attendee, else its location)
function evRoom(e) { const r = (e.attendees || []).filter(a => a.resource || /@resource\.calendar\.google\.com$/i.test(String(a.email || '')))
  .map(a => String(a.displayName || '').replace(/^KDC Plaza-Top Level-/i, '').replace(/\s*\(\d+\)\s*$/, '').trim()).filter(Boolean);
  return r.length ? r.join(', ') : String(e.location || '').replace(/^KDC Plaza-Top Level-/i, '').replace(/\s*\(\d+\)\s*$/, '').trim(); }
function evBooking(e) {
  const sd = e.start && e.start.dateTime, ed = e.end && e.end.dateTime;
  const m = x => { const d = new Date(new Date(x).getTime() + 8 * 3600000); return { d: d.toISOString().slice(0, 10), hm: d.toISOString().slice(11, 16) }; };
  if (sd) { const a = m(sd), b = m(ed); return { id: e.id, d: a.d, s: a.hm, e: b.hm, r: evRoom(e), t: e.summary || '(no title)' }; }
  return { id: e.id, d: String((e.start && e.start.date) || ''), s: '', e: '', r: evRoom(e), t: e.summary || '(no title)' };
}
"""

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
  if (reason === 'NO_REFERENCE_DATA' || reason === 'UNVERIFIABLE' || reason === 'LOOKUP_FAILED' || reason === 'CALENDAR_ERROR') return { warn: 'The room list or the calendar couldn’t be read just now. Press *Book* again in a moment.' };   // v15
  return { warn: 'This couldn’t be booked. Check the details and press *Book* again, or go *Back*.' };   // v15: no code shown
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

AFTER_BOOK = PROBLEM_JS + ROW_JS + r"""
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
// v11: the DM carries Change / Cancel for this booking
const T = A.book || {};
const iso = x => String(x || '').match(/^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})/) || [];
const si = iso(T.start_iso), ei = iso(T.end_iso);
const bk = { id: String(r.event_id || ''), d: si[1] || (R.s && R.s.date) || '', s: si[2] || (R.s && R.s.t0) || '', e: ei[2] || (R.s && R.s.t1) || '',
  r: F['Room'] || R.room || '', t: title };
const blocks = [{ type: 'section', block_id: 'bk_' + (bk.id || 'new'), text: { type: 'mrkdwn', text } }].concat(bk.id ? [bkButtons(bk)] : []);
return [{ json: { ok: true, view_id: R.viewId, view, channel: R.channel, text, blocks } }];"""

NOTE_TOGGLE = REP_JS + r"""// Note Toggle (v10; v13 also Repeats): "Add a note" ticked -> the Notes field appears under it; "Repeats" ticked -> How
// often, On (days), How many times and an end date appear under it; unticked -> they go. The form is rebuilt as it stands
// (entries kept) and replaced by views.update.
const p = $('Read Request').first().json.payload || {};
const V = p.view || {};
const st = (V.state && V.state.values) || {};
const a = (p.actions || [])[0] || {};
const on = (a.selected_options || []).length > 0;
const which = a.action_id === 'repeat_toggle' ? 'repeat_toggle' : 'note_toggle';
const OWN = which === 'repeat_toggle' ? ['rep_freq', 'rep_days', 'rep_count', 'rep_until', 'rep_note'] : ['notes'];
const blocks = JSON.parse(JSON.stringify(V.blocks || [])).filter(b => OWN.indexOf(b.block_id) === -1);
for (const b of blocks) {
  if (b.type === 'actions') { for (const e of b.elements || []) if (e.type === 'checkboxes' && b.block_id !== which) {   // the other box keeps its tick
    const sv = (st[b.block_id] || {})[e.action_id] || {}; const vals = (sv.selected_options || e.initial_options || []).map(o => o.value);
    const o = (e.options || []).filter(x => vals.indexOf(x.value) !== -1); if (o.length) e.initial_options = o; else delete e.initial_options; } continue; }
  if (b.type !== 'input' || !b.element) continue;
  const e = b.element, sv = (st[b.block_id] || {})[e.action_id] || {};
  if (e.type === 'plain_text_input') { if (sv.value) e.initial_value = sv.value; else delete e.initial_value; }
  else if (e.type === 'static_select' || e.type === 'radio_buttons') {
    const want = sv.selected_option && sv.selected_option.value;
    const all = (e.options || []).concat(...((e.option_groups || []).map(g => g.options || [])));
    const o = all.find(x => x.value === want);
    if (o) e.initial_option = o; else if (want === undefined && e.initial_option) {} else delete e.initial_option;
  }
  else if (e.type === 'datepicker') { if (sv.selected_date) e.initial_date = sv.selected_date; }
  else if (e.type === 'checkboxes') { const vals = (sv.selected_options || []).map(o => o.value); const o = (e.options || []).filter(x => vals.indexOf(x.value) !== -1);
    if (o.length) e.initial_options = o; else delete e.initial_options; }
}
const pt = x => ({ type: 'plain_text', text: x });
const at = blocks.findIndex(b => b.block_id === which);
if (at !== -1) {
  const cb = blocks[at].elements[0];
  if (on) cb.initial_options = cb.options; else delete cb.initial_options;
  if (on && which === 'note_toggle') blocks.splice(at + 1, 0, { type: 'input', block_id: 'notes', optional: true, label: pt('Note'),
    element: { type: 'plain_text_input', action_id: 'notes_in', focus_on_load: true, placeholder: pt('Anything the session needs') } });
  if (on && which === 'repeat_toggle') {
    const date = ((st.date || {}).date_pick || {}).selected_date || ((blocks.find(b => b.block_id === 'date') || {}).element || {}).initial_date || '';
    blocks.splice(at + 1, 0, ...repBlocks(date, null));
  }
}
const view = { type: 'modal', callback_id: V.callback_id || 'book_step2', title: V.title, close: V.close, private_metadata: V.private_metadata || '', blocks };
if (V.submit) view.submit = V.submit;
return [{ json: { view_id: V.id || '', hash: V.hash || '', view, ok: at !== -1 && !!V.id } }];"""

TO_PREPARE_SERIES = r"""
// To Prepare Series (v13): Book Series in prepare mode - every date through Book Session's checks (a taken date gets another
// room or time where one is free, or is left out), and the series stored for the confirm screen.
const T = $('To Prepare').first().json;
const R = $('Read Step 2').first().json;
return [{ json: { mode: 'prepare', confirmed: false, dates: R.s.series.dates.join(','), time_start: R.s.t0, time_end: R.s.t1, all_day: false,
  summary: T.summary, rooms: T.rooms, session_type: T.session_type, client: T.client, engineer: T.engineer, description: T.description,
  bookingType: T.bookingType, department: T.department, reference_data: T.reference_data, requester_text: T.requester_text,
  asked_text: T.asked_text, staff_data: T.staff_data, authority: T.authority, room_override: T.room_override === true,
  frequency: '', by_days: '', start_date: '', count: null, until_date: '', changes: '', per_date: '' } }];"""

AFTER_PREPARE_SERIES = PROBLEM_JS + r"""
// After Prepare Series (v13): the dates checked -> the confirm screen ("Book N dates", the series stored under its key);
// a question or a problem -> the step-2 form again, as for a single booking.
const r = $input.first().json || {};
const R = $('Read Step 2').first().json;
if (r.status !== 'PREPARED') {
  const pr = problemFor(r);
  return [{ json: { view_id: R.viewId, view: formAgain(pr.warn, pr.extra, pr.asked) } }];
}
const dates = [].concat(r.dates || []);
const card = String(r.card_text || '').replace(/\n*Confirm to book\.\s*(?:\(yes\/no\))?\s*$/i, '').trim();
const meta = { key: r.prep_stored === false ? '' : (r.prep_key || ''), n: dates.length, title: r.title || '', requester: R.s.requester, channel: R.channel,
  time: R.s.t0 + '-' + R.s.t1 };
let payload = null; try { payload = JSON.parse(r.prep_payload || 'null'); } catch (e) { payload = null; }
if (!meta.key && payload && JSON.stringify(payload.inputs || {}).length < 2400) meta.inputs = payload.inputs;
const ok = !!(meta.key || meta.inputs) && dates.length > 0;
const view = { type: 'modal', callback_id: 'series_confirm', title: { type: 'plain_text', text: 'Book a room' }, close: { type: 'plain_text', text: 'Back' },
  private_metadata: JSON.stringify(meta),
  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: card.slice(0, 2900) } }].concat(ok ? [] :
    [{ type: 'context', elements: [{ type: 'mrkdwn', text: '⚠️ The series could not be saved for booking. Go *Back* and try again.' }] }]) };
if (ok) view.submit = { type: 'plain_text', text: 'Book ' + dates.length + (dates.length === 1 ? ' date' : ' dates') };
return [{ json: { view_id: R.viewId, view } }];"""

READ_SERIES_CONFIRM = r"""
// Read Series Confirm (v13): "Book N dates" pressed -> "Booking…" at once (a batch takes minutes; the result also goes to
// the DM), then the stored series is read back and booked.
const c = $('Check Signature').first().json;
const p = $('Read Request').first().json.payload || {};
const V = p.view || {};
let meta = {}; try { meta = JSON.parse(V.private_metadata || '{}'); } catch (e) { meta = {}; }
const n = Number(meta.n || 0);
const working = { type: 'modal', title: { type: 'plain_text', text: 'Book a room' }, close: { type: 'plain_text', text: 'Close' }, private_metadata: V.private_metadata || '',
  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: '⏳ *Booking ' + n + ' dates…*\n' + (meta.title || '') } },
           { type: 'context', elements: [{ type: 'mrkdwn', text: 'Processing your series of bookings. This may take a while, so you can close this window for now. You will be notified once finished.' }] }] };
return [{ json: { meta, user: c.user, viewId: V.id || '', key: meta.key || 'prep-none', answer: { response_action: 'update', view: working } } }];"""

TO_BOOK_SERIES = CACHE_JS + r"""
// To Book Series (v13): exactly the series the confirm screen showed - read back by its key and checked against its own
// code (as main's Prepared Series does at a yes) - booked by Book Series. Anything wrong: nothing is booked.
const PB_SALT = '4539361661025d1d';
const pbHash = s => { let h = 0x811c9dc5; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; } return ('0000000' + h.toString(16)).slice(-8); };
const R = $('Read Series Confirm').first().json;
let inputs = null, why = '';
if (R.meta.inputs) inputs = R.meta.inputs;
else {
  const rows = $('Read Saved Series').all().map(i => i.json || {}).filter(x => x.cache_key === R.key);
  let P = null; try { P = rows.length ? JSON.parse(rows[rows.length - 1].payload) : null; } catch (e) { P = null; }
  if (!P || P.kind !== 'series' || !P.inputs) why = 'the saved series was not found';
  else if (P.code !== pbHash(PB_SALT + '|series-code|' + JSON.stringify(P.inputs))) why = 'the saved series did not check out';
  else if (P.ref && R.user && P.ref !== R.user) why = 'the saved series is someone else’s';
  else inputs = P.inputs;
}
if (!inputs) return [{ json: { go: false, why } }];
// v15 (Slack test): every date came back NO_REFERENCE_DATA - Book Session needs the room list, as the prepare step had it
const data = readCache($('Read Cache 8').all().map(i => i.json || {})) || { rooms: [], sessionTypes: [], bookers: [] };
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
const staff = (data.bookers || []).map(b => b.fields || {}).filter(f => f.Name).map(f => ({ Name: f.Name, Initials: f.Initials || '', Info: f.Info || '',
  Department: f.Department || [], 'Default Type': f['Default Type'] || [] }));
const me = (data.bookers || []).map(b => b.fields || {}).find(f => String(f['Slack User ID'] || '').split(/[\s,]+/).indexOf(R.user) !== -1) || {};
return [{ json: Object.assign({}, inputs, { go: true, confirmed: true, mode: '', frequency: '', by_days: '', start_date: '', count: null, until_date: '',
  asked_text: '', staff_data: JSON.stringify(staff), changes: '', reference_data: JSON.stringify({ rooms: refRooms, types: refTypes, preemptionRanks: ranks }),
  authority: [].concat(me.Authority || []).map(a => (a && a.name) || a).join(', ') }) }];"""

AFTER_BOOK_SERIES = r"""
// After Book Series (v13): booked / not booked, on the form (if still open) and in the DM. Each date can be changed or
// cancelled from My bookings.
const R = $('Read Series Confirm').first().json;
const T = $('To Book Series').first().json;
const r = T.go ? ($input.first().json || {}) : { status: 'NOT_BOOKED', human: '' };
const DS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'], MS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const sh = d => { const x = new Date(d + 'T12:00:00Z'); return DS[x.getUTCDay()] + ', ' + MS[x.getUTCMonth()] + ' ' + x.getUTCDate(); };
const t12 = hm => { if (!hm) return ''; let [h, m] = String(hm).split(':').map(Number); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(m).padStart(2, '0') + ' ' + ap; };
const booked = [].concat(r.booked || []), skipped = [].concat(r.skipped || []), failed = [].concat(r.failed || []);
// v15: never a code - the reason in words
const WHY = { NO_REFERENCE_DATA: 'the room list couldn’t be read', UNVERIFIABLE: 'the calendar couldn’t be checked', LOOKUP_FAILED: 'the calendar couldn’t be read',
  CALENDAR_ERROR: 'the calendar couldn’t be read', ROOM_OCCUPIED: 'the room was taken', ROOM_DECLINED: 'the room turned it down', ROOM_UNSUITABLE: 'the room can’t do this session',
  CLIENT_UNVERIFIED: 'the client couldn’t be checked', ENGINEER_UNKNOWN: 'the engineer isn’t in Bookers', ENGINEER_UNVERIFIED: 'the engineer couldn’t be checked',
  DURATION_INVALID: 'the time doesn’t work', NOT_CONFIRMED: 'it wasn’t confirmed' };
const why = w => WHY[String(w || '').toUpperCase()] || 'it couldn’t be booked';
const failLine = () => { const g = {}; for (const f of failed) (g[why(f.why)] = g[why(f.why)] || []).push(sh(f.date));
  return Object.keys(g).map(k => g[k].join(', ') + ' - ' + k).join('; '); };
const n = Number(R.meta.n || 0) || booked.length + skipped.length + failed.length;
const title = R.meta.title || T.summary || '';
const tm = String(R.meta.time || '').split('-');
let text;
if (!T.go) text = '❌ *Nothing was booked* - ' + (T.why || 'the series could not be read back') + '. Try again from *Book a room*.';
else if (!booked.length) text = '❌ *Nothing was booked.*\n\n*' + title + '*' + (skipped.length ? '\nThe room was taken on ' + skipped.map(sh).join(', ') + '.' : '')
  + (failed.length ? '\nNot booked: ' + failLine() + '. Try again in a moment.' : '');
else text = '✅ *Booked ' + (booked.length === n ? n + ' dates' : booked.length + ' of ' + n + ' dates') + '.*\n\n*' + title + '*\n*Dates:*\n'
  + booked.map(d => '- ' + sh(d)).join('\n') + (tm[0] ? '\n*Time:* ' + t12(tm[0]) + ' – ' + t12(tm[1]) : '') + (T.rooms ? '\n*Room:* ' + T.rooms : '')
  + (skipped.length ? '\n\nNot booked - the room was taken: ' + skipped.map(sh).join(', ') : '')
  + (failed.length ? '\n\nNot booked: ' + failLine() + '.' : '');
const blocks = [{ type: 'section', text: { type: 'mrkdwn', text: text.slice(0, 2900) } }].concat(booked.length
  ? [{ type: 'context', elements: [{ type: 'mrkdwn', text: 'Change or cancel a date from *My bookings*.' }] }] : []);
const view = { type: 'modal', clear_on_close: true, title: { type: 'plain_text', text: 'Book a room' }, close: { type: 'plain_text', text: 'Done' }, blocks };
// v17: the DM also has Book a room / My bookings (not the form - a button there would need a pushed view)
const dmBlocks = blocks.concat([{ type: 'actions', elements: [
  { type: 'button', style: 'primary', action_id: 'open_book', value: 'menu', text: { type: 'plain_text', text: 'Book a room' } },
  { type: 'button', action_id: 'my_bookings', value: 'menu', text: { type: 'plain_text', text: 'My bookings' } } ] }]);
return [{ json: { view_id: R.viewId, view, channel: R.meta.channel || R.user, text: text.slice(0, 2900), blocks: dmBlocks } }];"""

MY_WINDOW = ROW_JS + r"""
// My Window (v11): My bookings from the menu (from today, Manila, a year ahead during QA) or a page button (its date).
const YEAR_SHIFT = 1;
const c = $('Check Signature').first().json;
const p = $('Read Request').first().json.payload || {};
const a = (p.actions || [])[0] || {};
const page = /^my_page/.test(String(a.action_id || '')) && /^\d{4}-\d{2}-\d{2}$/.test(String(a.value || ''));   // v16
let start = page ? String(a.value) : '';
if (!start) { const m = new Date(Date.now() + 8 * 3600 * 1000);
  start = (m.getUTCFullYear() + YEAR_SHIFT) + '-' + String(m.getUTCMonth() + 1).padStart(2, '0') + '-' + String(m.getUTCDate()).padStart(2, '0'); }
const end = addDays(start, 7);
return [{ json: { user: c.user, page, start, end, timeMin: start + 'T00:00:00+08:00', timeMax: end + 'T00:00:00+08:00',
  channel: (p.container && p.container.channel_id) || (p.channel && p.channel.id) || c.user, ts: (p.container && p.container.message_ts) || '' } }];"""

RENDER_MY = CACHE_JS + ROW_JS + r"""
// Render My Bookings (v11): the week's bookings this person made (ref:) or engineers / arranges (team:), each with Change /
// Cancel; Previous / Next 7 days update the same message.
const W = $('My Window').first().json;
const res = $input.first().json || {};
const data = readCache($('Read Cache 4').all().map(i => i.json || {})) || { bookers: [] };
const meF = (data.bookers || []).map(b => b.fields || {}).find(f => String(f['Slack User ID'] || '').split(/[\s,]+/).indexOf(W.user) !== -1) || {};
const myName = String(meF.Name || '').trim().toLowerCase();
const md = t => ({ type: 'mrkdwn', text: t });
const blocks = [{ type: 'section', text: md('*Your bookings* · ' + dayShort(W.start) + ' – ' + dayShort(addDays(W.end, -1))) }];
const items = Array.isArray(res.items) ? res.items : null;
if (!items) blocks.push({ type: 'section', text: md('⚠️ The calendar couldn’t be read. Try again.') });
else {
  const rows = [];
  for (const e of items) {
    if (!e || e.status === 'cancelled') continue;
    const desc = String(e.description || '');
    const ref = (desc.match(/ref:\s*([A-Za-z0-9]+)/) || [])[1] || '';
    const team = ((desc.match(/team:\s*([^|]+)/) || [])[1] || '').split(/[\s,]+/).filter(Boolean);
    const mine = ref === W.user, onTeam = team.indexOf(W.user) !== -1;
    if (!mine && !onTeam) continue;
    const eng = ((desc.match(/Engineer:\s*([^(|]+)/) || [])[1] || '').trim().toLowerCase();
    const arr = ((desc.match(/Arranger:\s*([^(|]+)/) || [])[1] || '').trim().toLowerCase();
    const note = mine ? '' : (myName && eng === myName) ? 'You’re engineering' : (myName && arr === myName) ? 'You’re arranging' : 'You’re on the team';
    rows.push({ b: evBooking(e), note });
  }
  rows.sort((x, y) => (x.b.d + (x.b.s || '00:00')).localeCompare(y.b.d + (y.b.s || '00:00')));
  if (!rows.length) blocks.push({ type: 'section', text: md('Nothing booked these 7 days.') });
  for (const x of rows.slice(0, 20)) blocks.push({ type: 'section', block_id: 'bk_' + x.b.id, text: md('*' + x.b.t + '*\n' + whenLine(x.b) + (x.note ? '\n_' + x.note + '_' : '')) }, bkButtons(x.b));
  if (rows.length > 20) blocks.push({ type: 'context', elements: [md('Showing the first 20 of ' + rows.length + '.')] });
  if (res.nextPageToken) blocks.push({ type: 'context', elements: [md('Some bookings may be missing - the calendar sent only part of the week.')] });
}
blocks.push({ type: 'actions', block_id: 'my_nav', elements: [
  { type: 'button', action_id: 'my_page_prev', value: addDays(W.start, -7), text: { type: 'plain_text', text: '← Previous 7 days' } },
  { type: 'button', action_id: 'my_page_next', value: addDays(W.start, 7), text: { type: 'plain_text', text: 'Next 7 days →' } } ] });
blocks.push({ type: 'context', elements: [md('Further ahead? Type it, like _what do I have in November?_')] });
return [{ json: { channel: W.channel, ts: W.ts, page: W.page, blocks, text: 'Your bookings' } }];"""

BOOKER_JS = r"""
// The person pressing the button, from Bookers (authority and department decide who may change someone else's booking)
function booker(data, id) { const f = (data.bookers || []).map(b => b.fields || {}).find(f => String(f['Slack User ID'] || '').split(/[\s,]+/).indexOf(id) !== -1) || {};
  const names = x => [].concat(x || []).map(a => (a && a.name) || a).join(', ');
  return { name: String(f.Name || ''), authority: names(f.Authority), department: names(f.Department) }; }
"""

TO_CANCEL = CACHE_JS + BOOKER_JS + r"""
// To Cancel (v11): the booking on the button, cancelled after Slack's "Cancel this booking?" pop-up was confirmed.
const c = $('Check Signature').first().json;
const p = $('Read Request').first().json.payload || {};
let b = {}; try { b = JSON.parse(((p.actions || [])[0] || {}).value || '{}'); } catch (e) { b = {}; }
const me = booker(readCache($('Read Cache 5').all().map(i => i.json || {})) || { bookers: [] }, c.user);
return [{ json: { event_id: b.id || '', booking_date: b.d || '', title: b.t || '', confirmed: true, requester: c.user,
  requester_name: me.name, authority: me.authority, department: me.department, mode: '', check_code: '', card_time: '', card_room: '',
  booking_time: b.s || '' } }];"""

LEAD_JS = r"""
// v17: a reply about one booking ("Here's the booking - press Cancel…", "Here's your proposed change…") loses that line once
// the booking is cancelled or changed - the card says it. A list ("Which one?", My bookings) keeps its heading.
function dropLead(blocks) {
  const rows = blocks.filter(x => /^bk_/.test(x.block_id || ''));
  const h = blocks[0];
  if (rows.length === 1 && h && h.type === 'section' && !h.block_id && /^(?:Here(?:’|')s |Here it is)/.test(String((h.text || {}).text || ''))) return blocks.slice(1);
  return blocks;
}
// v17: the row being cancelled / changed - details kept, buttons hidden, "⏳ … being processed…" under it
function processing(blocks, id, line) {
  const out = JSON.parse(JSON.stringify(blocks || [])).filter(x => x.block_id !== 'bka_' + id && x.block_id !== 'bkw_' + id);
  const i = out.findIndex(x => x.block_id === 'bk_' + id);
  if (i === -1) return null;
  out.splice(i + 1, 0, { type: 'context', block_id: 'bkw_' + id, elements: [{ type: 'mrkdwn', text: '⏳ ' + line }] });
  return out;
}
"""

MARK_CANCELLING = LEAD_JS + r"""
// Mark Cancelling (v17): right after Slack's "Cancel this booking?" was confirmed - the row says it is being processed.
const p = $('Read Request').first().json.payload || {};
let b = {}; try { b = JSON.parse(((p.actions || [])[0] || {}).value || '{}'); } catch (e) { b = {}; }
const blocks = processing((p.message || {}).blocks, b.id, 'Your cancellation is being processed…');
return [{ json: { ok: !!blocks, channel: (p.container && p.container.channel_id) || (p.channel && p.channel.id) || '', ts: (p.container && p.container.message_ts) || '',
  blocks: blocks || [], text: (p.message && p.message.text) || 'Cancelling' } }];"""

MARK_CHANGING = LEAD_JS + r"""
// Mark Changing (v17): the Change form was submitted - the row in the message it came from says it is being processed.
const R = $('Read Change').first().json;
const h = $input.first().json || {};
const ts = String((R.meta && R.meta.ts) || '');
const m = (h.messages || []).find(x => String(x.ts) === ts);
const blocks = m ? processing(m.blocks, R.b.id, 'Your change is being processed…') : null;
return [{ json: { ok: !!blocks, channel: (R.meta && R.meta.ch) || '', ts, blocks: blocks || [], text: (m && m.text) || 'Changing', original: m ? m.blocks : [] } }];"""

RESTORE_MESSAGE = r"""
// Restore Message (v17): the change did not go through - the row goes back as it was (with its buttons); the form says why.
const A = $('After Move').first().json;
const M = $('Mark Changing').first().json || {};
if (A.ok || !M.ok || !M.ts) return [];
return [{ json: { channel: M.channel, ts: M.ts, blocks: M.original, text: M.text } }];"""

AFTER_CANCEL = ROW_JS + LEAD_JS + r"""
// After Cancel (v11): the message the button was in updates in place - the booking's row says Cancelled (buttons gone), or
// why it could not be cancelled (row kept).
const r = $input.first().json || {};
const p = $('Read Request').first().json.payload || {};
let b = {}; try { b = JSON.parse(((p.actions || [])[0] || {}).value || '{}'); } catch (e) { b = {}; }
const msg = p.message || {};
const ok = r.status === 'CANCELLED';
let blocks = JSON.parse(JSON.stringify(msg.blocks || [])).filter(x => x.block_id !== 'bkw_' + b.id);
const why = { NOT_YOURS: 'You can’t cancel this booking - only the person who booked it, or its engineer or arranger, can.',
  NOT_ON_CALENDAR: 'This booking isn’t on the calendar any more.', LOOKUP_FAILED: 'The calendar couldn’t be read. Try again.',
  NO_REFERENCE: 'This booking has no booker on it, so it has to be cancelled by hand.' }[r.reason] || 'It couldn’t be cancelled just now. Try again in a moment.';   // v15: no code shown
if (ok) {
  blocks = blocks.filter(x => x.block_id !== 'bka_' + b.id);
  // v17: the card, like Booked; a reply about this one booking loses its "Here's…" line
  const row = { type: 'section', block_id: 'bk_' + b.id, text: { type: 'mrkdwn', text: bkCard(b, '❌ *Cancelled.*') } };
  const i = blocks.findIndex(x => x.block_id === 'bk_' + b.id);
  if (i !== -1) blocks[i] = row; else blocks.push(row);
  blocks = dropLead(blocks);
} else {
  const i = blocks.findIndex(x => x.block_id === 'bka_' + b.id);
  blocks.splice(i === -1 ? blocks.length : i + 1, 0, { type: 'context', block_id: 'bkw_' + b.id, elements: [{ type: 'mrkdwn', text: '⚠️ ' + why }] });
}
return [{ json: { ok, channel: (p.container && p.container.channel_id) || (p.channel && p.channel.id) || '', ts: (p.container && p.container.message_ts) || '',
  blocks, text: msg.text || (ok ? 'Cancelled' : 'Not cancelled') } }];"""

CHANGE_JS = ROW_JS + r"""
// The Change form (v11): the booking's current date, start, end and room to start from; rooms of the same kind (studios,
// M booths, conference rooms) with the current one first.
function changeView(b, cur, warn, meta, rooms) {
  const pt = x => ({ type: 'plain_text', text: x });
  const times = [];
  for (let i = 0; i < 48; i++) { const mins = (8 * 60 + i * 30) % 1440, h = Math.floor(mins / 60), mm = mins % 60;
    times.push({ text: pt(((h % 12) || 12) + ':' + String(mm).padStart(2, '0') + ' ' + (h < 12 ? 'AM' : 'PM')), value: String(h).padStart(2, '0') + ':' + String(mm).padStart(2, '0') }); }
  const key = v => (Number(v.split(':')[0]) * 60 + Number(v.split(':')[1]) - 480 + 1440) % 1440;
  const tOpt = v => { if (!/^\d{2}:\d{2}$/.test(String(v || ''))) return null; let o = times.find(x => x.value === v); if (o) return o;
    o = { text: pt(t12(v)), value: v }; const at = times.findIndex(x => key(x.value) > key(v)); times.splice(at === -1 ? times.length : at, 0, o); return o; };
  [b.s, b.e].forEach(tOpt);
  const so = tOpt(cur.s), eo = tOpt(cur.e);
  const kind = n => /^M[1-8]$/.test(n) ? 'booth' : (rooms.common.indexOf(n) !== -1 ? 'common' : 'studio');
  const same = rooms.all.filter(n => kind(n) === kind(b.r || '')).sort((x, y) => x.localeCompare(y, 'en', { numeric: true }));
  const rnames = (b.r ? [b.r] : []).concat(same.filter(n => n !== b.r)).slice(0, 100);
  const ropts = rnames.map(n => ({ text: pt(n), value: n }));
  const blocks = [{ type: 'section', text: { type: 'mrkdwn', text: '*' + b.t + '*\nNow: ' + whenLine(b) } }];
  if (warn) blocks.push({ type: 'section', block_id: 'problem', text: { type: 'mrkdwn', text: '⚠️ ' + warn } });
  blocks.push({ type: 'input', block_id: 'date', label: pt('Date'), element: Object.assign({ type: 'datepicker', action_id: 'date_pick' }, /^\d{4}-\d{2}-\d{2}$/.test(cur.d || '') ? { initial_date: cur.d } : {}) },
    { type: 'input', block_id: 'start', label: pt('Start'), element: Object.assign({ type: 'static_select', action_id: 'start_pick', placeholder: pt('Choose a time'), options: times }, so ? { initial_option: so } : {}) },
    { type: 'input', block_id: 'end', label: pt('End'), element: Object.assign({ type: 'static_select', action_id: 'end_pick', placeholder: pt('Choose a time'), options: times }, eo ? { initial_option: eo } : {}) });
  if (cur.r && ropts.length && !ropts.some(o => o.value === cur.r)) ropts.splice(1, 0, { text: pt(cur.r), value: cur.r });   // v12: a typed room of another kind
  if (ropts.length) { const ro = ropts.find(o => o.value === (cur.r || b.r)) || ropts[0];
    blocks.push({ type: 'input', block_id: 'room', label: pt('Room'), element: { type: 'static_select', action_id: 'room_pick', options: ropts, initial_option: ro } }); }
  return { type: 'modal', callback_id: 'change_booking', title: pt('Change booking'), submit: pt('Change'), close: pt('Cancel'),
    private_metadata: JSON.stringify(meta), blocks };
}
function roomLists(data) {
  const all = [], common = [];
  for (const r of (data && data.rooms) || []) { const f = r.fields || {}; const n = String(f['Room Name'] || '').trim(); if (!n) continue; all.push(n);
    const k = [].concat(f['Room Type'] || []).map(x => String(x).toLowerCase()); if (k.indexOf('conference room') !== -1 || k.indexOf('lobby') !== -1) common.push(n); }
  return { all, common };
}
"""

BUILD_CHANGE = CACHE_JS + CHANGE_JS + r"""
// Build Change (v11): Change was pressed on a booking - the form starts at its current values.
const c = $('Check Signature').first().json;
const p = $('Read Request').first().json.payload || {};
let b = {}; try { b = JSON.parse(((p.actions || [])[0] || {}).value || '{}'); } catch (e) { b = {}; }
// v12: the new values typed in the chat (main v265) - the form starts there; a start alone keeps the booking's length
const nIn = (b.n && typeof b.n === 'object') ? b.n : null; delete b.n;
const mins = hm => { const m = String(hm || '').match(/^(\d{2}):(\d{2})$/); return m ? +m[1] * 60 + +m[2] : null; };
const cur = { d: b.d, s: b.s, e: b.e, r: b.r };
if (nIn) {
  if (/^\d{4}-\d{2}-\d{2}$/.test(String(nIn.d || ''))) cur.d = nIn.d;
  if (nIn.r) cur.r = nIn.r;
  if (mins(nIn.s) !== null && mins(nIn.e) !== null) { cur.s = nIn.s; cur.e = nIn.e; }
  else if (mins(nIn.s) !== null && mins(b.s) !== null && mins(b.e) !== null) { const e = mins(nIn.s) + mins(b.e) - mins(b.s); cur.s = nIn.s;
    cur.e = e < 1440 ? String(Math.floor(e / 60)).padStart(2, '0') + ':' + String(e % 60).padStart(2, '0') : ''; }
  else if (mins(nIn.e) !== null) cur.e = nIn.e;
}
const data = readCache($('Read Cache 6').all().map(i => i.json || {}));
const meta = { b, ch: (p.container && p.container.channel_id) || (p.channel && p.channel.id) || '', ts: (p.container && p.container.message_ts) || '', requester: c.user };
return [{ json: { trigger_id: c.triggerId, view: changeView(b, cur, '', meta, roomLists(data)) } }];"""

READ_CHANGE = ROW_JS + r"""
// Read Change (v11): the new date / times / room, checked at once. Nothing changed -> said on the form, nothing is moved.
const c = $('Check Signature').first().json;
const p = $('Read Request').first().json.payload || {};
const V = p.view || {};
const v = (V.state && V.state.values) || {};
let meta = {}; try { meta = JSON.parse(V.private_metadata || '{}'); } catch (e) { meta = {}; }
const b = meta.b || {};
const sel = (bl, a) => (v[bl] && v[bl][a] && v[bl][a].selected_option && v[bl][a].selected_option.value) || '';
const n = { d: (v.date && v.date.date_pick && v.date.date_pick.selected_date) || '', s: sel('start', 'start_pick'), e: sel('end', 'end_pick'), r: sel('room', 'room_pick') || b.r || '' };
const errors = {};
if (!n.d) errors.date = 'Pick a date.';
if (!n.s) errors.start = 'Pick a start time.';
if (!n.e) errors.end = 'Pick an end time.';
if (n.s && n.e && n.e <= n.s) errors.end = 'The end has to be after the start.';
if (!Object.keys(errors).length && n.d === b.d && n.s === b.s && n.e === b.e && n.r === (b.r || '')) errors.date = 'Nothing changed - pick a new date, time or room.';
const valid = Object.keys(errors).length === 0;
const working = { type: 'modal', title: { type: 'plain_text', text: 'Change booking' }, close: { type: 'plain_text', text: 'Close' },
  private_metadata: V.private_metadata || '',
  blocks: [{ type: 'section', text: { type: 'mrkdwn', text: '⏳ *Changing ' + b.t + '…*\n' + whenLine(n) } },
           { type: 'context', elements: [{ type: 'mrkdwn', text: 'This takes a few seconds.' }] }] };
return [{ json: { valid, b, n, meta, viewId: V.id || '', user: c.user,
  answer: valid ? { response_action: 'update', view: working } : { response_action: 'errors', errors } } }];"""

TO_MOVE = CACHE_JS + BOOKER_JS + r"""
// To Move (v11): Move Booking's inputs - the booking by its id on its own date, the new window, and a new room only when
// it changed. Confirmed: pressing Change is the confirmation.
const R = $('Read Change').first().json;
const me = booker(readCache($('Read Cache 7').all().map(i => i.json || {})) || { bookers: [] }, R.user);
return [{ json: { title: R.b.t || '', event_id: R.b.id || '', booking_date: R.b.d || '',
  new_start_iso: R.n.d + 'T' + R.n.s + ':00+08:00', new_end_iso: R.n.d + 'T' + R.n.e + ':00+08:00',
  new_rooms: R.n.r && R.n.r !== R.b.r ? R.n.r : '', requester: R.user, confirmed: true,
  authority: me.authority, department: me.department, requester_name: me.name, reference_data: '', booking_time: R.b.s || '' } }];"""

AFTER_MOVE = CACHE_JS + CHANGE_JS + r"""
// After Move (v11): Moved -> the form says Changed (the card) and the message's row is updated next; anything else -> the
// form again at the new values, with the problem on top (a taken room: its free times that day).
const r = $input.first().json || {};
const R = $('Read Change').first().json;
const b = R.b, n = R.n;
if (r.status === 'MOVED' || r.status === 'PARTIAL') {
  const nb = { id: String(r.event_id || b.id), d: n.d, s: n.s, e: n.e, r: n.r || b.r, t: b.t };
  const card = bkCard(nb, '✅ *Changed.*') + (r.status === 'PARTIAL' ? '\n⚠️ The old booking could not be removed - delete it from the calendar.' : '');
  const view = { type: 'modal', clear_on_close: true, title: { type: 'plain_text', text: 'Change booking' }, close: { type: 'plain_text', text: 'Done' },
    blocks: [{ type: 'section', text: { type: 'mrkdwn', text: card } }] };
  return [{ json: { ok: true, view_id: R.viewId, view, ch: (R.meta && R.meta.ch) || '', ts: (R.meta && R.meta.ts) || '', oldId: b.id, nb, card } }];
}
const hm = x => (String(x || '').match(/T(\d{2}:\d{2})/) || [])[1] || '';
const slots = [].concat(r.same_day_slots || []).map(x => t12(hm(x.start)) + ' – ' + t12(hm(x.end))).filter(x => x.length > 5);
const why = r.reason === 'ROOM_OCCUPIED' ? (n.r || b.r || 'The room') + ' is taken then' + (slots.length ? '. Free that day: ' + slots.join(', ') : '') + '.'
  : ({ NOT_YOURS: 'You can’t change this booking - only the person who booked it, or its engineer or arranger, can.',
       NOT_ON_CALENDAR: 'This booking isn’t on the calendar any more.', LOOKUP_FAILED: 'The calendar couldn’t be read. Try again.',
       UNKNOWN_ROOM: 'That room couldn’t be found. Pick another.', DURATION_INVALID: 'Check the start and end.', MISSING_TIMES: 'Check the start and end.',
       NO_REFERENCE: 'This booking has no booker on it, so it has to be changed by hand.' }[r.reason]
     || 'It couldn’t be changed just now. Try again in a moment.');   // v15: no code shown
const data = readCache($('Read Cache 7').all().map(i => i.json || {}));
return [{ json: { ok: false, view_id: R.viewId, view: changeView(b, n, why, R.meta || {}, roomLists(data)) } }];"""

FIX_MESSAGE = ROW_JS + LEAD_JS + r"""
// Fix Message (v11): after a change, the message the Change button was in shows the new time (and the new booking id on
// its buttons - Move Booking makes a new event).
const A = $('After Move').first().json;
const h = $input.first().json || {};
const m = (h.messages || []).find(x => String(x.ts) === String(A.ts));
if (!m) return [];
const nb = A.nb, old = A.oldId;
const blocks = JSON.parse(JSON.stringify(m.blocks || [])).filter(x => x.block_id !== 'bkw_' + old);
const i = blocks.findIndex(x => x.block_id === 'bk_' + old);
if (i === -1) return [];
// v17: the Changed card everywhere (it said only "Changed" in lists and replies); a one-booking reply loses its top line
blocks[i] = { type: 'section', block_id: 'bk_' + nb.id, text: { type: 'mrkdwn', text: A.card } };
const j = blocks.findIndex(x => x.block_id === 'bka_' + old);
if (j !== -1) blocks[j] = bkButtons(nb); else blocks.splice(i + 1, 0, bkButtons(nb));
return [{ json: { channel: A.ch, ts: A.ts, blocks: dropLead(blocks), text: m.text || 'Changed' } }];"""

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
rt = add({"parameters": {"mode": "expression", "numberOutputs": 14, "output": "={{ $json.route }}"},
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
dmr = slack("DM Booked", "chat.postMessage", "={{ JSON.stringify({ channel: $('After Book').first().json.channel, text: $('After Book').first().json.text, blocks: $('After Book').first().json.blocks }) }}", [X + 3120, 180])
sp = slack("Show Question", "views.update", "={{ JSON.stringify({ view_id: $json.view_id, view: $json.view }) }}", [X + 1920, 320])
sq = iff("Series?", "={{ ((($('Read Step 2').first().json.s || {}).series || {}).dates || []).length > 1 }}", [X + 1080, 120])
tps = code("To Prepare Series", TO_PREPARE_SERIES, [X + 1200, 60])
ps = run_wf("Prepare Series", SERIES_WF, "Jessie — Book Series", [X + 1440, 60])
aps = code("After Prepare Series", AFTER_PREPARE_SERIES, [X + 1680, 60])
sss = slack("Show Series Step", "views.update", "={{ JSON.stringify({ view_id: $json.view_id, view: $json.view }) }}", [X + 1920, 60])
link(rt, a, 6); chain(a, b, c_, v_); link(v_, tp, 0); chain(tp, sq); link(sq, tps, 0); link(sq, pr, 1); chain(tps, ps, aps, sss)
chain(pr, ap, gp); link(gp, tb, 0); link(gp, sp, 1)
chain(tb, bk, ab, sv, ok_); link(ok_, dmr, 0)
# 13 series confirmed -> "Booking N dates…" at once, the stored series read back, Book Series, the result (form + DM) (v13)
a = code("Read Series Confirm", READ_SERIES_CONFIRM, [X, 1240]); b = respond("Answer Series", [X + 240, 1240], body="={{ JSON.stringify($json.answer) }}")
rs = add({"parameters": {"operation": "get",
                          "dataTableId": {"__rl": True, "value": CACHE_TABLE, "mode": "list", "cachedResultName": "Jessie Reference Cache"},
                          "matchType": "allConditions", "filters": {"conditions": [{"keyName": "cache_key", "keyValue": "={{ $('Read Series Confirm').first().json.key }}"}]},
                          "returnAll": True},
          "type": "n8n-nodes-base.dataTable", "typeVersion": 1, "position": [X + 480, 1240], "id": nid(), "name": "Read Saved Series",
          "executeOnce": True, "alwaysOutputData": True, "onError": "continueRegularOutput"})
tbs = code("To Book Series", TO_BOOK_SERIES, [X + 720, 1240])
gs = iff("Series Go?", "={{ $json.go === true }}", [X + 960, 1240])
bs = run_wf("Book Series", SERIES_WF, "Jessie — Book Series", [X + 1200, 1220])
abs_ = code("After Book Series", AFTER_BOOK_SERIES, [X + 1440, 1240])
ssr = slack("Show Series Result", "views.update", "={{ JSON.stringify({ view_id: $json.view_id, view: $json.view }) }}", [X + 1680, 1240])
dms = slack("DM Series", "chat.postMessage", "={{ JSON.stringify({ channel: $('After Book Series').first().json.channel, text: $('After Book Series').first().json.text, blocks: $('After Book Series').first().json.blocks }) }}", [X + 1920, 1240])
rc8 = read_cache("Read Cache 8", [X + 600, 1360])
link(rt, a, 13); chain(a, b, rs, rc8, tbs, gs); link(gs, bs, 0); link(gs, abs_, 1); chain(bs, abs_, ssr, dms)
# 7 My bookings (menu) and 12 a page button -> the week's bookings, posted or the same message updated (v11)
a = respond("Ack My Bookings", [X, 440]); b = read_cache("Read Cache 4", [X + 240, 440]); c_ = code("My Window", MY_WINDOW, [X + 480, 440])
lm = add({"parameters": {"url": "=https://www.googleapis.com/calendar/v3/calendars/{{ encodeURIComponent('" + CAL + "') }}/events?timeMin={{ encodeURIComponent($json.timeMin) }}&timeMax={{ encodeURIComponent($json.timeMax) }}&singleEvents=true&orderBy=startTime&maxResults=2500",
                          "authentication": "predefinedCredentialType", "nodeCredentialType": "googleCalendarOAuth2Api", "options": {}},
          "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [X + 720, 440], "id": nid(), "name": "List My Events",
          "credentials": GCAL_CRED, "onError": "continueRegularOutput"})
rm = code("Render My Bookings", RENDER_MY, [X + 960, 440])
pg = iff("Page?", "={{ $json.page === true }}", [X + 1200, 440])
ul = slack("Update List", "chat.update", "={{ JSON.stringify({ channel: $json.channel, ts: $json.ts, text: $json.text, blocks: $json.blocks }) }}", [X + 1440, 400])
pl = slack("Post List", "chat.postMessage", "={{ JSON.stringify({ channel: $json.channel, text: $json.text, blocks: $json.blocks }) }}", [X + 1440, 500])
REPORT_LIST = r"""// Report List (v16): Slack refused the My bookings message (posted or updated) - tell the person why, so it never fails silently.
const r = $input.first().json || {};
if (r.ok === true) return [];
const c = $('Check Signature').first().json;
return [{ json: { channel: c.user || '', text: '⚠️ My bookings could not be shown: ' + String(r.error || (r.response_metadata && JSON.stringify(r.response_metadata.messages)) || JSON.stringify(r)).slice(0, 300) } }];"""
rl = code("Report List", REPORT_LIST, [X + 1680, 450]); dl = slack("DM List Failed", "chat.postMessage", DM, [X + 1920, 450])
link(rt, a, 7); link(rt, a, 12); chain(a, b, c_, lm, rm, pg); link(pg, ul, 0); link(pg, pl, 1); link(ul, rl); link(pl, rl); chain(rl, dl)
# 9 Cancel (after Slack's pop-up) -> Cancel Booking -> the message updates in place (v11)
a = respond("Ack Cancel", [X, 760]); b = read_cache("Read Cache 5", [X + 240, 760]); c_ = code("To Cancel", TO_CANCEL, [X + 480, 760])
d = run_wf("Cancel", CANCEL_WF, "Jessie — Cancel Booking", [X + 720, 760]); e = code("After Cancel", AFTER_CANCEL, [X + 960, 760])
f = slack("Update Cancelled", "chat.update", "={{ JSON.stringify({ channel: $json.channel, ts: $json.ts, text: $json.text, blocks: $json.blocks }) }}", [X + 1200, 760])
mc = code("Mark Cancelling", MARK_CANCELLING, [X + 120, 860])
uc = slack("Show Cancelling", "chat.update", "={{ JSON.stringify({ channel: $json.channel, ts: $json.ts, text: $json.text, blocks: $json.blocks }) }}", [X + 240, 860])
mcq = iff("Cancelling Shown?", "={{ $('Mark Cancelling').first().json.ok === true }}", [X + 120, 760])
link(rt, a, 9); chain(a, mc, mcq); link(mcq, uc, 0); link(mcq, b, 1); chain(uc, b); chain(b, c_, d, e, f)
# 10 Change pressed -> the Change form (v11)
a = respond("Ack Change", [X, 920]); b = read_cache("Read Cache 6", [X + 240, 920]); c_ = code("Build Change", BUILD_CHANGE, [X + 480, 920])
d = slack("Open Change", "views.open", "={{ JSON.stringify({ trigger_id: $json.trigger_id, view: $json.view }) }}", [X + 720, 920])
e = code("Report Open Change", REPORT_OPEN, [X + 960, 920]); f = slack("DM Change Failed", "chat.postMessage", DM, [X + 1200, 920])
link(rt, a, 10); chain(a, b, c_, d, e, f)
# 11 Change submitted -> "Changing…" at once, then Move Booking; the form says Changed (or the problem) and the message updates
a = code("Read Change", READ_CHANGE, [X, 1080]); b = respond("Answer Change", [X + 240, 1080], body="={{ JSON.stringify($json.answer) }}")
v_ = iff("Change OK?", "={{ $('Read Change').first().json.valid }}", [X + 480, 1080])
c_ = read_cache("Read Cache 7", [X + 720, 1060]); d = code("To Move", TO_MOVE, [X + 960, 1060])
e = run_wf("Move", MOVE_WF, "Jessie — Move Booking", [X + 1200, 1060]); f = code("After Move", AFTER_MOVE, [X + 1440, 1060])
g = slack("Show Change Result", "views.update", "={{ JSON.stringify({ view_id: $json.view_id, view: $json.view }) }}", [X + 1680, 1060])
mv = iff("Moved?", "={{ $('After Move').first().json.ok === true && !!$('After Move').first().json.ts }}", [X + 1920, 1060])
gm = add({"parameters": {"url": "=https://slack.com/api/conversations.history?channel={{ encodeURIComponent($('After Move').first().json.ch) }}&latest={{ encodeURIComponent($('After Move').first().json.ts) }}&inclusive=true&limit=1",
                          "authentication": "predefinedCredentialType", "nodeCredentialType": "slackApi", "options": {}},
          "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [X + 2160, 1040], "id": nid(), "name": "Get Message",
          "credentials": SLACK_CRED, "onError": "continueRegularOutput"})
fx = code("Fix Message", FIX_MESSAGE, [X + 2400, 1040])
um = slack("Update Changed", "chat.update", "={{ JSON.stringify({ channel: $json.channel, ts: $json.ts, text: $json.text, blocks: $json.blocks }) }}", [X + 2640, 1040])
gb = add({"parameters": {"url": "=https://slack.com/api/conversations.history?channel={{ encodeURIComponent((($('Read Change').first().json.meta) || {}).ch || '') }}&latest={{ encodeURIComponent((($('Read Change').first().json.meta) || {}).ts || '') }}&inclusive=true&limit=1",
                          "authentication": "predefinedCredentialType", "nodeCredentialType": "slackApi", "options": {}},
          "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [X + 600, 1160], "id": nid(), "name": "Get Message Before",
          "credentials": SLACK_CRED, "onError": "continueRegularOutput"})
mk = code("Mark Changing", MARK_CHANGING, [X + 720, 1160])
mkq = iff("Changing Shown?", "={{ $('Mark Changing').first().json.ok === true }}", [X + 840, 1160])
uk = slack("Show Changing", "chat.update", "={{ JSON.stringify({ channel: $json.channel, ts: $json.ts, text: $json.text, blocks: $json.blocks }) }}", [X + 960, 1200])
rsm = code("Restore Message", RESTORE_MESSAGE, [X + 2160, 1160])
ur = slack("Update Restored", "chat.update", "={{ JSON.stringify({ channel: $json.channel, ts: $json.ts, text: $json.text, blocks: $json.blocks }) }}", [X + 2400, 1160])
link(rt, a, 11); chain(a, b, v_); link(v_, gb, 0); chain(gb, mk, mkq); link(mkq, uk, 0); link(mkq, c_, 1); chain(uk, c_)
chain(c_, d, e, f, g, mv); link(mv, gm, 0); link(mv, rsm, 1); chain(gm, fx, um); chain(rsm, ur)
# 8 Add a note (v10) -> answered at once, then the form again with or without the Notes field
a = respond("Ack Note", [X, 600]); b = code("Note Toggle", NOTE_TOGGLE, [X + 240, 600])
c_ = slack("Show Note", "views.update", "={{ JSON.stringify({ view_id: $json.view_id, hash: $json.hash, view: $json.view }) }}", [X + 480, 600])
link(rt, a, 8); chain(a, b, c_)

nodes.append({"parameters": {"content": "## Jessie — Slack Interactions\nEvery Slack button click and form submission. The signature comes from "
                             "**Jessie — Slack Signature** (nothing to paste).\n\n**v11 = slice 1 step C1:** the menu's Book a room opens the two-step "
                             "booking form; Book books through Book Session. My bookings lists the week with Change / Cancel; Change opens a form (Move Booking), Cancel asks first (Cancel Booking).\n\nRequest URL: "
                             "`https://signal.hitpromanila.net/webhook/jessie-interactions`", "height": 320, "width": 460},
              "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [-40, -820], "id": nid(), "name": "About"})

wf = {"name": "Jessie — Slack Interactions — v17 (build A: wording, cards, buttons)", "nodes": nodes, "connections": conn,
      "settings": {"executionOrder": "v1"}, "pinData": {}, "active": False}
with open(OUT, "w") as fh:
    json.dump(wf, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(nodes), "nodes")
