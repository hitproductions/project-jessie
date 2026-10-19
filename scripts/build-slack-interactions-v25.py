#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v25.json - "Jessie — Slack Interactions", v25: round 8 (19 Oct, docs/design/round-8-plan.md).

  Forms
  10. Room: the recommended rooms, and right under them an "Another room" dropdown, always shown - one or the other: picking from
      the dropdown clears the ticked room, ticking a room clears the dropdown (each redraw gives the other control a new
      block_id, so Slack forgets its pick). No "Another room…" choice in the list. The list is an actions block (no "(optional)").
  21. Vocal booth: a dropdown whenever the studio takes one - set to the usual booth when the session needs one ("Studio B
      (usual)"), optional with "No booth" when the studio records in the room. Holding rooms: a multi-select dropdown. No tick boxes.
  22. Meetings and events: Another room also lists the free studios (never Studio M).
  18. Atmos Mixing (any type with "Atmos" in its name): "Project title or code" + Engineer + Note; Studio C only - taken ->
      "Studio C is taken then - pick another date or time."; title PROJECT / initials.
  23. Van Recording: Studio M only (same rule); Studio M never offered for anything else.
  19. Localization project code: a text box - any code, in capitals; Enter on a code in Localization Projects shows its title,
      client and people and sets the engineer. No search list (the Options Load URL is no longer used).
  20. M booth: "Who is it for?" - a text box, filled in with the booker's first name; title "M2 - <as typed>"; a name that is
      exactly one person in Bookers puts them on the booking and tells them.
  9, 13. Meetings and events: no "Booking this for someone else?"; titles start with a capital ("LIKHA - Post weekly meeting").
  14, 15. Every dropdown says "Select a/an …"; 4: text boxes blank (no "Write something" - an invisible placeholder).
  17. While booking, the message the form came from shows "Your booking details:" and the form's room · date · time, then
      ⏳ Booking… / ✅ Booked. A series the same (rooms · N dates · time); a change shows what the booking becomes.
  6. The Booking… window: the date and the time on two lines.
  Wording (items 2, 3, 5, 8): shorter hints, notes and problems - the table in the plan.
  Speed: the booking call carries the prepare run's client lookups (client_cache; Book Session v112 skips them).
Built on workflows/imported/slack-interactions-v24-imported.json (the live download). With Book Session v112 and main v275.
"""
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v24-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v25.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}

BLANK = "\\u2800"   # in JS source: an invisible placeholder (Slack shows "Write something" when there is none)


def js(node):
    return by[node]["parameters"]["jsCode"]


def setjs(node, code):
    by[node]["parameters"]["jsCode"] = code


def patch(node, pairs):
    code = js(node)
    for a, b in pairs:
        assert code.count(a) == 1, (node, a[:100], code.count(a))
        code = code.replace(a, b)
    setjs(node, code)


def everywhere(a, b, want=None):
    hit = 0
    for n in wf["nodes"]:
        code = n["parameters"].get("jsCode")
        if code and a in code:
            n["parameters"]["jsCode"] = code.replace(a, b)
            hit += 1
    assert want is None or hit == want, (a[:80], hit, want)
    return hit


def replace_fn(name, end_marker, new_text, want):
    hit = 0
    for n in wf["nodes"]:
        code = n["parameters"].get("jsCode") or ""
        i = code.find("function " + name + "(")
        if i == -1:
            continue
        j = code.find(end_marker, i)
        assert j != -1, (n["name"], name)
        n["parameters"]["jsCode"] = code[:i] + new_text + code[j:]
        hit += 1
    assert hit == want, (name, hit, want)


# ════ shared helpers ════════════════════════════════════════════════════════════════════════════════════════════════════
everywhere("if (/^(localization|qc)\\b/i.test(t)) return 'loc'; if (/^post processing$/i.test(t)) return 'post'; return 'studio'; }",
           "if (/atmos/i.test(t)) return 'atmos';   // v25: Atmos Mixing - project title or code + engineer, Studio C only\n"
           "  if (/^(localization|qc)\\b/i.test(t)) return 'loc'; if (/^post processing$/i.test(t)) return 'post'; return 'studio'; }\n"
           "// v25 (round 8): the booking types that use one room only - Atmos -> Studio C, Van Recording -> Studio M (the van)\n"
           "function onlyRoom(t) { t = String(t || '').trim(); return /atmos/i.test(t) ? 'Studio C' : /^van recording$/i.test(t) ? 'Studio M' : ''; }\n"
           "function cap1(x) { x = String(x || '').trim(); return x.charAt(0).toUpperCase() + x.slice(1); }   // v25: \"post weekly\" -> \"Post weekly\"",
           want=8)
# no "New project code" note - a code missing from Airtable may be an old one; nothing is shown, it is booked as typed
everywhere("  if (!proj) return code ? 'New project code - it is booked as typed.' : '';", "  if (!proj) return '';   // v25", want=8)

BOOTH_FN = r"""function boothBlocks(studio, BX) {   // v25: a dropdown, always shown - set to the usual booth when the session needs one
  if (!BX) return [];
  const pt = x => ({ type: 'plain_text', text: String(x).slice(0, 150) });
  const raw = BX.pair && BX.pair[studio], free = [].concat(BX.list || []);
  const pref = Array.isArray(raw) ? raw : (raw && raw.usual ? [raw.usual] : []);
  const list = raw && raw.list ? [].concat(raw.list) : pref.filter(b => free.indexOf(b) !== -1).concat(free.filter(b => pref.indexOf(b) === -1));
  const usual = pref[0] || '';
  const bid = 'booth~' + (Date.now() % 1000000);   // a new block each time: a new studio's booths, nothing kept from the last
  if (!list.length) return [{ type: 'context', block_id: bid, elements: [{ type: 'mrkdwn', text: '⚠️ No vocal booth is free then' + (BX.need ? ' - ' + studio + ' can still be booked on its own.' : '.') }] }];
  const opts = (BX.need ? [] : [{ text: pt('No booth'), value: 'none' }]).concat(list.slice(0, 99).map(n => ({ text: pt(n + (n === usual ? ' (usual)' : '')), value: n })));
  const el = Object.assign({ type: 'static_select', action_id: 'booth_pick', placeholder: pt('Select a booth'), options: opts }, BX.need ? { initial_option: opts[0] } : {});
  return [Object.assign({ type: 'input', block_id: bid, label: pt('Vocal booth'), element: el }, BX.need ? {} : { optional: true })];
}
"""
replace_fn("boothBlocks", "// v21: M booth - all day", BOOTH_FN, 3)

# Repeats: no "For every week…" hint; "Up to 16 dates."; Select … placeholders
everywhere("{ type: 'input', block_id: 'rep_days', optional: true, label: pt('On'), hint: pt('For every week. The first date’s day is ticked.'),",
           "{ type: 'input', block_id: 'rep_days', optional: true, label: pt('On'),", want=2)
everywhere("text: 'Up to 16 dates. Each one is checked before anything is booked.'", "text: 'Up to 16 dates.'", want=2)
everywhere("{ type: 'input', block_id: 'rep_freq', label: pt('How often'), element: { type: 'static_select', action_id: 'rep_freq_pick', options: freq,",
           "{ type: 'input', block_id: 'rep_freq', label: pt('How often'), element: { type: 'static_select', action_id: 'rep_freq_pick', placeholder: pt('Select how often'), options: freq,", want=2)
everywhere("action_id: 'rep_count_pick', placeholder: pt('Choose'),", "action_id: 'rep_count_pick', placeholder: pt('Select a number'),", want=2)
everywhere("const until = Object.assign({ type: 'datepicker', action_id: 'rep_until_pick' },",
           "const until = Object.assign({ type: 'datepicker', action_id: 'rep_until_pick', placeholder: pt('Select a date') },", want=2)

# ════ Step 1 ════════════════════════════════════════════════════════════════════════════════════════════════════════════
patch("Build Step 1", [
    ("text: '*Step 1 of 2* · when, and what for' }", "text: '*Step 1 of 2*' }"),
    ("hint: { type: 'plain_text', text: 'A room will be recommended to you based on your session details.' },",
     "hint: { type: 'plain_text', text: 'You’ll get a recommendation based on the booking details.' },"),
    ("action_id: 'purpose_pick', placeholder: { type: 'plain_text', text: 'Choose' }", "action_id: 'purpose_pick', placeholder: { type: 'plain_text', text: 'Select a booking type' }"),
    ("const timeEl = (id, o) => Object.assign({ type: 'static_select', action_id: id, placeholder: { type: 'plain_text', text: 'Choose a time' }, options: times }",
     "const timeEl = (id, o) => Object.assign({ type: 'static_select', action_id: id, placeholder: { type: 'plain_text', text: id === 'end_pick' ? 'Select an end time' : 'Select a start time' }, options: times }"),
    ("element: { type: 'datepicker', action_id: 'date_pick', initial_date:", "element: { type: 'datepicker', action_id: 'date_pick', placeholder: { type: 'plain_text', text: 'Select a date' }, initial_date:"),
])

# ════ Step 2 (Build Step 2) ═════════════════════════════════════════════════════════════════════════════════════════════
B2 = js("Build Step 2")
a = B2.index("let rooms = [], note = '';")
b = B2.index("const view = { type: 'modal', callback_id: 'book_step2'")
STEP2 = r"""let rooms = [], note = '';
const nu = [];   // v10: rooms offered that are not usual for this session (booked as asked)
const ONLY = onlyRoom(s.purpose);   // v25: Atmos -> Studio C, Van Recording -> Studio M; nothing else offered
const noM = n => ONLY === 'Studio M' || n !== 'Studio M';   // v25: Studio M (the van) is only for Van Recording
const rmLabel = s.kind === 'meeting' ? (/^event$/i.test(s.purpose) ? 'events' : 'meetings') : label;
if (ra.status !== 'OK') {
  note = '⚠️ Couldn’t check the calendar. Go *Back* and try again.';
} else if (s.kind === 'booth') {
  rooms = (ra.free_rooms || []).filter(r => /^M\d+$/i.test(r)).map(r => opt(r, r));
} else if (ONLY) {
  const free = [].concat(ra.free_priority || [], ra.free_last_resort || [], ra.free_rooms || []).indexOf(ONLY) !== -1;
  if (free) rooms = [opt(ONLY, ONLY, 'Recommended')]; else note = ONLY + ' is taken then - pick another date or time.';
} else {
  const pri = (ra.free_priority || []).filter(_main).filter(noM), last = (ra.free_last_resort || []).filter(_main).filter(noM);   // v21: studios only
  // v10: only the top room carries a note; the not-usual rooms are remembered in the form (nu), not read from the notes
  rooms = pri.map((r, i) => i === 0 ? opt(r, r, 'Recommended') : opt(r, r));
  if (!rooms.length) { rooms = last.map((r, i) => i === 0 ? opt(r, r, 'Not a usual room for ' + rmLabel) : opt(r, r)); nu.push(...last); }
  const st = (data.sessionTypes || []).find(r => String((r.fields || {}).Type || '').trim() === s.purpose);
  const nameOf = {}; for (const r of data.rooms || []) nameOf[r.id] = String((r.fields || {})['Room Name'] || '').trim();
  const usual = st ? [].concat((st.fields || {}).Priority || []).map(id => nameOf[id]).filter(Boolean) : [];
  const taken = usual.filter(r => _main(r) && noM(r) && pri.indexOf(r) === -1);
  if (taken.length && rooms.length) note = 'Not free then: ' + taken.join(', ');
}
// v19: which rooms are busy (on any date), and the rooms of this booking's kind
const busyAny = new Set(); for (const x of RAS) for (const bb of [].concat(x.busy || [])) busyAny.add(String(bb).replace(/\s*\(.*$/, '').trim());
const roomRow = n => ((data.rooms || []).find(r => String((r.fields || {})['Room Name'] || '').trim() === n) || {}).fields || null;
const kindOfRoom = n => { const f = roomRow(n); if (!f) return ''; const k = [].concat(f['Room Type'] || []).map(x => String(x).toLowerCase());
  if (/^M[1-8]$/.test(n)) return 'booth'; if (k.indexOf('conference room') !== -1 || k.indexOf('lobby') !== -1) return 'common'; return f['Vocal Booth'] === true ? 'vbooth' : 'studio'; };
const wantKind = s.kind === 'booth' ? 'booth' : s.kind === 'meeting' ? 'common' : 'studio';
// v25: meetings and events can also be in a studio; Studio M never, except for Van Recording
const sameKind = n => noM(n) && (s.kind === 'meeting' ? ['common', 'studio'].indexOf(kindOfRoom(n)) !== -1 : kindOfRoom(n) === wantKind);
// v9: the room the requester typed - chosen when it is free and fits; a free room that is not a usual one is offered as
// such (booked as asked); otherwise say it is taken, or that it is not a room for this.
const pre = (s.pre && typeof s.pre === 'object') ? s.pre : {};
let preRoom = null, preNote = '';
if (pre.r && ra.status === 'OK' && !ONLY) {
  const i = rooms.findIndex(o => o.value === pre.r);
  if (i !== -1) { preRoom = rooms[i]; if (i >= 10) { rooms.splice(i, 1); rooms.unshift(preRoom); } }
  else if (s.kind !== 'booth' && noM(pre.r) && [].concat(ra.free_last_resort || []).indexOf(pre.r) !== -1) {
    preRoom = opt(pre.r, pre.r, 'Not a usual room for ' + rmLabel); rooms.unshift(preRoom); nu.push(pre.r); }
  // v19 (Slack test: Studio 2 for Music Mixing said "taken" while free): a room on neither list is free when Room Availability
  // has it in no date's busy list - then it is offered as not a usual room, booked as asked
  else if (sameKind(pre.r) && !busyAny.has(pre.r)) { preRoom = opt(pre.r, pre.r, 'Not a usual room for ' + rmLabel); rooms.unshift(preRoom); nu.push(pre.r);
    if (SER) cnt[pre.r] = SER.dates.length; }
  else if (busyAny.has(pre.r)) preNote = pre.r + ' is taken then.';
  else preNote = pre.r + ' isn’t a room for ' + label + '.';
  if (preNote && rooms.length) preNote += ' These are free:';
}
rooms = rooms.slice(0, 10);
const others = ra.status === 'OK' && !ONLY ? (data.rooms || []).map(r => String((r.fields || {})['Room Name'] || '').trim())
  .filter(n => n && sameKind(n) && !busyAny.has(n) && !rooms.some(o => o.value === n)).sort((x, y) => x.localeCompare(y, 'en', { numeric: true })).slice(0, 30) : [];
// v21: booths and holding rooms on top of the studio (free on every date of a series)
const _req = String(((ST || {}).fields || {})['Room Requirements'] || '');
const needBooth = s.kind === 'loc' && /vocal booth/i.test(_req);
const offerBooth = s.kind === 'studio' && /recording/i.test(String(s.purpose || '')) && !needBooth && !ONLY;
const offerHold = s.kind === 'studio' && /holding|conference/i.test(_req);
const _nm = r => String((r.fields || {})['Room Name'] || '').trim();
const _num = (x, y) => x.localeCompare(y, 'en', { numeric: true });
const vbooths = (data.rooms || []).filter(r => (r.fields || {})['Vocal Booth'] === true).map(_nm).filter(n => n && !busyAny.has(n)).sort(_num);
const allVB = (data.rooms || []).filter(r => (r.fields || {})['Vocal Booth'] === true).map(_nm).filter(Boolean);
// "Paired with": "Studio A, B, or D, Can change using Dante" -> Studio A, Studio B, Studio D; a booth that names the studio comes first
const pairedOf = n => String((_row(n) || {})['Paired with'] || '').split(/can change/i)[0].replace(/\bStudio\s+/gi, '')
  .split(/,|\bor\b/i).map(x => x.trim()).filter(x => /^[A-Z0-9]$/i.test(x)).map(x => 'Studio ' + x.toUpperCase());
// v25: a studio's booths in preference order (the usual one first) - kept short in the form; boothBlocks puts the free ones first
const boothPref = studio => { const back = allVB.filter(b => new RegExp('\\b' + studio.replace(/\s+/g, '\\s+') + '\\b', 'i').test(String((_row(b) || {})['Paired with'] || '')));
  return back.concat(pairedOf(studio).filter(b => allVB.indexOf(b) !== -1 && back.indexOf(b) === -1)); };
const BX = (needBooth || offerBooth) && ra.status === 'OK' ? { need: needBooth, list: vbooths, pair: {} } : null;
if (BX) for (const n of rooms.map(o => o.value).concat(others)) { const pr = boothPref(n); if (pr.length) BX.pair[n] = pr; }   // v25: Another room's studios too
const holds = offerHold && ra.status === 'OK' ? (data.rooms || []).filter(r => [].concat((r.fields || {})['Room Type'] || []).map(x => String(x).toLowerCase()).indexOf('conference room') !== -1)
  .map(_nm).filter(n => n && !busyAny.has(n)).sort(_num) : [];
// v13: a series - each room says on how many of the dates it is free
if (SER) { const N = SER.dates.length;
  rooms = rooms.map(o => { const k = cnt[o.value] || 0, tail = k >= N ? 'free on all ' + N + ' dates' : 'free on ' + k + ' of ' + N + ' dates';
    const d = o.description ? o.description.text + ' · ' + tail : (k >= N ? '' : tail);
    return d ? Object.assign({}, o, { description: { type: 'plain_text', text: d.slice(0, 75) } }) : o; });
  if (preRoom) preRoom = rooms.find(o => o.value === preRoom.value) || preRoom; }
const _DS2 = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
const serShort = d => { const x = new Date(d + 'T12:00:00Z'); return _DS2[x.getUTCDay()] + ' ' + MON[x.getUTCMonth()] + ' ' + x.getUTCDate(); };
const blocks = [ctx('*Step 2 of 2*'), { type: 'section', text: md(SER
  ? '🗓️ *' + SER.dates.length + ' dates · ' + fmtT(s.t0) + '–' + fmtT(s.t1) + ' · ' + label + '*'
  : '🗓️ *' + when + ' · ' + label + '*') }];
if (SER) blocks.push(ctx(SER.dates.map(serShort).join(' · ')));
const BLANK = { type: 'plain_text', text: '__BLANK__' };   // v25: an empty-looking box (Slack shows "Write something" when there is no placeholder)
if (!rooms.length) {
  if (preNote) blocks.push({ type: 'section', text: md('⚠️ ' + preNote) });
  blocks.push({ type: 'section', text: md(note || ('Nothing that does ' + label + ' is free then. Go *Back* and try another time.')) });
} else {
  if (preNote) blocks.push({ type: 'section', text: md('⚠️ ' + preNote) });
  // v25: the recommended rooms (an actions block - no "(optional)"), then "Another room" right under them; one or the other
  // (route 8 clears the one not picked)
  const ini = rooms.find(o => o.value === (preRoom || rooms[0]).value) || rooms[0];
  blocks.push({ type: 'section', block_id: 'room_label', text: md('*' + (needBooth ? 'Studio' : 'Room') + '*') },
    { type: 'actions', block_id: 'room', elements: [{ type: 'radio_buttons', action_id: 'room_radio', options: rooms, initial_option: ini }] });
  if (note) blocks.push(ctx(note));
  if (others.length) blocks.push({ type: 'input', block_id: 'room_other', optional: true, dispatch_action: true, label: { type: 'plain_text', text: 'Another room' },
    hint: { type: 'plain_text', text: ('Not a usual room for ' + rmLabel + '.').slice(0, 150) },
    element: { type: 'static_select', action_id: 'room_other_pick', placeholder: { type: 'plain_text', text: 'Select a room' }, options: others.map(n => opt(n, n)) } });
  // v25: the booth and the holding rooms as dropdowns, always shown when they apply (no tick boxes)
  if (BX) blocks.push(...boothBlocks(ini.value, BX));
  if (offerHold) blocks.push(holds.length ? { type: 'input', block_id: 'holding', optional: true, label: { type: 'plain_text', text: 'Holding rooms' },
      element: { type: 'multi_static_select', action_id: 'holding_pick', placeholder: { type: 'plain_text', text: 'Select holding rooms' }, options: holds.slice(0, 100).map(n => opt(n, n)) } }
    : { type: 'context', block_id: 'holding', elements: [md('⚠️ No holding room is free then.')] });
  blocks.push({ type: 'divider' });
  // v24: the details each kind of booking needs, all shown at once; engineer / arranger from the session type's roles (Airtable)
  const people = (data.bookers || []).map(b => { const f = b.fields || {};
    return { name: String(f.Name || '').trim(), info: String(f.Info || ''), dept: [].concat(f.Department || []).map(x => String((x && x.name) || x)),
             slack: String(f['Slack User ID'] || '').split(/[\s,]+/).filter(Boolean)[0] || '' }; }).filter(p => p.name && p.slack);
  const popt = p => ({ text: { type: 'plain_text', text: p.name }, value: p.slack });
  const iv = (el, v) => { v = String(v || '').trim().slice(0, 150); if (v) el.initial_value = v; return el; };   // v9: typed values
  const txtIn = (aid, v, o) => iv(Object.assign({ type: 'plain_text_input', action_id: aid, placeholder: BLANK }, o || {}), v);
  const notes = input('notes', 'Note', txtIn('notes_in', '', { multiline: true }), { optional: true });   // v24: shown, no tick box
  const RR = typeRoles(data, s.purpose);
  const engs = people.filter(p => /\bengineer\b/i.test(p.info)).sort((a, b) => a.name.localeCompare(b.name));
  const arrs = people.filter(p => /\barranger\b/i.test(p.info)).sort((a, b) => a.name.localeCompare(b.name));
  const me = engs.find(p => p.slack === s.requester), meArr = arrs.find(p => p.slack === s.requester);
  // Localization: the project's people for this session type first and preset (QC: anyone, nothing preset)
  const LOC = locRows($('Loc Projects 2').all());
  const proj = s.kind === 'loc' && pre.cd ? locFind(LOC, pre.cd) : null;
  const locFirst = s.kind === 'loc' ? locIds(proj, s.purpose, data) : [];
  const engOrder = locFirst.map(id => engs.find(p => p.slack === id)).filter(Boolean).concat(engs.filter(p => locFirst.indexOf(p.slack) === -1));
  const NONE_E = { text: { type: 'plain_text', text: 'No engineer' }, value: 'none' }, NONE_A = { text: { type: 'plain_text', text: 'No arranger' }, value: 'none' };   // a picked dropdown cannot be emptied
  const engEl = { type: 'static_select', action_id: 'engineer_pick', placeholder: { type: 'plain_text', text: 'Select an engineer' }, options: (RR.either ? [NONE_E] : []).concat(engOrder.slice(0, RR.either ? 99 : 100).map(popt)) };
  const fromProj = engs.find(p => p.slack === locFirst[0]) || null, typed = engs.find(p => p.slack === pre.en) || null;
  const engDefault = typed || fromProj || ((RR.either && meArr && !me) ? null : me) || null;
  if (engDefault) engEl.initial_option = popt(engDefault);
  const arrEl = { type: 'static_select', action_id: 'arranger_pick', placeholder: { type: 'plain_text', text: 'Select an arranger' }, options: [NONE_A].concat(arrs.slice(0, 99).map(popt)) };
  const arrDefault = arrs.find(p => p.slack === pre.ar) || (meArr && !me ? meArr : null);
  if (arrDefault) arrEl.initial_option = popt(arrDefault);
  const engineer = input('engineer', 'Engineer', engEl, RR.either ? { optional: true } : {});   // v25: no hint
  const arranger = arrs.length ? input('arranger', 'Arranger', arrEl, { optional: true }) : null;
  const team = [].concat(RR.either ? [{ type: 'context', block_id: 'team_note', elements: [md('Engineer and arranger: pick one or both.')] }] : [])
    .concat(RR.eng || !RR.known ? [engineer] : []).concat(RR.arr && arranger ? [arranger] : []);
  // v25: a meeting's department, set to the booker's (no hint); no "Booking this for someone else?" on meetings or events
  const dOpts = [...new Set(people.reduce((acc, p) => acc.concat(p.dept), []))].filter(Boolean).sort().slice(0, 100).map(x => ({ text: { type: 'plain_text', text: x }, value: x }));
  const mine = people.find(p => p.slack === s.requester) || {};
  const myDept = (mine.dept || [])[0];
  const dIni = dOpts.find(o => o.value === myDept);
  if (s.kind === 'meeting') {
    blocks.push(input('title', s.purpose === 'Event' ? 'Event title' : 'Meeting title', txtIn('title_in', '')));
    if (s.purpose !== 'Event' && dOpts.length) blocks.push(input('department', 'Department', Object.assign({ type: 'static_select', action_id: 'department_pick',
      placeholder: { type: 'plain_text', text: 'Select a department' }, options: dOpts }, dIni ? { initial_option: dIni } : {})));
    blocks.push(notes);
  } else if (s.kind === 'booth') {   // v25: who it is for, typed - their name is the title ("M2 - Joaquin"); the booker's first name to start
    blocks.push(input('forname', 'Who is it for?', txtIn('forname_in', String(mine.name || '').split(/\s+/)[0])), notes);
  } else if (s.kind === 'post') {   // v21: Post Processing - the booker is set, a project title, no client
    blocks.push({ type: 'section', block_id: 'booker', text: md('*Booker*\n' + POST_BOOKER) },
      input('project', 'Project title', txtIn('project_in', pre.pj)), notes);
  } else if (s.kind === 'loc') {   // v25: the code typed (any code); Enter on one in Localization Projects shows it and sets the engineer
    const cd = String(pre.cd || '').trim().toUpperCase();
    blocks.push(input('code', 'Project code', txtIn('code_in', cd, { dispatch_action_config: { trigger_actions_on: ['on_enter_pressed'] } }), { dispatch_action: true }));
    if (proj) blocks.push({ type: 'context', block_id: 'code_info', elements: [md(locInfo(proj, cd))] });
    blocks.push(engineer, notes);
  } else if (s.kind === 'atmos') {   // v25: Atmos Mixing - a project title or code, the engineer
    blocks.push(input('project', 'Project title or code', txtIn('project_in', pre.pj || pre.cd)), engineer, notes);
  } else {
    blocks.push(input('project', 'Project title', txtIn('project_in', pre.pj)),
      input('client', 'Client', txtIn('client_in', pre.c), { optional: true }), ...team, notes);
  }
}
""".replace("__BLANK__", BLANK)
B2 = B2[:a] + STEP2 + B2[b:]
B2 = B2.replace("""const view = { type: 'modal', callback_id: 'book_step2', title: { type: 'plain_text', text: 'Book a room' },
  close: { type: 'plain_text', text: 'Back' }, private_metadata: JSON.stringify(Object.assign({}, s, { when, label }, nu.length ? { nu } : {}, others.length ? { others } : {},
    BX ? { bx: BX } : {}, offerHold ? { holds } : {})), blocks };   // v21""",
                """const view = { type: 'modal', callback_id: 'book_step2', title: { type: 'plain_text', text: 'Book a room' },
  close: { type: 'plain_text', text: 'Back' }, private_metadata: JSON.stringify(Object.assign({}, s, { when, label }, nu.length ? { nu } : {}, others.length ? { others } : {},
    BX ? { bx: BX } : {})), blocks };   // v21; v25: holding rooms drawn at once (no list kept)""")
assert "v25: holding rooms drawn at once" in B2
setjs("Build Step 2", B2)

# ════ Read Step 2 ═══════════════════════════════════════════════════════════════════════════════════════════════════════
patch("Read Step 2", [
    ("""const room0 = val('room_other', 'room_other_pick') || val('room', 'room_radio');   // v19: "Use another room" wins""",
     """// v25: a control by its action_id - route 8 gives a block a new block_id when it clears it ("room~123", "booth~456")
const valA = a => { for (const k of Object.keys(v)) { const x = (v[k] || {})[a]; const y = x && (x.value || (x.selected_option && x.selected_option.value)); if (y) return y; } return ''; };
const room0 = valA('room_other_pick') || valA('room_radio');   // v25: one or the other"""),
    ("const booth = val('booth', 'booth_pick');", "const booth = (b0 => b0 === 'none' ? '' : b0)(valA('booth_pick'));   // v25: a dropdown, \"No booth\""),
    ("const forId = val('forwho', 'forwho_pick');   // v24: a meeting / event / M booth booked for someone else",
     "let forId = val('forwho', 'forwho_pick');   // v24 (an older form still open); v25: the M booth's typed name below\n"
     "const forName = cap1(val('forname', 'forname_in'));   // v25: M booth - who it is for, as typed"),
    ("if (!room) errors.room = 'Pick a room.';",
     "{ const ib = ['room_other', 'project', 'title', 'code', 'forname', 'notes'].find(k => ((p.view && p.view.blocks) || []).some(bl => bl.type === 'input' && bl.block_id === k));   // v25: the list is not an input\n"
     "  if (!room) errors[ib || 'room'] = ib === 'room_other' ? 'Pick a room.' : 'Pick a room above.'; }"),
    ("if ((s.kind === 'studio' || s.kind === 'post') && !project) errors.project = 'What is the project called?';",
     "if ((s.kind === 'studio' || s.kind === 'post' || s.kind === 'atmos') && !project) errors.project = 'What is the project called?';\n"
     "if (s.kind === 'booth' && !forName) errors.forname = 'Who is it for?';   // v25"),
    ("const first = id => nm(id).split(/\\s+/)[0] || '';",
     "const first = id => nm(id).split(/\\s+/)[0] || '';\n"
     "// v25: an M booth's typed name that is exactly one person in Bookers (name, first name, \"Goes by\") puts them on it and tells them\n"
     "if (s.kind === 'booth' && forName) { const q = forName.toLowerCase();\n"
     "  const hits = (data.bookers || []).map(x => x.fields || {}).filter(f => { const full = String(f.Name || '').trim().toLowerCase(), fst = full.split(/\\s+/)[0];\n"
     "    const al = ((String(f.Info || '').match(/goes by\\s+([^\\n]*)/i) || [])[1] || '').split(/,|\\band\\b/).map(x => x.trim().replace(/\\.$/, '').toLowerCase()).filter(Boolean);\n"
     "    return q === full || q === fst || al.indexOf(q) !== -1; });\n"
     "  const id = hits.length === 1 ? String(hits[0]['Slack User ID'] || '').split(/[\\s,]+/).filter(Boolean)[0] || '' : '';\n"
     "  forId = id && id !== s.requester ? id : ''; }"),
    ("  if (s.kind === 'studio' || s.kind === 'loc') {\n    if (RR.either)",
     "  if (s.kind === 'studio' || s.kind === 'loc' || s.kind === 'atmos') {   // v25: + Atmos\n    if (RR.either)"),
    ("if (s.kind === 'meeting') calTitle = room.toUpperCase() + ' - ' + title;\nelse if (s.kind === 'booth') calTitle = room.toUpperCase() + ' - ' + first(forId || s.requester);   // v24: the person it is for",
     "if (s.kind === 'meeting') calTitle = room.toUpperCase() + ' - ' + cap1(title);   // v25: a capital first letter\n"
     "else if (s.kind === 'booth') calTitle = room.toUpperCase() + ' - ' + (forName || first(s.requester));   // v25: the name typed\n"
     "else if (s.kind === 'atmos') calTitle = [project.toUpperCase(), ini(engineerId)].filter(Boolean).join(' / ');   // v25: PROJECT / initials"),
    ("  (s.kind === 'studio') ? (client ? 'client ' + client : 'no client') : s.kind === 'post' ? 'no client' : '',",
     "  (s.kind === 'studio') ? (client ? 'client ' + client : 'no client') : (s.kind === 'post' || s.kind === 'atmos') ? 'no client' : '',"),
    ("  /music|band/i.test(s.purpose || '') ? (arrangerId ? 'arranger ' + nm(arrangerId) : (arrPick === 'none' ? 'no arranger' : '')) : '',",
     "  // v25: an arranger field left empty is \"no arranger\" - Book Session never asks\n"
     "  (s.kind === 'studio' && (typeRoles(data, s.purpose).arr || /music|band/i.test(s.purpose || ''))) ? (arrangerId ? 'arranger ' + nm(arrangerId) : 'no arranger') : '',"),
    ("    : [{ type: 'section', text: { type: 'mrkdwn', text: '⏳ *Booking ' + roomsAll.join(' + ') + '…*\\n' + s.when } },\n"
     "       { type: 'context', elements: [{ type: 'mrkdwn', text: 'Your booking is being processed. You may close this window – we’ll notify you once it’s done.' }] }] };",
     "    : [{ type: 'section', text: { type: 'mrkdwn', text: '⏳ *Booking ' + roomsAll.join(' + ') + '…*\\n' + (function () {   // v25: the date, then the time\n"
     "         const DL = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'], ML = ['January','February','March','April','May','June','July','August','September','October','November','December'];\n"
     "         const t = hm => { let [h, m] = String(hm).split(':').map(Number); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(m).padStart(2, '0') + ' ' + ap; };\n"
     "         const x = new Date(s.date + 'T12:00:00Z');\n"
     "         return DL[x.getUTCDay()] + ', ' + ML[x.getUTCMonth()] + ' ' + x.getUTCDate() + '\\n' + (s.allDay ? 'All day' : t(s.t0) + ' – ' + t(s.t1)); })() } },\n"
     "       { type: 'context', elements: [{ type: 'mrkdwn', text: 'You can close this window – we’ll let you know once it’s done.' }] }] };"),
    ("return [{ json: { valid, calTitle, room, rooms: roomsAll.join(', '), s, prep, team, engineerId, arrangerId, forId,",
     "return [{ json: { valid, calTitle, room, rooms: roomsAll.join(', '), s, prep, team, engineerId, arrangerId, forId, forName,"),
])

# ════ After Prepare / After Book / After Prepare Series: problems in fewer words ═════════════════════════════════════════
for a, b in [
    ("    if (!typed || !sug.length) return { warn: (typed ? '\"' + typed + '\"' : 'That client') + ' isn’t in the client list. Check the spelling, or press *Book* again to keep it as a new client.',",
     "    if (!typed || !sug.length) return { warn: (typed ? '\"' + typed + '\" is a new client' : 'That client is new') + '. Press *Book* again to keep it.',   // v25"),
    ("    return { warn: '\"' + typed + '\" isn’t in the client list. Did you mean *' + sug.join('* or *') + '*? Change the client, or press *Book* again to keep \"' + typed + '\" as a new client.',",
     "    return { warn: 'Did you mean *' + sug.join('* or *') + '*? Or press *Book* again to keep \"' + typed + '\" as a new client.',   // v25"),
    ("    return { warn: 'Which department is this session for?',", "    return { warn: 'Which department is this booking for?',"),
    ("  if (reason === 'NEED_ARRANGER') return { warn: 'Who’s the arranger? Pick one, or *No arranger*.' };",
     "  if (reason === 'NEED_ARRANGER') return { warn: 'Pick an arranger.' };   // v25: the form says \"no arranger\" for an empty field, so not asked"),
    ("  if (reason === 'ROOM_OCCUPIED') return { warn: 'That room was just booked by someone else for that time. Pick another room, or go *Back* to change the time.' };",
     "  if (reason === 'ROOM_OCCUPIED') return { warn: 'That room was just taken. Pick another room, or go *Back*.' };"),
    ("  if (reason === 'ROOM_DECLINED' || r.status === 'ROOM_DECLINED') return { warn: 'The room turned the booking down - its own calendar shows it is taken then' + (r.removed === false ? '' : ', so it was taken off the calendar') + '. Pick another room, or go *Back* to change the time.' };",
     "  if (reason === 'ROOM_DECLINED' || r.status === 'ROOM_DECLINED') { const rm = [].concat(r.declined || []).map(x => (String(x).match(/(Studio [0-9A-Z]|M[1-8]|Salin|Katha|Likha|Lobby)\\b/) || [])[1] || '').filter(Boolean).join(' and ');\n"
     "    return { warn: '*' + (rm || 'The room') + '* is already taken then - nothing was booked.' + (r.removed === false ? ' Delete the event from the calendar.' : '') }; }   // v25"),
    ("  if (reason === 'ROOM_UNSUITABLE' || reason === 'ROOM_NOT_PRIORITY' || reason === 'NO_ROOM' || reason === 'UNKNOWN_ROOM') return { warn: 'That room can’t be booked for this session. Pick another room.' };",
     "  if (/can only be booked in Studio [A-Z0-9]|Studio M is only for Van Recording/.test(human)) return { warn: human.replace(/\\s*Nothing was booked\\.\\s*$/, '') };   // v25: single-room types\n"
     "  if (reason === 'ROOM_UNSUITABLE' || reason === 'ROOM_NOT_PRIORITY' || reason === 'NO_ROOM' || reason === 'UNKNOWN_ROOM') return { warn: 'That room can’t be booked for this. Pick another room.' };"),
    ("  if (reason === 'NO_REFERENCE_DATA' || reason === 'UNVERIFIABLE' || reason === 'LOOKUP_FAILED' || reason === 'CALENDAR_ERROR') return { warn: 'The room list or the calendar couldn’t be read just now. Press *Book* again in a moment.' };   // v15",
     "  if (reason === 'NO_REFERENCE_DATA' || reason === 'UNVERIFIABLE' || reason === 'LOOKUP_FAILED' || reason === 'CALENDAR_ERROR') return { warn: 'Couldn’t check the calendar. Press *Book* again in a moment.' };   // v15; v25"),
    ("  return { warn: 'This couldn’t be booked. Check the details and press *Book* again, or go *Back*.' };   // v15: no code shown",
     "  return { warn: 'Couldn’t book this. Check the details and press *Book* again.' };   // v15: no code shown; v25"),
]:
    everywhere(a, b, want=3)

# the booking call carries the prepare run's client lookups (Book Session v112: Client Cache)
patch("After Prepare", [("  description: [engDesc, R.descTail].filter(Boolean).join(' | ')\n});",
                         "  description: [engDesc, R.descTail].filter(Boolean).join(' | '),\n"
                         "  client_cache: String(r.client_cache || '')   // v25: Book Session v112 skips the client lookups it just made\n});")])
patch("After Prepare Series", [("  time: R.s.t0 + '-' + R.s.t1 };", "  time: R.s.t0 + '-' + R.s.t1, rooms: R.rooms || '' };   // v25: rooms, for the message's details line")])

# ════ the message the form came from: "Your booking details:" + the form's details ══════════════════════════════════════
SRC_FNS = r"""function srcMark(blocks, line, head) { return (head ? [head] : (blocks || []).filter(b => b.type !== 'actions' && b.type !== 'context'))
  .concat([{ type: 'context', block_id: 'src_status', elements: [{ type: 'mrkdwn', text: line }] }]); }   // v25: head = the form's details
function srcIsOffer(blocks) { return (blocks || []).some(b => (b.elements || []).some(e => e.action_id === 'open_book' && /^\{/.test(String(e.value || '')))); }
function srcFrom(h, msg, line, head) {
  const m = ((h && h.messages) || []).find(x => msg && String(x.ts) === String(msg.ts));
  if (!m) return { ok: false };
  return { ok: true, channel: msg.ch, ts: msg.ts, blocks: srcMark(m.blocks, line, head), text: m.text || 'Booking', original: m.blocks || [], offer: srcIsOffer(m.blocks), head: head || null };
}
function srcDone(M, ok, line) {
  if (!M || !M.ok) return [];
  const blocks = ok && M.offer ? srcMark(M.original, line, M.head) : M.original;
  return [{ json: { channel: M.channel, ts: M.ts, blocks, text: M.text } }];
}
function srcHead(rooms, when) {   // v25: "Your booking details:" and the form's room · date · time
  const r = String(rooms || '').split(',').map(x => x.trim()).filter(Boolean).join(' + ');
  return { type: 'section', block_id: 'src_head', text: { type: 'mrkdwn', text: 'Your booking details:\n🗓️ *' + [r, when].filter(Boolean).join(' · ') + '*' } };
}
function srcT(hm) { let [h, m] = String(hm || '').split(':').map(Number); if (isNaN(h)) return ''; const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(m || 0).padStart(2, '0') + ' ' + ap; }
function srcDay(d) { const x = new Date(d + 'T12:00:00Z'); if (isNaN(x)) return '';
  return ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'][x.getUTCDay()] + ', ' + ['January','February','March','April','May','June','July','August','September','October','November','December'][x.getUTCMonth()] + ' ' + x.getUTCDate(); }

"""
replace_fn("srcMark", "\n// ", SRC_FNS, 4)
patch("Mark Source", [("""// Mark Source (v19): Book was pressed - the message it started from shows "⏳ Your booking is being processed…".
const R = $('Read Step 2').first().json;
return [{ json: srcFrom($input.first().json, (R.s || {}).msg, '⏳ Your booking is being processed…') }];""",
                       """// Mark Source (v19): Book was pressed - the message it started from shows the form's details and "⏳ Booking…" (v25).
const R = $('Read Step 2').first().json;
const S = R.s || {};
const head = srcHead(R.rooms, srcDay(S.date) + ' · ' + (S.allDay ? 'All day' : srcT(S.t0) + ' – ' + srcT(S.t1)));
return [{ json: srcFrom($input.first().json, S.msg, '⏳ Booking…', head) }];""")])
patch("Mark Source Series", [("""const R = $('Read Series Confirm').first().json;
return [{ json: srcFrom($input.first().json, (R.meta || {}).msg, '⏳ Your series is being processed…') }];""",
                              """const R = $('Read Series Confirm').first().json;
const M = R.meta || {}, tm = String(M.time || '').split('-');   // v25: rooms · N dates · time
const head = srcHead(M.rooms, [M.n ? M.n + ' dates' : '', tm.length === 2 ? srcT(tm[0]) + ' – ' + srcT(tm[1]) : ''].filter(Boolean).join(' · '));
return [{ json: srcFrom($input.first().json, M.msg, '⏳ Booking…', head) }];""")])
patch("Read Series Confirm", [("text: 'Processing your series of bookings. This may take a while. You may close this window – we’ll notify you once it’s done.'",
                               "text: 'Multiple bookings may take longer to process. You can close this window – we’ll let you know once it’s done.'")])
patch("Mark Cancelling", [("'Your cancellation is being processed…'", "'Cancelling…'")])
patch("Mark Changing", [("""const blocks = m ? processing(m.blocks, R.b.id, 'Your change is being processed…') : null;""",
                         """const blocks = m ? processing(m.blocks, R.b.id, 'Changing…') : null;
// v25: the row shows what the booking becomes while it changes
if (blocks) { const row = blocks.find(x => x.block_id === 'bk_' + R.b.id), n = R.n || {};
  const DS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'], MS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const t = hm => { let [h, mm] = String(hm).split(':').map(Number); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(mm).padStart(2, '0') + ' ' + ap; };
  const x = new Date(String(n.d) + 'T12:00:00Z');
  if (row && row.text && !isNaN(x)) row.text.text = '*' + (R.newTitle || R.b.t) + '*\\n' + DS[x.getUTCDay()] + ', ' + MS[x.getUTCMonth()] + ' ' + x.getUTCDate() + ' · '
    + (n.s && !(n.s === '00:00' && n.e === '00:00') ? t(n.s) + ' – ' + t(n.e) : 'all day')
    + (R.newRooms ? ' · ' + String(R.newRooms).split(',').map(y => y.trim()).filter(Boolean).join(' + ') : ''); }""")])

# ════ Cancel / Change problems in fewer words ═══════════════════════════════════════════════════════════════════════════
patch("After Cancel", [("NOT_YOURS: 'You can’t cancel this booking - only the person who booked it, or its engineer or arranger, can.',",
                        "NOT_YOURS: 'Only the booker, engineer or arranger can cancel this.',")])
patch("After Move", [("{ NOT_YOURS: 'You can’t change this booking - only the person who booked it, or its engineer or arranger, can.',",
                      "{ NOT_YOURS: 'Only the booker, engineer or arranger can change this.',")])
patch("To Move", [("""    const warn = near.length ? '"' + t + '" isn’t in the client list. Did you mean *' + near.join('* or *') + '*? Change the client, or press *Change* again to keep "' + t + '" as a new client.'
      : '"' + t + '" isn’t in the client list. Check the spelling, or press *Change* again to keep it as a new client.';""",
                   """    const warn = near.length ? 'Did you mean *' + near.join('* or *') + '*? Or press *Change* again to keep "' + t + '" as a new client.'
      : '"' + t + '" is a new client. Press *Change* again to keep it.';   // v25""")])

# ════ the Change form ═══════════════════════════════════════════════════════════════════════════════════════════════════
# "What's it for?": Select a booking type, no hint
everywhere("""    if (tOpts.length) blocks.push({ type: 'input', block_id: 'purpose_c', dispatch_action: true, optional: !tIni, label: pt("What's it for?"),
      element: Object.assign({ type: 'static_select', action_id: 'purpose_c', placeholder: pt('Choose'), options: tOpts }, tIni ? { initial_option: tIni } : {}),
      hint: pt(tIni ? 'Change it and the details below follow.' : 'Leave it empty to keep the session as it is.') }); }""",
           """    if (tOpts.length) blocks.push({ type: 'input', block_id: 'purpose_c', dispatch_action: true, optional: !tIni, label: pt("What's it for?"),
      element: Object.assign({ type: 'static_select', action_id: 'purpose_c', placeholder: pt('Select a booking type'), options: tOpts }, tIni ? { initial_option: tIni } : {}) }); }   // v25: no hint""",
           want=5)
everywhere("""  blocks.push({ type: 'input', block_id: 'date', label: pt('Date'), element: Object.assign({ type: 'datepicker', action_id: 'date_pick' },""",
           """  blocks.push({ type: 'input', block_id: 'date', label: pt('Date'), element: Object.assign({ type: 'datepicker', action_id: 'date_pick', placeholder: pt('Select a date') },""", want=5)
everywhere("""action_id: 'start_pick', placeholder: pt('Choose a time'), options: times }""", """action_id: 'start_pick', placeholder: pt('Select a start time'), options: times }""", want=5)
everywhere("""action_id: 'end_pick', placeholder: pt('Choose a time'), options: times }""", """action_id: 'end_pick', placeholder: pt('Select an end time'), options: times }""", want=5)
# the rooms: meetings and events can move to a studio; Studio M only for Van Recording; Atmos only Studio C
everywhere("""  const same = known ? rooms.all.filter(n => kind(n) === kind(br)).sort((x, y) => x.localeCompare(y, 'en', { numeric: true })) : [];""",
           """  // v25: a meeting / event can move to a studio; Studio M only for Van Recording; Atmos only in Studio C
  const T0 = String((det && det.vals && det.vals.st) || b.st || ''), only = onlyRoom(T0);
  const same = (known ? rooms.all.filter(n => kind(n) === kind(br) || (kind(br) === 'common' && kind(n) === 'studio')).sort((x, y) => x.localeCompare(y, 'en', { numeric: true })) : [])
    .filter(n => only ? n === only : n !== 'Studio M');""", want=5)
everywhere("""      blocks.push({ type: 'input', block_id: 'booth_c', label: pt('Booth'), element: { type: 'static_select', action_id: 'booth_c_pick', options: bo.slice(0, 100),""",
           """      blocks.push({ type: 'input', block_id: 'booth_c', label: pt('Vocal booth'), element: { type: 'static_select', action_id: 'booth_c_pick', placeholder: pt('Select a booth'), options: bo.slice(0, 100),""", want=5)
everywhere("""      blocks.push({ type: 'input', block_id: 'holding_c', optional: true, label: pt('Holding rooms'), element: Object.assign({ type: 'checkboxes', action_id: 'holding_c_pick', options: ho }, hi.length ? { initial_options: hi } : {}) }); }""",
           """      blocks.push({ type: 'input', block_id: 'holding_c', optional: true, label: pt('Holding rooms'), element: Object.assign({ type: 'multi_static_select', action_id: 'holding_c_pick', placeholder: pt('Select holding rooms'), options: ho }, hi.length ? { initial_options: hi } : {}) }); }   // v25: a dropdown""", want=5)
everywhere("""    options: [{ text: pt('Change other session details'), value: 'det' }] }] };""", """    options: [{ text: pt('Change other details'), value: 'det' }] }] };""", want=5)

PARSE_FN = r"""function parseTitle(b) {
  const t = String(b.t || ''), r = String(b.r || '');
  if (/^M[1-8]$/.test(r)) { const m = t.match(/^\S+\s+-\s+(.+)$/); return { kind: 'booth', name: m ? m[1].trim() : '' }; }   // v25: the name after "M2 - "
  const segs = t.split(' / ').map(x => x.trim());
  if (segs.length === 1) { const m = t.match(/^(.+?)\s+-\s+(.+)$/); return { kind: 'meeting', title: m ? m[2] : t, prefix: m ? m[1] : '' }; }
  const ini = segs[segs.length - 1].split(/\s+x\s+/i).map(x => (x || '').trim());
  if (segs.length === 2 && /^[A-Z0-9]+(?:-[A-Z0-9]+)+$/.test(segs[0])) return { kind: 'loc', code: segs[0], ei: ini[0] || '', ai: '' };
  return { kind: 'studio', project: segs[0], client: segs.length >= 3 ? segs.slice(1, -1).join(' / ') : '', ei: ini[0] || '', ai: ini[1] || '' };
}
"""
replace_fn("parseTitle", "function staffOf(", PARSE_FN, 5)

DET_FN = r"""function detBlocks(b, data, vals) {   // v24: the fields of the booking's session type (or the type picked on the form)
  const pt = x => ({ type: 'plain_text', text: x });
  const O = detOrig(b, data), V = Object.assign({}, O, vals || {}), st = staffOf(data);
  const T = String((vals && vals.st) || b.st || ''), K = typeKind(T) || O.kind;
  const R = T ? typeRoles(data, T) : { known: false, eng: K !== 'meeting', arr: K === 'studio' && !!O.ai, either: false };
  const iv = (el, v) => { v = String(v || '').trim().slice(0, 150); if (v) el.initial_value = v; return el; };
  const inp = (bid, label, el, opt) => Object.assign({ type: 'input', block_id: bid, label: pt(label), element: el }, opt ? { optional: true } : {});
  const txt = (aid, v, o) => iv(Object.assign({ type: 'plain_text_input', action_id: aid, placeholder: pt('__BLANK__') }, o || {}), v);   // v25: blank boxes
  const popt = x => ({ text: pt(x.name), value: x.slack });
  const engs = (R.either ? [{ text: pt('No engineer'), value: 'none' }] : []).concat(st.filter(x => /\bengineer\b/i.test(x.info)).sort((x, y) => x.name.localeCompare(y.name)).slice(0, R.either ? 99 : 100).map(popt));
  const arrs = [{ text: pt('No arranger'), value: 'none' }].concat(st.filter(x => /\barranger\b/i.test(x.info)).sort((x, y) => x.name.localeCompare(y.name)).slice(0, 99).map(popt));   // a picked dropdown cannot be emptied
  const sel = (aid, opts, val, ph) => { const o = opts.find(x => x.value === val); return Object.assign({ type: 'static_select', action_id: aid, placeholder: pt(ph), options: opts }, o ? { initial_option: o } : {}); };
  const notes = inp('det_notes', 'Note', txt('det_notes_in', '', { multiline: true }), true);
  const engIn = opt => inp('det_engineer', 'Engineer', sel('det_engineer_pick', engs, V.en, 'Select an engineer'), opt);
  if (K === 'booth') return [inp('det_forname', 'Who is it for?', txt('det_forname_in', V.forname != null ? V.forname : O.name))];   // v25: the name in the title
  if (K === 'meeting') return [inp('det_title', T === 'Event' ? 'Event title' : 'Meeting title', txt('det_title_in', V.title)), notes];
  if (K === 'loc') { const code = String(V.code || '').trim();   // v25: a typed code (Enter: the project's people)
    return [Object.assign(inp('det_code', 'Project code', txt('det_code_in', code, { dispatch_action_config: { trigger_actions_on: ['on_enter_pressed'] } })), { dispatch_action: true }),
      engIn(false), notes]; }
  if (K === 'post') return [inp('det_project', 'Project title', txt('det_project_in', V.project)),
    { type: 'context', block_id: 'det_booker', elements: [{ type: 'mrkdwn', text: 'Booker: Dylan Diaz' }] }, notes];
  if (K === 'atmos') return [inp('det_project', 'Project title or code', txt('det_project_in', V.project || V.code)), engIn(false), notes];   // v25
  const out = [inp('det_project', 'Project title', txt('det_project_in', V.project)),
    inp('det_client', 'Client', txt('det_client_in', V.client), true)];
  if (R.either) out.push({ type: 'context', block_id: 'team_note', elements: [{ type: 'mrkdwn', text: 'Engineer and arranger: pick one or both.' }] });
  if (R.eng || !R.known) out.push(engIn(R.either));
  if (R.arr) out.push(inp('det_arranger', 'Arranger', sel('det_arranger_pick', arrs, V.ar, 'Select an arranger'), true));
  out.push(notes);
  return out;
}
""".replace("__BLANK__", BLANK)
replace_fn("detBlocks", "// the new title from the details", DET_FN, 5)

DETTITLE_FN = r"""function detTitle(b, data, d, room) {   // v24: the title follows the session type picked on the form (its kind decides the shape)
  d = d || {};
  const O = detOrig(b, data), st = staffOf(data), ini = id => { const x = st.find(y => y.slack === id); return x ? x.ini : ''; };
  const K = typeKind(d.st || '') || O.kind;
  if (K === 'booth' || O.kind === 'booth') {   // v25: "M2 - <name>" - the room and the name as now
    const nm0 = d.forname != null && d.forname !== '' ? d.forname : (O.name || ''), nmB = nm0 === (O.name || '') ? nm0 : cap1(nm0);   // an unchanged name stays as it was
    const rm = String(room || String(b.r || '').split(',')[0] || '').trim().toUpperCase();
    return nmB && rm ? rm + ' - ' + nmB : b.t; }
  if (K === 'meeting') { const t0 = O.title || O.project || '', tt = d.title != null ? String(d.title).trim() : t0;   // v25: a new title starts with a capital;
    return String(room || O.prefix || b.r || '').toUpperCase() + ' - ' + (tt === t0 ? tt : cap1(tt)); }        // an unchanged one stays as it was (no pointless change)
  const ok = x => x && x !== 'none';
  const ei = d.teamShown ? (ok(d.en) ? ini(d.en) : '') : (ok(d.en) ? ini(d.en) : (d.en === 'none' ? '' : O.ei));
  const ai = d.teamShown ? (ok(d.ar) ? ini(d.ar) : '') : (ok(d.ar) ? ini(d.ar) : (d.ar === 'none' ? '' : O.ai));
  const inits = [ei, ai].filter(Boolean).join(' x ');
  if (K === 'loc') return [String(d.code ? d.code : (O.code || '')).trim(), inits].filter(Boolean).join(' / ');
  if (K === 'atmos') return [String(d.project ? d.project : (O.project || O.code || '')).trim().toUpperCase(), ei].filter(Boolean).join(' / ');   // v25: PROJECT / initials
  return [String(d.project != null && d.project !== '' ? d.project : (O.project || O.code || '')).trim().replace(/^(?:project|proj)\s+/i, '').toUpperCase(),
          K === 'post' ? '' : String(d.client != null ? d.client : (O.client || '')).trim(), K === 'post' ? (O.ei || ei) : inits].filter(Boolean).join(' / ');
}
"""
replace_fn("detTitle", "// v19: a room as the calendar", DETTITLE_FN, 5)

# Read Change: the M booth name, Atmos, the code as typed; fewer words
patch("Read Change", [
    ("const open = Object.keys(v).some(k => /^det_(?:project|client|code|title|engineer|arranger|notes)$/.test(k) || k === 'purpose_c');   // v24",
     "const open = Object.keys(v).some(k => /^det_(?:project|client|code|title|engineer|arranger|notes|forname)$/.test(k) || k === 'purpose_c');   // v24; v25: forname"),
    ("        title: txt('det_title', 'det_title_in'), en: sel('det_engineer', 'det_engineer_pick'),",
     "        title: txt('det_title', 'det_title_in'), forname: txt('det_forname', 'det_forname_in'), en: sel('det_engineer', 'det_engineer_pick'),"),
    ("  if ((KD === 'studio' || KD === 'post') && v.det_project && !d.project) errors.det_project = 'What is the project called?';",
     "  if ((KD === 'studio' || KD === 'post' || KD === 'atmos') && v.det_project && !d.project) errors.det_project = 'What is the project called?';\n"
     "  if (KD === 'booth' && v.det_forname && !d.forname) errors.det_forname = 'Who is it for?';   // v25"),
    ("  if (KD === 'studio' || KD === 'loc') {\n    if (RD.either)", "  if (KD === 'studio' || KD === 'loc' || KD === 'atmos') {   // v25: + Atmos\n    if (RD.either)"),
    ("const newTitle = detTitle(b, data, d || {}, O.kind === 'meeting' && roomChanged ? n.r : null);",
     "const newTitle = detTitle(b, data, d || {}, (O.kind === 'meeting' || O.kind === 'booth') && roomChanged ? n.r : null);   // v25: an M booth's title follows its room"),
    ("  errors.date = open ? 'Nothing changed - change the date, time, room or a detail.' : 'Nothing changed - pick a new date, time or room.';",
     "  errors.date = 'Nothing changed.';   // v25"),
    ("{ type: 'context', elements: [{ type: 'mrkdwn', text: 'You may close this window – we’ll notify you once it’s done.' }] }] };",
     "{ type: 'context', elements: [{ type: 'mrkdwn', text: 'You can close this window – we’ll let you know once it’s done.' }] }] };"),
])

# ════ route 8 (Note Toggle): the either/or room, the code on Enter ══════════════════════════════════════════════════════
patch("Note Toggle", [
    ("const WH = ['repeat_toggle', 'details_toggle', 'room_toggle', 'add_booth', 'add_holding', 'allday_toggle', 'purpose_pick', 'room_radio', 'code_pick', 'forwho_toggle', 'purpose_c'];   // v21; v24",
     "const WH = ['repeat_toggle', 'details_toggle', 'room_toggle', 'add_booth', 'add_holding', 'allday_toggle', 'purpose_pick', 'room_radio', 'code_pick', 'forwho_toggle', 'purpose_c',\n"
     "  'room_other_pick', 'code_in', 'det_code_in'];   // v21; v24; v25: Another room, a code on Enter"),
    ("  : which === 'code_pick' ? ['code_info'] : which === 'forwho_toggle' ? (on ? [] : ['forwho'])",
     "  : (which === 'code_pick' || which === 'code_in' || which === 'det_code_in') ? ['code_info'] : which === 'forwho_toggle' ? (on ? [] : ['forwho'])\n"
     "  : which === 'room_other_pick' ? []"),
    ("  : which === 'purpose_pick' ? ['allday_toggle'] : which === 'room_radio' ? ['room_other']",
     "  : which === 'purpose_pick' ? ['allday_toggle'] : which === 'room_radio' ? []   // v25: Another room stays (cleared below)"),
    ("const atId = which === 'code_pick' ? (blocks.some(b => b.block_id === 'code') ? 'code' : 'det_code') : ({ purpose_pick: 'purpose', room_radio: 'room' }[which] || which);   // v24\n"
     "const at = blocks.findIndex(b => b.block_id === atId);",
     "const atId = (which === 'code_pick' || which === 'code_in' || which === 'det_code_in') ? (blocks.some(b => b.block_id === 'code') ? 'code' : 'det_code') : ({ purpose_pick: 'purpose', room_radio: 'room', room_other_pick: 'room_other' }[which] || which);   // v24\n"
     "// v25: the room list and Another room get a new block_id when cleared (\"room~123\") - find them by their stem\n"
     "const at = blocks.findIndex(b => (which === 'room_radio' || which === 'room_other_pick') ? new RegExp('^' + atId + '(~\\\\d+)?$').test(b.block_id || '') : b.block_id === atId);"),
    ("  const studioNow = (((st.room || {}).room_radio || {}).selected_option || {}).value || (((rb || {}).element || {}).initial_option || {}).value || '';",
     "  const studioNow = (((st.room || {}).room_radio || {}).selected_option || {}).value || (((rb || {}).element || {}).initial_option || {}).value || '';\n"
     "  // v25: one or the other - a room ticked clears Another room, a room from Another room clears the ticked one (a new block_id, so\n"
     "  // Slack forgets the old pick); the booth follows the room picked\n"
     "  if (which === 'room_radio' || which === 'room_other_pick') {\n"
     "    const picked = String((a.selected_option || {}).value || '');\n"
     "    const k = Date.now() % 1000000;\n"
     "    const clear = (re, nb) => { const i = blocks.findIndex(b => re.test(b.block_id || '')); if (i === -1) return;\n"
     "      const c = JSON.parse(JSON.stringify(blocks[i])); c.block_id = nb + '~' + k;\n"
     "      for (const e of [].concat(c.element || [], c.elements || [])) delete e.initial_option;\n"
     "      blocks[i] = c; };\n"
     "    if (which === 'room_radio') clear(/^room_other(~\\d+)?$/, 'room_other'); else clear(/^room(~\\d+)?$/, 'room');\n"
     "    const bi = blocks.findIndex(b => /^booth(~\\d+)?$/.test(b.block_id || ''));\n"
     "    if (bi !== -1 && picked && M2.bx) blocks.splice(bi, 1, ...boothBlocks(picked, M2.bx));\n"
     "  }"),
    ("  if (which === 'room_radio' && studioNow !== '__other') { const bi = blocks.findIndex(b => b.block_id === 'booth'); if (bi !== -1) blocks.splice(bi, 1, ...boothBlocks(studioNow, M2.bx)); }",
     "  // (v21-v24: the booth followed a studio change here - v25 above)"),
    ("  if (which === 'code_pick') {\n    const pv = String((a.selected_option || {}).value || ''), code = pv.replace(/^new:/, '');",
     "  if (which === 'code_pick' || which === 'code_in' || which === 'det_code_in') {   // v25: a typed code on Enter (code_pick: a v24 form still open)\n"
     "    const pv = which === 'code_pick' ? String((a.selected_option || {}).value || '') : String(a.value || '').trim().toUpperCase(), code = pv.replace(/^new:/, '');"),
    ("    if (code) blocks.splice(at + 1, 0, { type: 'context', block_id: 'code_info', elements: [{ type: 'mrkdwn', text: locInfo(proj, code) }] });",
     "    if (code && proj) blocks.splice(at + 1, 0, { type: 'context', block_id: 'code_info', elements: [{ type: 'mrkdwn', text: locInfo(proj, code) }] });   // v25: only a known project"),
    ("      if (first.length) { eb.element.options = first.concat(opts.filter(o => first.indexOf(o) === -1)); eb.element.initial_option = first[0];\n"
     "        eb.hint = pt('From the project. Change it if someone else is engineering.'); } }",
     "      if (first.length) { eb.element.options = first.concat(opts.filter(o => first.indexOf(o) === -1)); eb.element.initial_option = first[0];\n"
     "        delete eb.hint; } }   // v25: no hint - the project line lists the people"),
    ("element: { type: 'static_select', action_id: 'forwho_pick', placeholder: pt('Choose a person'),", "element: { type: 'static_select', action_id: 'forwho_pick', placeholder: pt('Select a person'),"),
    ("    const el = id => ({ type: 'static_select', action_id: id, placeholder: pt('Choose a time'), options: times });",
     "    const el = id => ({ type: 'static_select', action_id: id, placeholder: pt(id === 'end_pick' ? 'Select an end time' : 'Select a start time'), options: times });"),
    ("    element: { type: 'plain_text_input', action_id: 'notes_in', focus_on_load: true, placeholder: pt('Anything the session needs') } });",
     "    element: { type: 'plain_text_input', action_id: 'notes_in', focus_on_load: true, placeholder: pt('__BLANK__') } });".replace("__BLANK__", BLANK)),
    ("    if (ro.length) blocks.splice(at + 1, 0, { type: 'input', block_id: 'room_other', label: pt('Another room'), hint: pt(('Not a usual room for ' + (meta.label || 'this') + ' - booked as asked.').slice(0, 150)),\n"
     "      element: { type: 'static_select', action_id: 'room_other_pick', placeholder: pt('Choose a room'), options: ro } });",
     "    if (ro.length) blocks.splice(at + 1, 0, { type: 'input', block_id: 'room_other', label: pt('Another room'), hint: pt(('Not a usual room for ' + (meta.label || 'this') + '.').slice(0, 150)),\n"
     "      element: { type: 'static_select', action_id: 'room_other_pick', placeholder: pt('Select a room'), options: ro } });"),
])
# v25: the room list is an actions block - keep its pick on every redraw (the restore loop only kept checkboxes there)
patch("Note Toggle", [("""  if (b.type === 'actions') { for (const e of b.elements || []) if (e.type === 'checkboxes' && b.block_id !== which) {""",
                       """  if (b.type === 'actions') { for (const e of b.elements || []) if (e.type === 'radio_buttons' || e.type === 'static_select') {   // v25: the room list
      const sv = (st[b.block_id] || {})[e.action_id] || {}; const w = sv.selected_option && sv.selected_option.value; const o = (e.options || []).find(x => x.value === w); if (o) e.initial_option = o; }
    for (const e of b.elements || []) if (e.type === 'checkboxes' && b.block_id !== which) {""")])
# the code typed on the Change form is read too (Read Change already reads det_code_in); a v24 code_pick still works
patch("Check Signature", [("'room_radio', 'code_pick', 'forwho_toggle', 'purpose_c'].indexOf(action) !== -1) route = ROUTES.note_toggle;",
                           "'room_radio', 'code_pick', 'forwho_toggle', 'purpose_c', 'room_other_pick', 'code_in', 'det_code_in'].indexOf(action) !== -1) route = ROUTES.note_toggle;")])

# main v275 leads a typed change with "Your change so far:" - dropped like "Here's the booking" once it is done
everywhere("/^(?:Here(?:’|')s |Here it is)/", "/^(?:Here(?:’|')s |Here it is|Your change so far)/", want=4)

wf["name"] = "Jessie — Slack Interactions — v25 (round 8: forms, wording, single rooms)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
