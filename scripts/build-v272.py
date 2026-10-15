#!/usr/bin/env python3
"""main v272 (round 3: questions answered cleanly): from the Slack test of v271 (15 Oct 16:44-16:47).
  1. Room Availability's window took the times from earlier messages ("what's free friday afternoon?" checked 2-4 PM, from
     an earlier "2-4pm") - the tool now overrides the AI's times only with times typed in THIS message. List Events'
     description no longer mentions cancelling or moving.
  2. Book a room under an answer opens the form filled in from THIS message - its date, times and room ("is studio 8 free
     tomorrow 3-5?" -> step 1 at Sat Oct 16, 3-5 PM, Studio 8 carried).
  3. "What do I have this week / tomorrow / on the 20th / in November", "my bookings", "my schedule" are answered in code
     with the same list as My bookings - title, date, time, room, each with Change / Cancel, Previous / Next 7 days for a
     week (PENDING 100). Live 16:47 the AI wrote "Filtering for Howard (HL, …)" and "(Engineer: you, Arranger: …)" per row.
  4. The prompt gets back the question rules that kept answers tidy, checked for spill: the tone section, "never invent a
     reason", a list shows only title, date, time and room (never who booked, engineer, arranger, client or notes unless
     asked; never how it searched), and each question stands alone (no date, time or room from an earlier message unless
     they point back to it).
Built on workflows/imported/project-jessie-v271-imported.json (the live download).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v271-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v272.json")
SLACK_CRED = {"slackApi": {"id": "EcX8szEJrOLYLUfl", "name": "Jessie Slack (signed)"}}
GCAL_CRED = {"googleCalendarOAuth2Api": {"id": "6D1r3kaq6KaFdL0a", "name": "Google Calendar account"}}
CAL = "c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com"
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:70], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


# ---- 1: the window's times only from this message
ra = by["Room Availability"]["parameters"]["workflowInputs"]["value"]
OLD = "if (!t || !b.timeStart || !b.timeEnd || !m) return v;"
for k in ("start_iso", "end_iso"):
    assert ra[k].count(OLD) == 1, k
    ra[k] = ra[k].replace(OLD, "if (!t || !b.timeStart || !b.timeEnd || !b.timeInNewest || !m) return v;")   # v272: times typed in this message only
le = by["List Events"]["parameters"]
le["toolDescription"] = "List the events on the KDC Bookings calendar in a window, to show a requester what is already booked. Not for availability - use Room Availability to find out what is free."

# ---- 2: Book a room under an answer, filled in from this message
patch("Build Reply", [
    ("const blocks = chunks.map(c => ({ type: 'section', text: { type: 'mrkdwn', text: c } })).concat([{ type: 'actions', elements: [\n  { type: 'button', style: 'primary', action_id: 'open_book', value: 'menu',",
     """// v272: Book a room opens the form at what THIS message named - its date, times and room (nothing from earlier messages)
let bookValue = 'menu';
try {
  const g = $('Gate Context').first().json || {}, bf = $('Booked For').first().json || {};
  const tx = String((($('Slack Trigger').first().json || {}).text) || '');
  const P = {};
  const ds = String(g.datesInMessage || '').split(',').map(x => x.trim()).filter(x => /^\\d{4}-\\d{2}-\\d{2}$/.test(x));
  if (ds.length === 1) P.d = ds[0];
  if (bf.timeInNewest && /^\\d{2}:\\d{2}$/.test(String(bf.timeStart || '')) && /^\\d{2}:\\d{2}$/.test(String(bf.timeEnd || '')) && bf.timeStart < bf.timeEnd) { P.s = bf.timeStart; P.e = bf.timeEnd; }
  const rm = []; let m; const r1 = /\\bstudio\\s*([1-8a-fm])\\b/gi; while ((m = r1.exec(tx))) rm.push('Studio ' + m[1].toUpperCase());
  const r2 = /\\bm[\\s-]?booth\\s*([1-8])\\b|\\bm-?([1-8])\\b/gi; while ((m = r2.exec(tx))) rm.push('M' + (m[1] || m[2]));
  for (const n of ['Likha', 'Salin', 'Katha', 'Lobby']) if (new RegExp('\\\\b' + n + '\\\\b', 'i').test(tx)) rm.push(n);
  if (rm.length === 1) P.r = rm[0];
  if (Object.keys(P).length) bookValue = JSON.stringify(P);
} catch (e) { bookValue = 'menu'; }
const blocks = chunks.map(c => ({ type: 'section', text: { type: 'mrkdwn', text: c } })).concat([{ type: 'actions', elements: [
  { type: 'button', style: 'primary', action_id: 'open_book', value: bookValue,"""),
])

# ---- 3: "what do I have …" answered in code, like My bookings
ROW_JS = by["Change Reply"]["parameters"]["jsCode"].split("\n// Change Reply (main v265)")[0]
assert "function bkButtons" in ROW_JS and "function evBooking" in ROW_JS
MINE_CHECK = r"""// Mine Check (main v272, PENDING 100): "what do I have this week / tomorrow / on the 20th / in November", "my bookings", "my
// schedule" - answered in code with the My bookings list (Mine Reply), never written by the AI (live 16:47 it added
// "Filtering for …" and the engineer / arranger to every row). Works out the window; never throws.
const item = Object.assign({}, $input.first().json);
const mc = { go: false, why: '', timeMin: '', timeMax: '', start: '', end: '', week: false, channel: '', user: '' };
try {
  const g = $('Gate Context').first().json || {}, gate = g.gate || {};
  const trig = $('Slack Trigger').first().json || {};
  mc.channel = String(trig.channel || ''); mc.user = String(trig.user || '');
  const t = String(trig.text || '').replace(/\*sent using\*[\s\S]*$/i, '').toLowerCase().replace(/[’']/g, '');
  const mine = /\bwhat (?:do|have) i (?:got|have)\b|\bwhat do i have\b|\bwhats? (?:on )?my (?:schedule|calendar|bookings?|sessions?)\b|\bmy (?:bookings?|sessions?|schedule|calendar)\b|\bam i (?:booked|on|engineering|arranging)\b|\bdo i have (?:any )?(?:bookings?|sessions?)\b|\bwhere am i\b/.test(t);
  if (!mine) mc.why = 'not a my-bookings question';
  else if (/\b(?:cancel|delete|remove|move|resched\w*|change|push|extend|shorten|book)\b/.test(t)) mc.why = 'a change / cancel / booking';
  else if (g.confirmed || g.confirmedCancel || g.confirmedMove || gate.presentedBook || gate.presentedCancel || gate.presentedMove) mc.why = 'answering a chat card';
  else {
    const today = /^\d{4}-\d{2}-\d{2}$/.test(String(g.todayIso || '')) ? g.todayIso : new Date(Date.now() + 8 * 3600000).toISOString().slice(0, 10);
    const add = (d, n) => new Date(Date.parse(d + 'T12:00:00Z') + n * 86400000).toISOString().slice(0, 10);
    const ds = String(g.datesInMessage || '').split(',').map(x => x.trim()).filter(x => /^\d{4}-\d{2}-\d{2}$/.test(x)).sort();
    const MON = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'];
    const mm = t.match(/\b(?:in|for|during|this|next)?\s*(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\b(?!\s*\d)/);
    let start = today, end = add(today, 7), week = true;
    if (/\bnext week\b/.test(t)) { start = add(today, 7); end = add(today, 14); }
    else if (/\bthis month\b/.test(t) || mm) {
      const y0 = +today.slice(0, 4), mo0 = +today.slice(5, 7) - 1;
      const mo = mm ? MON.findIndex(x => x.startsWith(mm[1].slice(0, 3))) : mo0;
      const y = mo < mo0 ? y0 + 1 : y0;
      start = y + '-' + String(mo + 1).padStart(2, '0') + '-01'; end = new Date(Date.UTC(y, mo + 1, 1)).toISOString().slice(0, 10);
      if (start < today && mo === mo0) start = today;
      week = false;
    }
    else if (ds.length === 1 && !/\b(?:this|next) week\b|\bweek\b/.test(t)) { start = ds[0]; end = add(ds[0], 1); week = false; }
    else if (ds.length > 1) { start = ds[0]; end = add(ds[ds.length - 1], 1); week = false; }
    Object.assign(mc, { go: !!mc.channel && !!mc.user, why: 'my bookings', start, end, week, timeMin: start + 'T00:00:00+08:00', timeMax: end + 'T00:00:00+08:00' });
  }
} catch (e) { mc.go = false; mc.why = 'error: ' + ((e && e.message) || e); }
item.mineCheck = mc;
return [{ json: item }];"""

MINE_REPLY = ROW_JS + r"""
// Mine Reply (main v272): the person's bookings in the window - made, or engineered / arranged - as My bookings shows them:
// title, date, time, room, each with Change / Cancel; Previous / Next 7 days for a week.
const mc = ($('Mine Check').first().json || {}).mineCheck || {};
const res = $input.first().json || {};
const md = t => ({ type: 'mrkdwn', text: t });
const addD = (d, n) => new Date(Date.parse(d + 'T12:00:00Z') + n * 86400000).toISOString().slice(0, 10);
const head = mc.end === addD(mc.start, 1) ? dayShort(mc.start) : dayShort(mc.start) + ' – ' + dayShort(addD(mc.end, -1));
const blocks = [{ type: 'section', text: md('*Your bookings* · ' + head) }];
const items = Array.isArray(res.items) ? res.items : null;
let count = 0;
if (!items) blocks.push({ type: 'section', text: md('⚠️ The calendar couldn’t be read. Try again in a moment.') });
else {
  const rows = [];
  for (const e of items) {
    if (!e || e.status === 'cancelled') continue;
    const desc = String(e.description || '');
    const ref = (desc.match(/ref:\s*([A-Za-z0-9]+)/) || [])[1] || '';
    const team = ((desc.match(/team:\s*([^|]+)/) || [])[1] || '').split(/[\s,]+/).filter(Boolean);
    if (ref !== mc.user && team.indexOf(mc.user) === -1) continue;
    rows.push(evBooking(e));
  }
  rows.sort((a, b) => (a.d + (a.s || '00:00')).localeCompare(b.d + (b.s || '00:00')));
  count = rows.length;
  if (!rows.length) blocks.push({ type: 'section', text: md('Nothing booked for you then.') });
  for (const b of rows.slice(0, 20)) blocks.push({ type: 'section', block_id: 'bk_' + b.id, text: md('*' + b.t + '*\n' + whenLine(b)) }, bkButtons(b));
  if (rows.length > 20) blocks.push({ type: 'context', elements: [md('Showing the first 20 of ' + rows.length + '.')] });
}
if (mc.week) blocks.push({ type: 'actions', block_id: 'my_nav', elements: [
  { type: 'button', action_id: 'my_page_prev', value: addD(mc.start, -7), text: { type: 'plain_text', text: '← Previous 7 days' } },
  { type: 'button', action_id: 'my_page_next', value: addD(mc.start, 7), text: { type: 'plain_text', text: 'Next 7 days →' } } ] });
blocks.push({ type: 'actions', block_id: 'menu_nav', elements: [
  { type: 'button', style: 'primary', action_id: 'open_book', value: 'menu', text: { type: 'plain_text', text: 'Book a room' } } ] });
return [{ json: { channel: mc.channel, text: 'Your bookings · ' + head, blocks, count } }];"""

lx, ly = by["Late Menu?"]["position"]
wf["nodes"].extend([
    {"parameters": {"jsCode": MINE_CHECK}, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [lx + 200, ly + 260], "id": str(uuid.uuid4()), "name": "Mine Check"},
    {"parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
                                   "conditions": [{"id": str(uuid.uuid4()), "leftValue": "={{ ($json.mineCheck || {}).go === true }}", "rightValue": True,
                                                   "operator": {"type": "boolean", "operation": "true", "singleValue": True}}], "combinator": "and"}, "options": {}},
     "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [lx + 400, ly + 260], "id": str(uuid.uuid4()), "name": "Mine?"},
    {"parameters": {"url": "=https://www.googleapis.com/calendar/v3/calendars/{{ encodeURIComponent('" + CAL + "') }}/events?timeMin={{ encodeURIComponent($json.mineCheck.timeMin) }}&timeMax={{ encodeURIComponent($json.mineCheck.timeMax) }}&singleEvents=true&orderBy=startTime&maxResults=2500",
                    "authentication": "predefinedCredentialType", "nodeCredentialType": "googleCalendarOAuth2Api", "options": {}},
     "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [lx + 600, ly + 400], "id": str(uuid.uuid4()), "name": "List My Window",
     "credentials": GCAL_CRED, "onError": "continueRegularOutput"},
    {"parameters": {"jsCode": MINE_REPLY}, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [lx + 800, ly + 400], "id": str(uuid.uuid4()), "name": "Mine Reply"},
    {"parameters": {"method": "POST", "url": "https://slack.com/api/chat.postMessage", "authentication": "predefinedCredentialType",
                    "nodeCredentialType": "slackApi", "sendBody": True, "specifyBody": "json",
                    "jsonBody": "={{ JSON.stringify({ channel: $json.channel, text: $json.text, blocks: $json.blocks }) }}", "options": {}},
     "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [lx + 1000, ly + 400], "id": str(uuid.uuid4()), "name": "Send Mine",
     "credentials": SLACK_CRED, "onError": "continueRegularOutput"},
])
assert [c["node"] for c in C["Late Menu?"]["main"][1]] == ["Early Room Plan"]
C["Late Menu?"]["main"][1] = [{"node": "Mine Check", "type": "main", "index": 0}]
C["Mine Check"] = {"main": [[{"node": "Mine?", "type": "main", "index": 0}]]}
C["Mine?"] = {"main": [[{"node": "List My Window", "type": "main", "index": 0}], [{"node": "Early Room Plan", "type": "main", "index": 0}]]}
C["List My Window"] = {"main": [[{"node": "Mine Reply", "type": "main", "index": 0}]]}
C["Mine Reply"] = {"main": [[{"node": "Send Mine", "type": "main", "index": 0}]]}
C["Send Mine"] = {"main": [[{"node": "Turn Log Row", "type": "main", "index": 0}, {"node": "Clear Ack", "type": "main", "index": 0}]]}
by = {n["name"]: n for n in wf["nodes"]}
patch("Turn Log Row", [
    ("  try { if (!mn) mn = $('Send Late Menu').first().json || null; } catch (e) {}   // v267\n",
     "  try { if (!mn) mn = $('Send Late Menu').first().json || null; } catch (e) {}   // v267\n  let mi = null; try { mi = $('Send Mine').first().json || null; } catch (e) {}   // v272\n"),
    ("fo ? 'form offer' : cr ? 'change offer' : mn ? 'menu' : 'agent';", "fo ? 'form offer' : cr ? 'change offer' : mi ? 'my bookings' : mn ? 'menu' : 'agent';"),
])

# ---- 4: the question rules back in the prompt
ag = by["Jessie AI Agent"]["parameters"]["options"]
sm = ag["systemMessage"]


def prep(a, b):
    global sm
    assert sm.count(a) == 1, a[:70]
    sm = sm.replace(a, b)


prep("""- If it is none of these, say in one line what you can help with: questions about the studios and the calendar here, and booking through the buttons below.""",
     """- If it is none of these, say in one line what you can help with: questions about the studios and the calendar here, and booking through the buttons below.

*Each question stands alone.* Answer only what this message asks. Never carry a date, a time or a room over from an earlier message unless they point back to it ("that day", "same time", "then").

*Relay, don't invent.* Never invent a reason or a detail a tool did not give - "I'm not sure" beats a confident wrong answer. Never say how you searched or filtered; give the answer.""")
prep("""*Show:* title, date with the weekday (always, in groups too), time, and for Studio and Localization bookings only, the plain room name ("Studio 8").""",
     """*Show only:* title, date with the weekday (always, in groups too), time, and for Studio and Localization bookings only, the plain room name ("Studio 8"). Never add who booked it, the engineer, the arranger, the client or notes unless they ask for them, and never open with how you searched.""")
prep("""## Style

Philippine time (UTC+8). You write Slack mrkdwn - single asterisks for *bold*. Casual, friendly and direct - busy studio staff, not documentation. Match their language (English or Taglish) but never their tone: warm, even and professional.""",
     """## Style

*Timezone.* Philippine Standard Time, UTC+8.

*Slack formatting.* You write Slack mrkdwn, not Markdown - single asterisks for *bold*.

*Tone.* Casual, friendly and direct - busy studio staff, not documentation. Small chunks, line breaks between ideas. Match their language (English or Taglish) but never their tone: no slang, endearments, terms of address or emotional escalation, and don't turn apologetic or defensive when someone is annoyed. Stay warm, even and professional.

Good: "Studio 8 is taken from 2 to 4 PM. Studio 7 and Studio F are free then."

Avoid: "To accommodate your 10:00 PM–12:00 AM slot, the total time required is 9:45 PM–12:15 AM. Please confirm if this is correct...\"""")   # the old prompt's own example - never one that shows the habit being stopped (gotcha 6)
ag["systemMessage"] = sm

wf["name"] = "Project Jessie — v272 (round 3: questions answered cleanly)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes; prompt", len(sm), "characters")
