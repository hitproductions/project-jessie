#!/usr/bin/env python3
"""Builds workflows/project-jessie-v286.json - Project Jessie — v286 (room details), 28 Oct.

Howard's Slack test, 28 Oct ~10:31: "what rooms have symphony?" got only "Use Book a room or My bookings below." Two causes:
- the AI cannot see what a room has. Symphony is in Airtable's Equipment / Equipment (additional) (Studio 7, 8, C, F), but the
  prompt carries only room names and the session-type ranking, and the Rooms and Studios tool searches by name, format, kind,
  session type and vocal booth only - nothing searches Equipment, Workstation, Paired with or Capacity;
- Build Reply replaced a WHOLE reply with the pointer to the buttons whenever any sentence in it asked a booking question
  ("Which room would you like?"), so an answer that ended with one was thrown away.

v286:
1. **Facts Check -> Facts? -> Send Facts** (after Mine?, before the AI): questions about what the rooms have, answered in code
   from the rooms in the reference cache (every Rooms & Studios field, refreshed every 5 minutes - no Airtable call):
   "which rooms have <thing>" -> every room whose details name it, with the line that says so ("no Mac Studio" is not a match);
   a setup question about one named room ("what's in Studio F", "does Studio 8 have a Mac Studio?", "how many people fit in
   Likha?") -> that room's details. Availability, bookings, formats and session types still go to the AI and its tools.
2. **Room Table** writes every room's details as one line each (roomDetails) and the prompt carries them under *What each room
   has*, so the AI can answer the questions Facts Check does not catch from Airtable, not from memory - only when the message
   mentions a room or gear (Howard: no extra cost on every message). No new lookup anywhere: the rooms come from the reference
   cache main already reads on every message.
3. **Build Reply** drops only the sentences that ask for booking details; the answer before them stays. The pointer is used only
   when nothing else is left.
Built on workflows/imported/project-jessie-v285-imported.json (the live download).
"""
import copy
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "project-jessie-v285-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:120])
    return js.replace(a, b)


# The room facts, shared by Facts Check and Room Table (Code nodes cannot share code - keep the two copies the same)
FACTS = r"""const arrOf = v => [].concat(v == null ? [] : v).map(x => (x && typeof x === 'object') ? String(x.name || '') : String(x)).map(s => s.trim()).filter(Boolean);
const plainOf = s => String(s == null ? '' : s).replace(/\*+/g, '').replace(/[ \t]+/g, ' ').trim();
const capOf = s => s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
// one room's Airtable details as {label, text} - Room Type, Size + Capacity, Recording Format, Workstation, the vocal flags,
// Paired with, Prioritized For, Equipment (one per sentence) and Equipment (additional) under its own headings
function factsOf(f) {
  const out = [];
  const type = arrOf(f['Room Type']); if (type.length) out.push({ label: 'Room type', text: type.join(', ') });
  const size = plainOf(f['Size Category']), cp = Number(f['Capacity']);
  const people = Number.isFinite(cp) && cp > 0 ? 'up to ' + cp + (cp === 1 ? ' person' : ' people') : '';
  if (size || people) out.push({ label: 'Size', text: [size, people].filter(Boolean).join(' · ') });
  const fm = arrOf(f['Recording Format']).filter(x => !/^none$/i.test(x)); if (fm.length) out.push({ label: 'Formats', text: fm.join(', ') });
  const ws = arrOf(f['Workstation']); if (ws.length) out.push({ label: 'Workstation', text: ws.join(', ') });
  if (f['Vocal Booth'] === true) out.push({ label: 'Vocal booth', text: 'yes' });
  if (f['Records Vocals In-Room'] === true) out.push({ label: 'Vocals', text: 'recorded in the room' });
  const pw = plainOf(f['Paired with']); if (pw && !/^n\/?a$/i.test(pw)) out.push({ label: 'Paired with', text: pw });
  const pf = arrOf(f['Prioritized For']); if (pf.length) out.push({ label: 'Prioritized for', text: pf.join(', ') });
  for (const s of String(f['Equipment'] || '').split(/\n+|(?<=\.)\s+/)) { const x = plainOf(s).replace(/\.$/, ''); if (x) out.push({ label: 'Equipment', text: x }); }
  let head = 'Equipment';
  for (const ln of String(f['Equipment (additional)'] || '').split(/\n/)) {
    const h = ln.match(/^\s*\*\*\s*(.+?)\s*\*\*\s*$/); if (h) { head = capOf(h[1].trim()); continue; }
    const x = plainOf(ln.replace(/^\s*[-•*]\s*/, '')); if (x) out.push({ label: head, text: x });
  }
  return out;
}
// the facts grouped by label, in order: [[label, [texts]]]
function groupsOf(facts) {
  const g = [], at = {};
  for (const x of facts) { if (!(x.label in at)) { at[x.label] = g.length; g.push([x.label, []]); } g[at[x.label]][1].push(x.text); }
  return g;
}
"""

FACTS_CHECK = r"""// Facts Check (main v286, Howard 28 Oct: "what rooms have symphony?" got only "Use Book a room or My bookings below."):
// questions about what the rooms have - equipment, setup, workstation, capacity, pairing - answered in code from the rooms in
// the reference cache (every Rooms & Studios field; no Airtable call). Two shapes:
// - "which rooms have <thing>" -> every room whose details name it, with the line that says so ("no Mac Studio" is not a match);
// - a setup question about one named room ("what's in Studio F", "does Studio 8 have a Mac Studio?") -> that room's details.
// Availability, bookings, formats across rooms and session types go on to the AI and its tools. Never throws: on any doubt, the AI.
const item = Object.assign({}, $input.first().json);
const fc = { go: false, why: '', shape: '', term: '', rooms: [], channel: '', text: '', blocks: [] };
""" + FACTS + r"""
try {
  const g = $('Gate Context').first().json || {};
  const trig = $('Slack Trigger').first().json || {};
  fc.channel = String(trig.channel || '');
  const raw = String(trig.text || '').slice(0, 500).replace(/\*sent using\*[\s\S]*$/i, '').replace(/<[^>]+>/g, ' ');
  const t = raw.toLowerCase().replace(/[’']/g, '').replace(/[^a-z0-9.+&!\s\/-]/g, ' ').replace(/\s+/g, ' ').replace(/[.!]+$/, '').trim();
  const rooms = [];
  for (const it of $('All Rooms').all()) { const f = ((it && it.json) || {}).fields || {}; const nm = String(f['Room Name'] || '').trim(); if (nm) rooms.push({ name: nm, facts: factsOf(f) }); }
  const types = [];
  try { for (const it of $('All Session Types').all()) { const ty = String((((it && it.json) || {}).fields || {})['Type'] || '').trim().toLowerCase(); if (ty) types.push(ty); } } catch (e) {}
  const asks = /\?/.test(raw) || /^(?:what|whats|which|where|wheres|does|do|is|are|any|list|show|tell|how|can|got)\b/.test(t) || /\brooms? with\b/.test(t);
  const when = !!String(g.datesInMessage || '').trim()
    || /\b(?:free|available|availability|vacant|open|booked|book|booking|reserve|schedule|calendar|today|tomorrow|tonight|now|later|week|month|monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun|noon|cancel|move|change|taken|busy|occupied|reserved|left|sessions?|bookings?|meetings?|slots?|someone|anyone|anybody|who|whos|client|engineer|arranger|project)\b/.test(t)
    || /\b(?:at|from|until|till|by|on|before|after)\s+\d/.test(t)
    || /\b\d{1,2}(?::\d{2})?\s*(?:am|pm|nn)\b/.test(t) || /\bmy\b/.test(t);
  const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const FORMAT = /^(?:5\.1|7\.1|atmos|dolby(?: atmos)?|stereo(?: with sub)?|surround|mono)(?: (?:mixing|format|sound))?$/;
  const tidy = s => String(s || '').replace(/^(?:an?|the|any|some|a pair of)\s+/, '').replace(/\s+(?:setups?|set ups?|installed|in (?:it|them|there)|inside|please|pls|po|naman)$/g, '').trim();
  // a term as a regex: the words in order, the last one with or without its plural
  const termRe = term => {
    const w = term.split(/\s+/).filter(Boolean).map(esc); if (!w.length) return null;
    const last = w.pop(), sing = /[a-z]{3,}(?:es|s)$/.test(last) ? last.replace(/(?:es|s)$/, '') : last;
    return new RegExp('(^|[^a-z0-9])(' + w.concat(['(?:' + last + '|' + sing + '(?:es|s)?)']).join('[\\s-]*') + ')(?![a-z0-9])', 'i');
  };
  // the facts of one room that name the term - not after "no" / "without" / "not"
  const hitsIn = (room, re, labels) => room.facts.filter(x => {
    if (labels && labels.indexOf(x.label) === -1) return false;
    const m = re.exec(x.text); if (!m) return false;
    return !/\b(?:no|without|not)\s+(?:an?\s+)?$/i.test(x.text.slice(0, m.index + m[1].length));
  });
  // v286: Slack's three escapes on everything printed - Airtable text and the typed term never become a mention or a link
  const se = v => String(v == null ? '' : v).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const line = x => se((x.label === 'Equipment' ? '' : x.label + ': ') + x.text);
  const nat = (a, b) => a.localeCompare(b, undefined, { numeric: true });
  // rooms named in the message
  const named = rooms.filter(r => {
    const n = r.name.toLowerCase();
    let re;
    const st = n.match(/^studio\s+(\S+)$/), mb = n.match(/^m(\d)$/);
    if (st) re = new RegExp('\\bstudio\\s*' + esc(st[1]) + '\\b(?!\\s*(?:studio|mini))');
    else if (mb) re = new RegExp('\\bm[\\s-]?(?:booth\\s*)?' + mb[1] + '\\b');
    else re = new RegExp('\\b' + esc(n) + '\\b');
    return re.test(t);
  });
  const isType = term => types.some(ty => term === ty || term.indexOf(ty) !== -1 || (term.length > 4 && ty.indexOf(term) !== -1));
  if (!asks) fc.why = 'not a question';
  else if (when) fc.why = 'about a time or a booking';
  else if (!rooms.length) fc.why = 'no rooms in the cache';
  if (!fc.why) {
    // shape 1: which rooms have <thing>
    const m1 = t.match(/^(?:(?:which|what|wat|any|list(?: the| all)?|show(?: me)?(?: the| all)?)\s+)?(?:of the\s+)?(?:rooms?|studios?|booths?)\s+(?:(?:that|which)\s+)?(?:have|has|got|use|uses|come with|comes with|are equipped with|is equipped with|equipped with|with|carry|carries)\s+(.+)$/)
      || t.match(/^(?:does|do)\s+any\s+(?:rooms?|studios?|booths?)\s+(?:have|has|use|come with)\s+(.+)$/)
      || t.match(/^(?:is|are)\s+there\s+(?:an?\s+|any\s+)?(?:rooms?|studios?|booths?)\s+with\s+(.+)$/)
      || t.match(/^where\s+(?:is|are|can i (?:find|use))\s+(.+)$/)
      || t.match(/^(?:which|what)\s+(?:rooms?|studios?|booths?)\s+(?:is|are)\s+(.+)$/);
    if (m1 && !named.length) {
      const term = tidy(m1[1]);
      fc.term = term;
      if (!term || term.split(' ').length > 4 || /\d|\b(?:people|pax|persons?|space|seats?|capacity|most|best|biggest|smallest|more|less)\b/.test(term)) fc.why = 'no clear thing to look for';
      else if (FORMAT.test(term)) fc.why = 'a format (Rooms and Studios answers it)';
      else if (isType(term) || /\b(?:vocal|booths?|session|sessions)\b/.test(term)) fc.why = 'a session type or a booth (the AI answers it)';
      else {
        const re = termRe(term);
        const found = [];
        for (const r of rooms) { const h = hitsIn(r, re); if (h.length) found.push({ r, h }); }
        found.sort((a, b) => nat(a.r.name, b.r.name));
        if (!found.length) fc.why = 'no room lists it (the AI answers, from the details)';
        else {
          fc.shape = 'which rooms'; fc.go = true;
          const m = re.exec(found[0].h[0].text); const shown = m ? m[2] : term;
          fc.rooms = found.map(x => x.r.name);
          fc.text = '*Rooms with ' + se(shown) + ':*\n' + found.slice(0, 30).map(x => '• *' + se(x.r.name) + '* – ' + x.h.slice(0, 2).map(line).join(' · ')).join('\n');
        }
      }
    } else if (named.length === 1) {
      // shape 2: one room's setup
      const r = named[0], nm = r.name.toLowerCase().replace(/^studio\s+/, 'studio\\s*');
      const gear = /\b(?:equipment|gear|setup|set up|specs?|specifications|features|inside|interfaces?|preamps?|speakers?|monitors?|mics?|microphones?|console|workstation|computer|mac|laptop|capacity|fit|size|big|paired|pair|details?|tell me about|have|has|got|in it|whats inside|what is inside)\b/.test(t);
      if (!gear) fc.why = 'a room named, but not its setup';
      else {
        const m2 = t.match(new RegExp('^(?:does|do|is there|has)\\s+(?:the\\s+)?' + nm + '\\s+(?:have|has|got|come with|use)\\s+(.+)$'))
          || t.match(new RegExp('^(?:is|are)\\s+there\\s+(.+?)\\s+in\\s+(?:the\\s+)?' + nm + '$'))
          || t.match(new RegExp('^(?:the\\s+)?' + nm + '\\s+(?:has|have|got)\\s+(.+)$'));
        const term = m2 ? tidy(m2[1]) : '';
        const out = [];
        if (term && term.split(' ').length <= 4 && !/^(?:it|anything|what)$/.test(term)) {
          fc.term = term;
          const h = hitsIn(r, termRe(term), FORMAT.test(term) ? ['Formats'] : null);
          if (h.length) out.push('*' + se(r.name) + '* has ' + se(term) + ':\n' + h.slice(0, 4).map(x => '• ' + line(x)).join('\n'));
          else out.push('Airtable doesn’t list *' + se(term) + '* for *' + se(r.name) + '*.');
          out.push('');
        }
        out.push('*' + se(r.name) + '*');
        for (const [label, texts] of groupsOf(r.facts)) out.push('*' + se(label) + ':* ' + se(texts.join(label === 'Equipment' ? '. ' : ', ')));
        if (r.facts.length === 0) out.push('Airtable lists no details for this room yet.');
        fc.shape = 'one room'; fc.go = true; fc.rooms = [r.name];
        fc.text = out.join('\n');
      }
    } else fc.why = named.length > 1 ? 'more than one room named' : 'not a question about what rooms have';
  }
  if (fc.go) {
    fc.text = fc.text.slice(0, 2900);
    fc.blocks = [{ type: 'section', text: { type: 'mrkdwn', text: fc.text } }, { type: 'actions', elements: [
      { type: 'button', style: 'primary', action_id: 'open_book', value: 'menu', text: { type: 'plain_text', text: 'Book a room' } },
      { type: 'button', action_id: 'my_bookings', value: 'menu', text: { type: 'plain_text', text: 'My bookings' } } ] }];
  }
} catch (e) { fc.go = false; fc.why = 'error: ' + e.message; }
return [{ json: Object.assign(item, { factsCheck: fc }) }];
"""

# 1. Facts Check -> Facts? -> Send Facts, between Mine? (no) and Early Room Plan
mine_if = by["Mine?"]
x0, y0 = by["Mine Check"]["position"]
fc_node = {"parameters": {"jsCode": FACTS_CHECK}, "id": str(uuid.uuid4()), "name": "Facts Check",
           "type": "n8n-nodes-base.code", "typeVersion": by["Mine Check"]["typeVersion"], "position": [x0, y0 + 352]}
fq = copy.deepcopy(mine_if)
fq["id"] = str(uuid.uuid4()); fq["name"] = "Facts?"; fq["position"] = [x0 + 192, y0 + 352]
fq["parameters"]["conditions"]["conditions"][0]["id"] = str(uuid.uuid4())
fq["parameters"]["conditions"]["conditions"][0]["leftValue"] = "={{ ($json.factsCheck || {}).go === true }}"
sf = copy.deepcopy(by["Send Mine"])
sf["id"] = str(uuid.uuid4()); sf["name"] = "Send Facts"; sf["position"] = [x0 + 400, y0 + 352]
sf["parameters"]["jsonBody"] = "={{ JSON.stringify({ channel: $json.factsCheck.channel, text: $json.factsCheck.text, blocks: $json.factsCheck.blocks }) }}"
for n in (fc_node, fq, sf):
    sf.pop("webhookId", None)
    wf["nodes"].append(n)
assert [c["node"] for c in C["Mine?"]["main"][1]] == ["Early Room Plan"], C["Mine?"]["main"]
C["Mine?"]["main"][1] = [{"node": "Facts Check", "type": "main", "index": 0}]
C["Facts Check"] = {"main": [[{"node": "Facts?", "type": "main", "index": 0}]]}
C["Facts?"] = {"main": [[{"node": "Send Facts", "type": "main", "index": 0}], [{"node": "Early Room Plan", "type": "main", "index": 0}]]}
C["Send Facts"] = copy.deepcopy(C["Send Mine"])

# Turn Log Row: the new path
p = by["Turn Log Row"]["parameters"]
p["jsCode"] = sub(p["jsCode"], "  let mi = null; try { mi = $('Send Mine').first().json || null; } catch (e) {}   // v272\n",
    "  let mi = null; try { mi = $('Send Mine').first().json || null; } catch (e) {}   // v272\n"
    "  let fa = null; try { fa = $('Send Facts').first().json || null; } catch (e) {}   // v286\n")
p["jsCode"] = sub(p["jsCode"], ": mi ? 'my bookings' : ", ": mi ? 'my bookings' : fa ? 'room details' : ")

# 2. Room Table: every room's details, one line each, for the prompt
p = by["Room Table"]["parameters"]
js = p["jsCode"]
js = sub(js, "const preemptionRanks = {};\n",
    "// v286 (28 Oct): what each room has - the AI could not see Equipment, Workstation, Paired with or Capacity\n"
    + FACTS +
    "// only when the message is about rooms or what is in them - the rest of the prompt does not need ~1,500 tokens of gear\n"
    "let roomDetails = '';\n"
    "let gearAsk = false;\n"
    "try {\n"
    "  const tq = String(($('Slack Trigger').first().json || {}).text || '').toLowerCase();\n"
    "  gearAsk = /\\b(?:equipment|gear|setup|set up|specs?|features|interfaces?|preamps?|speakers?|monitors?|mics?|microphones?|console|workstation|computer|mac|laptop|capacity|how many people|fit|size|how big|paired|pair|dante|symphony)\\b/.test(tq)\n"
    "    || /\\b(?:rooms?|studios?|booths?)\\s+(?:with|that have|have|has)\\b|\\bdoes\\s+(?:studio\\s*\\w+|m[1-8]|likha|salin|katha|lobby)\\s+have\\b/.test(tq);\n"
    "} catch (e) { gearAsk = false; }\n"
    "try {\n"
    "  if (!gearAsk) throw new Error('not about rooms');\n"
    "  const dl = [];\n"
    "  for (const it of $('All Rooms').all()) {\n"
    "    const f = ((it && it.json) || {}).fields || {}; const nm = String(f['Room Name'] || '').trim(); if (!nm) continue;\n"
    "    const gs = groupsOf(factsOf(f)).map(([l, xs]) => l + ': ' + xs.join(l === 'Equipment' ? '. ' : ', '));\n"
    "    if (gs.length) dl.push('- ' + nm + ' - ' + gs.join('; '));\n"
    "  }\n"
    "  dl.sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));\n"
    "  roomDetails = dl.join('\\n');\n"
    "} catch (e) { roomDetails = ''; }\n"
    "if (!roomDetails) roomDetails = gearAsk ? '(room details unavailable this run - ask Rooms and Studios)' : '(not needed for this message)';\n\n"
    "const preemptionRanks = {};\n")
js = sub(js, "forNameNotice: forNameNotice, roomNames: roomNames }",
    "forNameNotice: forNameNotice, roomNames: roomNames, roomDetails: roomDetails }")
p["jsCode"] = js

# the prompt: the details, under the room names
o = by["Jessie AI Agent"]["parameters"]["options"]
o["systemMessage"] = sub(o["systemMessage"], "{{ $('Room Table').first().json.roomNames }}\n",
    "{{ $('Room Table').first().json.roomNames }}\n\n"
    "*What each room has* (Airtable Rooms & Studios: type, size, formats, workstation, pairing, equipment). Answer a question about a "
    "room's gear, setup, workstation, size or pairing from these lines only: name every room whose line mentions it, and if none "
    "does, say Airtable doesn't list it. Never add equipment that is not here.\n\n"
    "{{ $('Room Table').first().json.roomDetails }}\n")

# 3. Build Reply: drop only the booking-question sentences
p = by["Build Reply"]["parameters"]
p["jsCode"] = sub(p["jsCode"], "if (agent && BOOKING_ASK.test(text)) text = 'Use *Book a room* or *My bookings* below.';   // v275\n",
    "// v286 (28 Oct): drop only the sentences that ask for booking details - an answer before them stays (\"what rooms have\n"
    "// symphony?\" lost its whole answer to a closing \"Which room would you like?\"); the pointer only when nothing is left\n"
    "if (agent && BOOKING_ASK.test(text)) {\n"
    "  // kept: statements only - no question (\"Cancel it?\"), no leftover aside (\"(or none)\"), no \"Reply yes or no\"\n"
    "  const keep = s => !BOOKING_ASK.test(s) && !/\\?\\s*$/.test(s) && !/^\\(.*\\)$/.test(s.trim()) && !/\\b(?:yes or no|yes\\/no)\\b/i.test(s);\n"
    "  const kept = text.split('\\n').map(l => l.split(/(?<=[.!?])\\s+/).filter(keep).join(' ').trimEnd());\n"
    "  const left = kept.join('\\n').replace(/\\n{3,}/g, '\\n\\n').trim();\n"
    "  const collecting = /\\*?(?:project|client|engineer|arranger|session type|date|time|room|booked by|department):\\*?\\s/i.test(left) || /\\b(?:noted|so far|got it|i(?:’|')?ll book|i can book|let me book|i(?:’|')?ve (?:added|put|set|noted))\\b/i.test(left);\n"
    "  text = (left.match(/[a-z0-9]+/gi) || []).length >= 3 && !collecting ? left : 'Use *Book a room* or *My bookings* below.';   // v275\n"
    "}\n")

wf["name"] = "Project Jessie — v286 (room details)"
out = os.path.join(ROOT, "workflows", "project-jessie-v286.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
