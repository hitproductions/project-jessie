#!/usr/bin/env python3
"""main v265 (typed cancel / change -> buttons; anything else -> the menu): step C2 of the Slack-app slice 1. A typed cancel or change ("cancel ORANGE
saturday", "make it 3-5pm", "move it to friday", "change my booking") no longer goes to the agent's chat cards (no
confirmation is typed - decided 15 Oct). Code finds the requester's bookings (made, or engineered / arranged - "team:"),
from today for 60 days, by the words they typed, the date, the time or the room - or, with nothing to go on, the booking
in Jessie's newest message that has one ("make it 3-5pm" right after Booked) - and answers with each booking and its
Change / Cancel buttons (Slack Interactions v11/v12): Cancel asks with Slack's pop-up, Change opens the form at the new
time typed. Nothing found: says so, with a My bookings button.

Still the agent's: questions, a yes / no to a chat card already shown (Cancel Direct / Move Direct carry those out as
before), a series. Built on workflows/imported/project-jessie-v264-imported.json (the live download). New nodes on Form
Offer?'s "no offer" output: Change Offer -> Change Offer? -> List Mine (calendar) -> Change Reply -> Send Change Reply ->
Turn Log Row + Clear Ack; otherwise Early Room Plan as before. Turn Log Row logs "change offer".

Also (Howard, 15 Oct 10:50: "what's up" got "Hi Howard! What do you need?" from the agent): Menu Check sends the menu for
"what's up" / "how are you", thanks ("Anytime! Anything else?"), and any short message that asks nothing and is not about a
booking - unless Jessie is waiting for an answer (her newest message asks something, is a card awaiting yes / no, or is
a form offer). The agent gets questions and answers.
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v264-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v265.json")
SLACK_CRED = {"slackApi": {"id": "EcX8szEJrOLYLUfl", "name": "Jessie Slack (signed)"}}
GCAL_CRED = {"googleCalendarOAuth2Api": {"id": "6D1r3kaq6KaFdL0a", "name": "Google Calendar account"}}
CAL = "c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com"

wf = json.load(open(SRC))
nodes = wf["nodes"]
by = {n["name"]: n for n in nodes}
assert "Change Offer" not in by
x, y = by["Form Offer?"]["position"]

ROW_JS = r"""
// Booking rows - the same blocks Slack Interactions v11 renders (bk_<id> + bka_<id>), so its Change / Cancel handle them.
const _DS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'], _MS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
function t12(hm) { if (!hm) return ''; let [h, m] = String(hm).split(':').map(Number); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(m).padStart(2, '0') + ' ' + ap; }
function dayShort(d) { const x = new Date(d + 'T12:00:00Z'); return _DS[x.getUTCDay()] + ', ' + _MS[x.getUTCMonth()] + ' ' + x.getUTCDate(); }
function whenLine(b) { return dayShort(b.d) + ' · ' + (b.s ? t12(b.s) + ' – ' + t12(b.e) : 'all day') + (b.r ? ' · ' + b.r : ''); }
function mins(hm) { const m = String(hm || '').match(/^(\d{2}):(\d{2})$/); return m ? +m[1] * 60 + +m[2] : null; }
function hhmm(n) { return String(Math.floor(n / 60)).padStart(2, '0') + ':' + String(n % 60).padStart(2, '0'); }
// the new values: what was typed over the booking's own; a start alone keeps the length
function newOf(b, n) {
  n = n || {}; const o = { d: n.d || b.d, s: b.s, e: b.e, r: n.r || b.r };
  if (n.s && n.e) { o.s = n.s; o.e = n.e; }
  else if (n.s && mins(b.s) !== null && mins(b.e) !== null) { const e = mins(n.s) + (mins(b.e) - mins(b.s)); o.s = n.s; o.e = e < 1440 ? hhmm(e) : ''; }
  else if (n.e) o.e = n.e;
  return o;
}
function bkValue(b, n) { const v = { id: b.id, d: b.d, s: b.s || '', e: b.e || '', r: b.r || '', t: String(b.t || '').slice(0, 150) };
  if (n && Object.keys(n).length) v.n = n; return JSON.stringify(v); }
function bkButtons(b, n) {
  const pt = x => ({ type: 'plain_text', text: x });
  return { type: 'actions', block_id: 'bka_' + b.id, elements: [
    { type: 'button', action_id: 'bk_change', value: bkValue(b, n), text: pt('Change') },
    { type: 'button', action_id: 'bk_cancel', style: 'danger', value: bkValue(b), text: pt('Cancel'),
      confirm: { title: pt('Cancel this booking?'), text: { type: 'mrkdwn', text: ('*' + b.t + '*\n' + whenLine(b)).slice(0, 290) },
                 confirm: pt('Cancel booking'), deny: pt('Keep it'), style: 'danger' } } ] };
}
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

CHANGE_OFFER = r"""// Change Offer (main v265): a typed cancel or change is answered by code with the booking(s) and their Change / Cancel
// buttons - no chat card, no typed yes. This decides whether, and what to look for; List Mine reads the calendar and
// Change Reply writes the answer. Never throws: on any doubt, the agent answers as before.
const item = Object.assign({}, $input.first().json);
const co = { go: false, why: '', kind: '', words: [], dates: [], fDates: [], time: '', fRooms: [], n: {}, recent: null, timeMin: '', timeMax: '', channel: '', user: '' };
try {
  const g = $('Gate Context').first().json || {}, gate = g.gate || {};
  const bf = $('Booked For').first().json || {};
  const trig = $('Slack Trigger').first().json || {};
  co.channel = String(trig.channel || ''); co.user = String(trig.user || '');
  const t = String(trig.text || '').replace(/\*sent using\*[\s\S]*$/i, '').replace(/<[^>]+>/g, ' ').trim();
  const skip = why => { co.why = why; return true; };
  const cancel = /\b(?:cancel|delete|remove)\b/i.test(t);
  const change = !cancel && (/\b(?:move|moving|resched\w*|change|push|pull|extend|shorten|switch)\b/i.test(t) || /\bmake it\b/i.test(t)
    || /\b(?:instead|earlier|later)\b/i.test(t));
  if (g.confirmed || g.confirmedCancel || g.confirmedMove) skip('a yes to a chat card');
  else if (gate.presentedBook || gate.presentedCancel || gate.presentedMove) skip('answering a chat card');
  else if (/\b(?:free|available|availability|vacant)\b/i.test(t) && /\?/.test(t)) skip('an availability question');
  else if (/\b(?:every|weekly|daily|recurring|series)\b/i.test(t)) skip('a series');
  else if (!cancel && !change) skip('not a cancel or change');
  if (!co.why) {
    co.kind = cancel ? 'cancel' : 'change';
    // the booking in Jessie's newest message that has one (its Change button carries it)
    let msgs = []; try { msgs = $('Get Recent Messages').all().map(i => (i && i.json) || {}); } catch (e) {}
    const isBot = m => Boolean(m.bot_id || (m.message && m.message.bot_id)) || m.subtype === 'bot_message';
    for (const m of msgs) { if (String(m.ts || '') === String(trig.ts || '') || !isBot(m)) continue;
      const vals = []; for (const b of m.blocks || []) for (const e of b.elements || []) if (e.action_id === 'bk_change') { try { vals.push(JSON.parse(e.value)); } catch (er) {} }
      if (vals.length === 1) co.recent = vals[0];
      break; }
    // what they typed: dates, a time, rooms, the words of a title
    const dates = String(g.datesInMessage || '').split(',').map(s => s.trim()).filter(s => /^\d{4}-\d{2}-\d{2}$/.test(s));
    let s = '', e = '';
    if (bf.timeInNewest && /^\d{2}:\d{2}$/.test(String(bf.timeStart || '')) && /^\d{2}:\d{2}$/.test(String(bf.timeEnd || ''))) { s = bf.timeStart; e = bf.timeEnd; }
    else { const m = t.match(/\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|nn)\b|\b(noon)\b/i);
      if (m) { let h = m[4] ? 12 : +m[1]; const mm = m[2] ? +m[2] : 0, ap = (m[3] || '').toLowerCase();
        if (ap === 'pm' && h < 12) h += 12; if (ap === 'am' && h === 12) h = 0; if (h < 24 && mm < 60) s = String(h).padStart(2, '0') + ':' + String(mm).padStart(2, '0'); } }
    const rooms = []; { let m; const r1 = /\bstudio\s*([1-8a-fm])\b/gi; while ((m = r1.exec(t))) rooms.push('Studio ' + m[1].toUpperCase());
      const r2 = /\bm[\s-]?booth\s*([1-8])\b|\bm-?([1-8])\b/gi; while ((m = r2.exec(t))) rooms.push('M' + (m[1] || m[2]));
      for (const n of ['Likha', 'Salin', 'Katha', 'Lobby']) if (new RegExp('\\b' + n + '\\b', 'i').test(t)) rooms.push(n); }
    const STOP = new Set(('cancel delete remove move moving change push pull extend shorten switch make it instead earlier later reschedule rescheduled '
      + 'my the a an booking bookings session sessions room studio booth to on at for from in and or of please pls po it that this one me i we our '
      + 'can could would you jessie need want to today tomorrow tonight next week day days monday tuesday wednesday thursday friday saturday sunday '
      + 'mon tue tues wed thu thur thurs fri sat sun jan january feb february mar march apr april may jun june jul july aug august sep sept september '
      + 'oct october nov november dec december am pm nn noon instead hours hour mins minutes until till by with no not just also again actually').split(' '));
    co.words = (t.toLowerCase().match(/[a-z0-9][a-z0-9&'-]*/g) || []).filter(w => w.length >= 3 && !STOP.has(w) && !/^\d+(?:am|pm)?$/.test(w)
      && !/^(?:m[1-8]|[1-8a-f])$/.test(w) && !/^\d[\d:-]*(?:am|pm|nn)?$/.test(w));
    if (cancel) { co.fDates = dates; co.time = s; co.fRooms = rooms; }
    else {
      co.n = {};
      if (dates.length) co.n.d = dates[dates.length - 1];
      if (s) co.n.s = s; if (e) co.n.e = e;
      if (rooms.length) co.n.r = rooms[rooms.length - 1];
      if (dates.length > 1) co.fDates = [dates[0]];
      if (rooms.length > 1) co.fRooms = [rooms[0]];
    }
    const today = /^\d{4}-\d{2}-\d{2}$/.test(String(g.todayIso || '')) ? g.todayIso : new Date(Date.now() + 8 * 3600000).toISOString().slice(0, 10);
    const lo = [today].concat(co.fDates).sort()[0];
    co.timeMin = lo + 'T00:00:00+08:00';
    co.timeMax = new Date(Date.parse(today + 'T12:00:00Z') + 61 * 86400000).toISOString().slice(0, 10) + 'T00:00:00+08:00';
    co.go = !!co.channel && !!co.user;
    co.why = co.kind;
  }
} catch (e) { co.go = false; co.why = 'error: ' + ((e && e.message) || e); }
item.changeOffer = co;
return [{ json: item }];"""

CHANGE_REPLY = ROW_JS + r"""
// Change Reply (main v265): the requester's bookings (made, or engineered / arranged) that match what they typed - or the
// one in Jessie's newest message - each with Change / Cancel. Change opens the form at the new time typed.
const co = ($('Change Offer').first().json || {}).changeOffer || {};
const res = $input.first().json || {};
const md = t => ({ type: 'mrkdwn', text: t });
let list = [];
const ok = Array.isArray(res.items);
if (ok) for (const e of res.items) {
  if (!e || e.status === 'cancelled') continue;
  const desc = String(e.description || '');
  const ref = (desc.match(/ref:\s*([A-Za-z0-9]+)/) || [])[1] || '';
  const team = ((desc.match(/team:\s*([^|]+)/) || [])[1] || '').split(/[\s,]+/).filter(Boolean);
  if (ref === co.user || team.indexOf(co.user) !== -1) list.push(evBooking(e));
}
const any = co.words.length || co.fDates.length || co.fRooms.length || (co.kind === 'cancel' && co.time);
if (co.words.length) list = list.filter(b => co.words.every(w => String(b.t).toLowerCase().indexOf(w) !== -1));
if (co.fDates.length) list = list.filter(b => co.fDates.indexOf(b.d) !== -1);
if (co.fRooms.length) list = list.filter(b => co.fRooms.some(r => String(b.r).toLowerCase().split(/,\s*/).indexOf(r.toLowerCase()) !== -1));
if (co.kind === 'cancel' && co.time) { const at = list.filter(b => b.s === co.time); if (at.length) list = at; }
let fromRecent = false;
if (!any && co.recent && co.recent.id) {
  const hit = list.filter(b => b.id === co.recent.id);
  list = hit.length ? hit : [co.recent]; fromRecent = true;
}
list.sort((a, b) => (a.d + (a.s || '00:00')).localeCompare(b.d + (b.s || '00:00')));
const blocks = [];
const n = co.kind === 'change' ? co.n : null;
if (!ok && !fromRecent) blocks.push({ type: 'section', text: md('⚠️ The calendar couldn’t be read. Try again in a moment.') });
else if (!list.length) {
  const what = (co.words.length ? ' called "' + co.words.join(' ') + '"' : '') + (co.fDates.length ? ' on ' + dayShort(co.fDates[0]) : '') + (co.fRooms.length ? ' in ' + co.fRooms[0] : '');
  blocks.push({ type: 'section', text: md('I couldn’t find a booking of yours' + what + ' from today on.') },
    { type: 'actions', elements: [{ type: 'button', action_id: 'my_bookings', value: 'menu', text: { type: 'plain_text', text: 'My bookings' } }] });
} else {
  const one = list.length === 1;
  const hasNew = n && Object.keys(n).length;
  blocks.push({ type: 'section', text: md(!one ? 'Which one?' : co.kind === 'cancel' ? 'Here it is - press *Cancel* to cancel it.'
    : hasNew ? 'Here it is - press *Change* to check the new time.' : 'Here it is - press *Change* to pick the new time.') });
  for (const b of list.slice(0, 10)) {
    const nw = hasNew ? newOf(b, n) : null;
    blocks.push({ type: 'section', block_id: 'bk_' + b.id, text: md('*' + b.t + '*\n' + (one && nw ? 'Now: ' : '') + whenLine(b)
      + (one && nw && nw.e ? '\nNew: ' + whenLine(nw) : '')) }, bkButtons(b, hasNew ? n : null));
  }
  if (list.length > 10) blocks.push({ type: 'context', elements: [md('Showing the first 10 of ' + list.length + ' - add the title or the date to narrow it.')] });
}
const text = String(((blocks[0] || {}).text || {}).text || 'Your booking');
return [{ json: { channel: co.channel, text, blocks, count: list.length } }];"""

MENU_CHECK = r"""// Menu Check (main v262; v265: anything that is not a booking, a question or an answer gets the menu): a greeting ("hi",
// "what's up"), "menu", "help", thanks, or a short message that asks nothing and is not about a booking ("test") gets the
// Slack-app menu (Book a room · My bookings) instead of the agent - the scope's "off-topic and not understood -> the menu".
// Never when Jessie is waiting for an answer: her newest message asks something, is a card awaiting yes / no, or is a
// booking-form reply with a button (a typed detail goes to Form Offer). The menu's buttons are handled by Jessie — Slack Interactions.
const trig = $('Slack Trigger').first().json || {};
const raw = String(trig.text || '');
const body = raw.replace(/\*sent using\*[\s\S]*$/i, '').replace(/<[^>]+>/g, ' ').replace(/:[a-z0-9_+\-]+:/gi, ' ').trim();
const t = body.toLowerCase().replace(/[’']/g, '').replace(/[^a-z0-9?\s]/g, ' ').replace(/\s+/g, ' ').trim();
const FILL = new Set(['jessie', 'po', 'there', 'again', 'pls', 'please', 'naman', 'ulit']);
const phrase = t.replace(/\?/g, '').split(' ').filter(w => w && !FILL.has(w)).join(' ');
const GREET = ['hi', 'hello', 'hey', 'heya', 'hiya', 'yo', 'sup', 'hola', 'good morning', 'good afternoon', 'good evening',
  'good day', 'morning', 'afternoon', 'evening', 'gm', 'menu', 'help', 'start', 'options', 'kumusta', 'musta', 'hoy', 'uy',
  'whats up', 'wassup', 'whatsup', 'wazzup', 'how are you', 'how r u', 'hows it going', 'whats new', 'hi whats up', 'hey whats up'];   // v265
const THANKS = /^(?:thanks?|thank you|thank u|ty|tysm|salamat|thanks a lot|ok(?:ay)?|ok thanks|okay thanks|cool|great|nice|got it|noted|sige)$/;   // v265
let menu = raw.trim() !== '' && (phrase === '' || GREET.indexOf(phrase) !== -1 || /^(h+i+|he+y+|hel+o+)$/.test(phrase));
let why = menu ? 'greeting' : '';
const thanks = THANKS.test(phrase);
// v265: not a greeting - the menu only when nothing is waiting for an answer and the message is neither a question nor
// about a booking
try {
  if (!menu) {
    const g = $('Gate Context').first().json || {}, gate = g.gate || {};
    let msgs = []; try { msgs = $('Get Recent Messages').all().map(i => (i && i.json) || {}); } catch (e) {}
    const isBot = m => Boolean(m.bot_id || (m.message && m.message.bot_id)) || m.subtype === 'bot_message';
    let last = null; for (const m of msgs) { if (String(m.ts || '') === String(trig.ts || '')) continue; if (isBot(m)) { last = m; break; } }
    const lastText = String((last && (last.text || (last.message && last.message.text))) || '').replace(/\*sent using\*[\s\S]*$/i, '').trim();
    const lastButtons = []; for (const b of (last && last.blocks) || []) for (const e of b.elements || []) if (e.action_id) lastButtons.push(e.action_id + ':' + String(e.value || '').slice(0, 1));
    const waiting = g.confirmed || g.confirmedCancel || g.confirmedMove || gate.presentedBook || gate.presentedCancel || gate.presentedMove
      || /\?\s*$/.test(lastText) || lastButtons.some(x => x === 'open_book:{');
    const question = /\?/.test(body) || /^(?:what|when|where|who|whos|whose|which|why|how|is|are|am|can|could|do|does|did|will|would|should|may|any|have|has)\b/.test(t);
    const booking = !!String(g.datesInMessage || '').trim()
      || /\b\d{1,2}(?::\d{2})?\s*(?:am|pm|nn)\b|\bnoon\b|\b\d{1,2}\s*-\s*\d{1,2}\b/.test(t)
      || /\b(?:book\w*|reserve|cancel\w*|delete|remove|move|moving|resched\w*|change|push|extend|shorten|make it|instead|earlier|later|studio|booth|room|rooms|session|record\w*|mix\w*|dub\w*|edit\w*|master\w*|meeting|likha|salin|katha|lobby|m[1-8]|client|engineer|arranger|project|free|available|availability|schedule|calendar|tomorrow|today|tonight|every|weekly|series|reset|yes|yeah|yep|no|nope)\b/.test(t);
    if (!waiting && !question && !booking && phrase.split(' ').length <= 8) { menu = true; why = thanks ? 'thanks' : 'not a booking or a question'; }
  }
} catch (e) {}
let first = '';
try { first = String((($('Get Booker').first().json || {}).fields || {}).Name || '').trim().split(/\s+/)[0]; } catch (e) {}
const head = why === 'thanks' ? 'Anytime! Anything else?' : why === 'not a booking or a question' ? 'I can help with bookings - what would you like to do?'
  : 'Hi' + (first ? ' ' + first : '') + '! What would you like to do?';
const blocks = [
  { type: 'section', text: { type: 'mrkdwn', text: head } },
  { type: 'actions', elements: [
    { type: 'button', style: 'primary', action_id: 'open_book', value: 'menu', text: { type: 'plain_text', text: 'Book a room' } },
    { type: 'button', action_id: 'my_bookings', value: 'menu', text: { type: 'plain_text', text: 'My bookings' } } ] },
  { type: 'context', elements: [{ type: 'mrkdwn', text: 'Or just type it, like _book studio 7 tomorrow 2-4pm_ or _is studio 8 free friday?_' }] }
];
return [{ json: { menu, why, phrase, blocks, channel: String(trig.channel || '') } }];"""

by["Menu Check"]["parameters"]["jsCode"] = MENU_CHECK
sm = by["Send Menu"]["parameters"]
assert "text: 'What would you like to do?'" in sm["jsonBody"]
sm["jsonBody"] = sm["jsonBody"].replace("text: 'What would you like to do?'", "text: $json.blocks[0].text.text")

new_nodes = [
    {"parameters": {"jsCode": CHANGE_OFFER}, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [x + 200, y + 260],
     "id": str(uuid.uuid4()), "name": "Change Offer"},
    {"parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
                                   "conditions": [{"id": str(uuid.uuid4()), "leftValue": "={{ ($json.changeOffer || {}).go === true }}", "rightValue": True,
                                                   "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                                   "combinator": "and"}, "options": {}},
     "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [x + 400, y + 260], "id": str(uuid.uuid4()), "name": "Change Offer?"},
    {"parameters": {"url": "=https://www.googleapis.com/calendar/v3/calendars/{{ encodeURIComponent('" + CAL + "') }}/events?timeMin={{ encodeURIComponent($json.changeOffer.timeMin) }}&timeMax={{ encodeURIComponent($json.changeOffer.timeMax) }}&singleEvents=true&orderBy=startTime&maxResults=2500",
                    "authentication": "predefinedCredentialType", "nodeCredentialType": "googleCalendarOAuth2Api", "options": {}},
     "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [x + 600, y + 400], "id": str(uuid.uuid4()), "name": "List Mine",
     "credentials": GCAL_CRED, "onError": "continueRegularOutput"},
    {"parameters": {"jsCode": CHANGE_REPLY}, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [x + 800, y + 400],
     "id": str(uuid.uuid4()), "name": "Change Reply"},
    {"parameters": {"method": "POST", "url": "https://slack.com/api/chat.postMessage", "authentication": "predefinedCredentialType",
                    "nodeCredentialType": "slackApi", "sendBody": True, "specifyBody": "json",
                    "jsonBody": "={{ JSON.stringify({ channel: $json.channel, text: $json.text, blocks: $json.blocks }) }}", "options": {}},
     "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [x + 1000, y + 400], "id": str(uuid.uuid4()),
     "name": "Send Change Reply", "credentials": SLACK_CRED, "onError": "continueRegularOutput"},
]
nodes.extend(new_nodes)
C = wf["connections"]
outs = C["Form Offer?"]["main"]
assert [c["node"] for c in outs[1]] == ["Early Room Plan"], outs
outs[1] = [{"node": "Change Offer", "type": "main", "index": 0}]
C["Change Offer"] = {"main": [[{"node": "Change Offer?", "type": "main", "index": 0}]]}
C["Change Offer?"] = {"main": [[{"node": "List Mine", "type": "main", "index": 0}], [{"node": "Early Room Plan", "type": "main", "index": 0}]]}
C["List Mine"] = {"main": [[{"node": "Change Reply", "type": "main", "index": 0}]]}
C["Change Reply"] = {"main": [[{"node": "Send Change Reply", "type": "main", "index": 0}]]}
C["Send Change Reply"] = {"main": [[{"node": "Turn Log Row", "type": "main", "index": 0}, {"node": "Clear Ack", "type": "main", "index": 0}]]}

tl = by["Turn Log Row"]["parameters"]
old = "  try { mn = $('Send Menu').first().json || null; } catch (e) {}\n"
assert old in tl["jsCode"]
tl["jsCode"] = tl["jsCode"].replace(old, old + "  let cr = null; try { cr = $('Send Change Reply').first().json || null; } catch (e) {}   // v265\n", 1)
old = "fo ? 'form offer' : mn ? 'menu' : 'agent';"
assert old in tl["jsCode"]
tl["jsCode"] = tl["jsCode"].replace(old, "fo ? 'form offer' : cr ? 'change offer' : mn ? 'menu' : 'agent';", 1)

wf["name"] = "Project Jessie — v265 (typed cancel / change, menu otherwise)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(nodes), "nodes")
