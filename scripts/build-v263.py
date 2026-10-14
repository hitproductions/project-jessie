#!/usr/bin/env python3
"""main v263 (typed booking -> form): a typed booking request no longer goes the chat-card way. Code reads what was typed
(date, time, room, session type, project, client, engineer, arranger), answers with what it read and a Book a room button,
and the button opens the booking form with those filled in (Jessie — Slack Interactions v9). The form then checks the room
(only free rooms are offered) and Book Session books it - the same checks as the chat, without the chat's card.

Decided 14 Oct after the step B test: a typed request with a taken studio led into the chat's free-text loop; the form
shows only free rooms, so the risky part moves there.

What still goes to the agent, unchanged: questions ("is studio 7 free friday?", "what do I have tomorrow?"), cancel and
move (until step C), a series (until the form has Repeats), a yes or no to a chat card already shown, and anything after an
offer that adds nothing new. Typing more details after an offer ("make it 3-5pm", "client is Jem Lim") gets a new offer
with them added.

Built on workflows/imported/project-jessie-v262-imported.json (the live download). New nodes on Already Done?'s "not done"
output: Form Offer -> Form Offer? -> Send Form Offer -> Turn Log Row + Clear Ack; otherwise Early Room Plan as before.
Turn Log Row says "form offer" / "menu" as the path.
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v262-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v263.json")
SLACK_CRED = {"slackApi": {"id": "EcX8szEJrOLYLUfl", "name": "Jessie Slack (signed)"}}

wf = json.load(open(SRC))
nodes = wf["nodes"]
by = {n["name"]: n for n in nodes}
assert "Form Offer" not in by
x, y = by["Already Done?"]["position"]

FORM_OFFER = r"""// Form Offer (main v263): a typed booking request is answered by code - what was read, and a Book a room button that
// opens the booking form with it filled in (Jessie — Slack Interactions v9). The form shows only free rooms and books
// through Book Session. Questions, cancel / move, a series, a yes / no to a chat card, and anything after an offer that
// adds nothing new still go to the agent. Never throws: on any doubt, no offer (the agent answers as before).
const item = Object.assign({}, $input.first().json);
const fo = { offer: false, why: '', channel: '', text: '', blocks: [], prefill: {} };
try {
  const g = $('Gate Context').first().json || {}, gate = g.gate || {};
  const bf = $('Booked For').first().json || {};
  const trig = $('Slack Trigger').first().json || {};
  fo.channel = String(trig.channel || '');
  const clean = s => String(s || '').replace(/\*sent using\*[\s\S]*$/i, '').replace(/<[^>]+>/g, ' ').trim();
  const t = clean(trig.text);
  const ctx = String(bf.requesterText || t);
  const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  // the newest message of Jessie's before this one, and the form offer in it (the button's value is the prefill)
  let msgs = []; try { msgs = $('Get Recent Messages').all().map(i => (i && i.json) || {}); } catch (e) {}
  const isBot = m => Boolean(m.bot_id || (m.message && m.message.bot_id)) || m.subtype === 'bot_message';
  const tts = String(trig.ts || '');
  let lastBot = null;
  for (const m of msgs) { if (tts && String(m.ts || '') === tts) continue; if (isBot(m)) { lastBot = m; break; } }
  let prev = null;
  try { for (const b of (lastBot && lastBot.blocks) || []) for (const e of b.elements || [])
    if (e.action_id === 'open_book' && /^\{/.test(String(e.value || ''))) prev = JSON.parse(e.value); } catch (e) { prev = null; }
  const skip = why => { fo.why = why; return true; };
  const intent = /\b(book|rebook|reserve)\b/i.test(t)
    && !/\b(?:what|which|when|where|who|how|do i|did i|have i)\b[^?]*\b(?:book|booked)\b[^?]*\?/i.test(t);
  if (g.confirmed || g.confirmedCancel || g.confirmedMove) skip('a yes to a chat card');
  else if (gate.presentedBook || gate.presentedCancel || gate.presentedMove) skip('answering a chat card');
  else if (/\b(?:cancel|move|moving|moved|resched\w*|delete|remove)\b/i.test(t)) skip('a cancel or move');
  else if (/\b(?:every|weekly|daily|biweekly|fortnightly|recurring|series|weekdays)\b/i.test(t)) skip('a series');
  else if (/\b(?:free|available|availability|vacant|open)\b/i.test(t) && (/\?/.test(t) || /^\s*(?:is|are|any|which|what|check)\b/i.test(t))) skip('an availability question');
  else if (!intent && !prev) skip('not a booking request');
  if (!fo.why) {
    // ---- what was typed, read by code
    const P = {};
    if (prev && !intent) Object.assign(P, prev);                    // more details after an offer: build on it
    const dates = String(g.datesInMessage || '').split(',').map(s => s.trim()).filter(s => /^\d{4}-\d{2}-\d{2}$/.test(s));
    if (dates.length === 1) P.d = dates[0];
    else if (dates.length > 1) delete P.d;
    if (/^\d{2}:\d{2}$/.test(String(bf.timeStart || '')) && /^\d{2}:\d{2}$/.test(String(bf.timeEnd || '')) && bf.timeStart < bf.timeEnd) {
      P.s = bf.timeStart; P.e = bf.timeEnd; }
    const roomRows = $('All Rooms').all().map(i => (i.json || {}).fields || {}).filter(f => f['Room Name']);
    const NAMES = roomRows.map(f => String(f['Room Name']).trim());
    const roomsIn = s => {
      const hit = new Set(), x = String(s || ''); let m;
      const r1 = /\bstudio\s*([1-8a-fm])\b/gi; while ((m = r1.exec(x))) hit.add('Studio ' + m[1].toUpperCase());
      const r2 = /\bm[\s-]?booth\s*([1-8])\b|\bm-?([1-8])\b/gi; while ((m = r2.exec(x))) hit.add('M' + (m[1] || m[2]));
      for (const n of NAMES) if (!/^Studio\s|^M[1-8]$/i.test(n) && new RegExp('\\b' + esc(n) + '\\b', 'i').test(x)) hit.add(n);
      return [...hit].filter(n => NAMES.indexOf(n) !== -1);
    };
    const rNow = roomsIn(t), rAll = roomsIn(ctx);
    if (rNow.length === 1) P.r = rNow[0]; else if (rNow.length > 1) delete P.r; else if (!P.r && rAll.length === 1) P.r = rAll[0];
    // the session type: the longest type named in full, else one word that only one type has ("vo", "dubbing")
    const TYPES = $('All Session Types').all().map(i => String((((i.json || {}).fields || {}).Type) || '').trim()).filter(Boolean);
    const typeIn = s => {
      let best = '';
      for (const ty of TYPES) if (ty.length > best.length && new RegExp('\\b' + esc(ty) + '\\b', 'i').test(s)) best = ty;
      if (best) return best;
      const ALIAS = { voiceover: 'vo', 'voice over': 'vo', celeb: 'celebrity', dub: 'dubbing', meeting: 'meeting', meetings: 'meeting' };
      const words = String(s).toLowerCase().replace(/voice over/g, 'voiceover').split(/[^a-z0-9]+/).map(w => ALIAS[w] || w)
        .filter(w => w.length >= 2 && ['recording', 'session', 'music', 'post', 'studio', 'room', 'booth', 'for', 'the', 'and', 'book'].indexOf(w) === -1);
      for (const w of words) { const hits = TYPES.filter(ty => new RegExp('\\b' + esc(w) + '\\b', 'i').test(ty)); if (hits.length === 1) return hits[0]; }
      return '';
    };
    const tyNow = typeIn(t), tyAll = typeIn(ctx);
    if (tyNow) P.p = tyNow; else if (!P.p && tyAll) P.p = tyAll;
    const rf = P.r ? roomRows.find(f => String(f['Room Name']).trim() === P.r) || {} : {};
    const rk = [].concat(rf['Room Type'] || []).map(v => String(v).toLowerCase());
    if (P.r && /^M[1-8]$/.test(P.r) && !P.p) P.p = '__booth';
    if (P.r && !P.p && (rk.indexOf('conference room') !== -1 || rk.indexOf('lobby') !== -1) && TYPES.indexOf('Meeting') !== -1) P.p = 'Meeting';
    // project, client, people - Booked For's reading of this booking's messages
    const cut = (s, n) => String(s || '').trim().slice(0, n);
    if (bf.project) P.pj = cut(bf.project, 80);
    if (bf.projectCode) P.cd = cut(bf.projectCode, 40);
    const client = bf.client || bf.forClient || '';
    if (client && !/^none$/i.test(client)) P.c = cut(client, 80);
    const staff = $('All Bookers').all().map(i => (i.json || {}).fields || {}).filter(f => f.Name);
    const slackOf = name => { const f = staff.find(s => String(s.Name).trim().toLowerCase() === String(name || '').trim().toLowerCase());
      return f ? String(f['Slack User ID'] || '').split(/[\s,]+/).filter(Boolean)[0] || '' : ''; };
    if (bf.engineer && bf.engineerResolved) { const id = slackOf(bf.engineer); if (id) { P.en = id; P.enN = cut(bf.engineer, 60); } }
    if (bf.arranger && bf.arrangerResolved) { const id = slackOf(bf.arranger); if (id) { P.ar = id; P.arN = cut(bf.arranger, 60); } }
    if (prev && !intent && JSON.stringify(P) === JSON.stringify(prev)) skip('nothing new after an offer');
    else {
      // ---- the reply, written by code
      const fmtT = hm => { let [h, m] = hm.split(':').map(Number); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(m).padStart(2, '0') + ' ' + ap; };
      const dl = P.d ? new Date(P.d + 'T12:00:00+08:00').toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' }) : '';
      const head = [P.r, dl, P.s ? fmtT(P.s) + ' – ' + fmtT(P.e) : ''].filter(Boolean).join(' · ');
      const more = [P.p === '__booth' ? 'M booth' : P.p, P.pj ? 'Project ' + P.pj : '', P.cd ? 'Code ' + P.cd : '', P.c ? 'Client ' + P.c : '',
        P.enN ? 'Engineer ' + P.enN : '', P.arN ? 'Arranger ' + P.arN : ''].filter(Boolean).join(' · ');
      const any = !!(head || more);
      const lines = any ? ['Here’s what I have so far:'].concat(head ? ['🗓️ *' + head + '*'] : []).concat(more ? [more] : [])
                        : ['Let’s book it with the form.'];
      const value = JSON.stringify(P);
      fo.prefill = P;
      fo.text = lines.join('\n');
      fo.blocks = [
        { type: 'section', text: { type: 'mrkdwn', text: fo.text } },
        { type: 'actions', elements: [{ type: 'button', style: 'primary', action_id: 'open_book', value: value.length <= 1900 ? value : '{}',
          text: { type: 'plain_text', text: 'Book a room' } }] },
        { type: 'context', elements: [{ type: 'mrkdwn', text: any ? 'Opens the form with these filled in - only free rooms are offered.' : 'Pick the date, time and room in the form.' }] }
      ];
      fo.offer = !!fo.channel;
      fo.why = intent ? 'a booking request' : 'more details after an offer';
    }
  }
} catch (e) { fo.offer = false; fo.why = 'error: ' + ((e && e.message) || e); }
item.formOffer = fo;
return [{ json: item }];"""

new_nodes = [
    {"parameters": {"jsCode": FORM_OFFER}, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [x + 200, y + 260],
     "id": str(uuid.uuid4()), "name": "Form Offer"},
    {"parameters": {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
                                   "conditions": [{"id": str(uuid.uuid4()), "leftValue": "={{ ($json.formOffer || {}).offer === true }}", "rightValue": True,
                                                   "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                                   "combinator": "and"}, "options": {}},
     "type": "n8n-nodes-base.if", "typeVersion": 2.2, "position": [x + 400, y + 260], "id": str(uuid.uuid4()), "name": "Form Offer?"},
    {"parameters": {"method": "POST", "url": "https://slack.com/api/chat.postMessage", "authentication": "predefinedCredentialType",
                    "nodeCredentialType": "slackApi", "sendBody": True, "specifyBody": "json",
                    "jsonBody": "={{ JSON.stringify({ channel: $json.formOffer.channel, text: $json.formOffer.text, blocks: $json.formOffer.blocks }) }}",
                    "options": {}},
     "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [x + 600, y + 400], "id": str(uuid.uuid4()),
     "name": "Send Form Offer", "credentials": SLACK_CRED, "onError": "continueRegularOutput"},
]
nodes.extend(new_nodes)

C = wf["connections"]
outs = C["Already Done?"]["main"]
assert [c["node"] for c in outs[1]] == ["Early Room Plan"], outs
outs[1] = [{"node": "Form Offer", "type": "main", "index": 0}]
C["Form Offer"] = {"main": [[{"node": "Form Offer?", "type": "main", "index": 0}]]}
C["Form Offer?"] = {"main": [[{"node": "Send Form Offer", "type": "main", "index": 0}], [{"node": "Early Room Plan", "type": "main", "index": 0}]]}
C["Send Form Offer"] = {"main": [[{"node": "Turn Log Row", "type": "main", "index": 0}, {"node": "Clear Ack", "type": "main", "index": 0}]]}

# Turn Log Row: the menu and the form offer are their own paths (they were logged as "agent")
tl = by["Turn Log Row"]["parameters"]
old = "  try { ad = $('Already Done Reply').first().json || null; } catch (e) {}\n"
assert old in tl["jsCode"]
tl["jsCode"] = tl["jsCode"].replace(old, old + "  let fo = null, mn = null;   // v263\n"
    "  try { fo = $('Send Form Offer').first().json || null; } catch (e) {}\n"
    "  try { mn = $('Send Menu').first().json || null; } catch (e) {}\n", 1)
old = "ad ? 'already done' : 'agent';"
assert old in tl["jsCode"]
tl["jsCode"] = tl["jsCode"].replace(old, "ad ? 'already done' : fo ? 'form offer' : mn ? 'menu' : 'agent';", 1)

wf["name"] = "Project Jessie — v263 (typed booking to form)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(nodes), "nodes")
