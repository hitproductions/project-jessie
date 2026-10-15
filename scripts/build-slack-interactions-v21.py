#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v21.json - "Jessie — Slack Interactions", v21: round 4 of the Slack-test notes (15 Oct).

  1. "Use another room" showed nothing: the click was never routed (Check Signature sent room_toggle to "other"), and the
     dropdown's options carried descriptions, which Slack allows only in radio buttons and checkboxes. Routed; one hint under
     the dropdown instead.
  2. Holding rooms and vocal booths ON TOP of the studio. The Room list holds studios only (Celebrity Recording's ranking has
     Likha / Katha / Salin, Localization Dubbing's has Studio A / B / D). Celebrity Recording (Room Requirements: holding /
     conference) gets "+ Holding room" -> a checklist of the conference rooms free then; recording sessions get "+ Vocal booth"
     -> the free vocal booths. All rooms go on the one booking ("Studio F, Studio A, Likha").
  3. Studios and booths pair (prototype 36 / 36b / 71-76): Localization Dubbing (Room Requirements: separate vocal booth) shows
     Studio and Booth; the booth starts at the studio's usual one (Airtable "Paired with": a booth naming the studio first,
     then the studio's own list), any free one can be picked ("the engineer patches it (Dante)"); changing the studio resets
     it. A studio that records vocals in the room says so under + Vocal booth. Cards: "Studio F + Studio A" and "Holding room:
     Likha". The Change form keeps the booth and holding rooms when the studio changes.
  4. QC asks for the Localization details (Project code + Engineer, no client) - as Book Session already titles it.
  5. Post Processing: "Booker" (Dylan Diaz, set) instead of Engineer, a Project title, no client; title "PROJECT / DD". Anyone
     can pick it for now.
  6. M booth: "All day booking" appears once M booth is picked in "What's it for?"; ticked, Start and End go - all day OR the
     chosen times.
Built on workflows/imported/slack-interactions-v20-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v20-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v21.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:80], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


def prepend(node, code):
    by[node]["parameters"]["jsCode"] = code + "\n" + by[node]["parameters"]["jsCode"]


# ---- shared: rooms on a card / row - the studio (+ its booth), then the holding rooms
ROOMS_FN = r"""// v21: a booking's rooms - the first is the studio, a later studio / M booth is its booth ("Studio F + Studio A"),
// any other later room is a holding room
function roomList(r) { return String(r || '').split(',').map(x => x.trim()).filter(Boolean); }
function roomMain(r) { const a = roomList(r); return [a[0]].concat(a.slice(1).filter(x => /^(?:Studio\s|M\d)/i.test(x))).filter(Boolean).join(' + '); }
function roomHold(r) { return roomList(r).slice(1).filter(x => !/^(?:Studio\s|M\d)/i.test(x)).join(', '); }
function roomExtras(r) { return roomList(r).slice(1); }"""
OLD_CARD = r"""function bkCard(b, head) { return head + '\n\n*' + b.t + '*\n*Date:* ' + dayLong(b.d) + '\n*Time:* ' + (b.s ? t12(b.s) + ' – ' + t12(b.e) : 'All day') + '\n*Room:* ' + (b.r || '-'); }"""
NEW_CARD = ROOMS_FN + "\n" + r"""function bkCard(b, head) { return head + '\n\n*' + b.t + '*\n*Date:* ' + dayLong(b.d) + '\n*Time:* ' + (b.s ? t12(b.s) + ' – ' + t12(b.e) : 'All day') + '\n*Room:* ' + (roomMain(b.r) || '-') + (roomHold(b.r) ? '\n*Holding room:* ' + roomHold(b.r) : ''); }"""
OLD_WHEN = r"""function whenLine(b) { return dayShort(b.d) + ' · ' + (b.s ? t12(b.s) + ' – ' + t12(b.e) : 'all day') + (b.r ? ' · ' + b.r : ''); }"""
NEW_WHEN = r"""function whenLine(b) { return dayShort(b.d) + ' · ' + (b.s ? t12(b.s) + ' – ' + t12(b.e) : 'all day') + (b.r ? ' · ' + roomMain(b.r) + (roomHold(b.r) ? ' + ' + roomHold(b.r) : '') : ''); }"""
OLD_CANON = r"""function canonRoom(x, rooms) { const v = roomName(x); const all"""
NEW_CANON = r"""function canonRoom(x, rooms) { const v = roomName(String(x || '').split(',')[0]); const all"""   # v21: the studio of a multi-room booking
n_card = n_when = n_canon = 0
for n in wf["nodes"]:
    js = n["parameters"].get("jsCode")
    if not js:
        continue
    if OLD_CARD in js:
        js = js.replace(OLD_CARD, NEW_CARD); n_card += 1
    if OLD_WHEN in js:
        assert NEW_CARD in js, n["name"]
        js = js.replace(OLD_WHEN, NEW_WHEN); n_when += 1
    if OLD_CANON in js:
        js = js.replace(OLD_CANON, NEW_CANON); n_canon += 1
    n["parameters"]["jsCode"] = js
assert n_card == 13 and n_when == 13 and n_canon == 5, (n_card, n_when, n_canon)

# ---- 1: route every toggle and redraw to Note Toggle
patch("Check Signature", [
    ("""else if (p.type === 'block_actions' && (action === 'note_toggle' || action === 'repeat_toggle' || action === 'details_toggle')) route = ROUTES.note_toggle;   // v10; v13 Repeats; v18 details""",
     """else if (p.type === 'block_actions' && ['note_toggle', 'repeat_toggle', 'details_toggle', 'room_toggle', 'add_booth', 'add_holding', 'allday_toggle', 'purpose_pick', 'room_radio'].indexOf(action) !== -1) route = ROUTES.note_toggle;   // v10; v13 Repeats; v18 details; v21 room_toggle (v19 never routed it), booths, holding rooms, all day, purpose / studio redraws"""),
])

# ---- the booth picker and the all-day box (Build Step 1 / Build Step 2 / Note Toggle)
BOOTH_JS = r"""// v21: the Booth picker for a studio - the free vocal booths, the studio's usual one first (Airtable "Paired with")
function boothBlocks(studio, BX) {
  if (!BX) return [];
  const pt = x => ({ type: 'plain_text', text: String(x).slice(0, 150) });
  const P = (BX.pair && BX.pair[studio]) || { usual: '', list: [].concat(BX.list || []) };
  const list = [].concat(P.list || []);
  if (!list.length) return [{ type: 'context', block_id: 'booth', elements: [{ type: 'mrkdwn', text: '⚠️ No vocal booth is free then' + (BX.need ? ' - ' + studio + ' can still be booked on its own.' : '.') }] }];
  const opts = list.slice(0, 10).map(n => ({ text: pt(n), value: n, description: pt(n === P.usual ? studio + '’s usual booth' : 'the engineer patches it (Dante)') }));
  const inRoom = [].concat(BX.inRoom || []).indexOf(studio) !== -1;
  const hint = !BX.need && inRoom ? studio + ' records vocals in the room - add a booth only if the session needs one.'
    : P.usual && list[0] === P.usual ? 'Set to ' + studio + '’s usual booth. Any free booth works - the engineer patches it.'
    : P.usual ? studio + '’s usual booth (' + P.usual + ') is taken then. Any free booth works - the engineer patches it.'
    : 'Any free booth works - the engineer patches it.';
  return [{ type: 'input', block_id: 'booth', label: pt('Booth'), hint: pt(hint), element: { type: 'radio_buttons', action_id: 'booth_pick', options: opts, initial_option: opts[0] } }];
}
// v21: M booth - all day, or the chosen times
const ALLDAY_BLOCK = { type: 'actions', block_id: 'allday_toggle', elements: [{ type: 'checkboxes', action_id: 'allday_toggle',
  options: [{ text: { type: 'plain_text', text: 'All day booking' }, value: 'allday' }] }] };"""

# ---- 6: Build Step 1 - "What's it for?" redraws; M booth picked -> All day booking
prepend("Build Step 1", BOOTH_JS)
patch("Build Step 1", [
    ("""    { type: 'input', block_id: 'purpose', label: { type: 'plain_text', text: "What's it for?" },""",
     """    { type: 'input', block_id: 'purpose', dispatch_action: true, label: { type: 'plain_text', text: "What's it for?" },   // v21: M booth -> All day booking"""),
    ("""// v14: a typed series (main v268) - Repeats ticked and filled in""",
     """// v21: M booth already picked (typed) -> the All day box under it
if (purposeOpt && purposeOpt.value === '__booth') { const pi = view.blocks.findIndex(b => b.block_id === 'purpose'); view.blocks.splice(pi + 1, 0, JSON.parse(JSON.stringify(ALLDAY_BLOCK))); }
// v14: a typed series (main v268) - Repeats ticked and filled in"""),
])

# ---- 4 / 5 / 6: Read Step 1 - QC is Localization, Post Processing its own kind, all day
patch("Read Step 1", [
    ("""const t0 = pickT('start', 'start_pick');
const t1 = pickT('end', 'end_pick');""",
     """// v21: an M booth booked all day - no start or end (the box replaces them)
const allDay = !!(v.allday_toggle && v.allday_toggle.allday_toggle && (v.allday_toggle.allday_toggle.selected_options || []).length)
  && ((v.purpose && v.purpose.purpose_pick && v.purpose.purpose_pick.selected_option && v.purpose.purpose_pick.selected_option.value) === '__booth');
const t0 = allDay ? '00:00' : pickT('start', 'start_pick');
const t1 = allDay ? '23:59' : pickT('end', 'end_pick');"""),
    ("""const valid = Object.keys(errors).length === 0;""",
     """if (allDay && repOn) errors.purpose = 'All day books one date - untick Repeats, or untick All day and pick the times.';   // v21
const valid = Object.keys(errors).length === 0;"""),
    ("""  : /^localization/i.test(purpose) ? 'loc' : 'studio';""",
     """  : /^(?:localization|qc)\\b/i.test(purpose) ? 'loc' : /^post processing$/i.test(purpose) ? 'post' : 'studio';   // v21: QC as Localization; Post Processing"""),
    ("""if (series) s.series = series;   // v13""",
     """if (series) s.series = series;   // v13
if (allDay) s.allDay = true;   // v21"""),
])

# ---- 1 / 2 / 3 / 5 / 6: Build Step 2
prepend("Build Step 2", BOOTH_JS)
patch("Build Step 2", [
    ("""const data = readCache($('Read Cache 2').all().map(i => i.json || {})) || { rooms: [], sessionTypes: [], bookers: [] };""",
     """const data = readCache($('Read Cache 2').all().map(i => i.json || {})) || { rooms: [], sessionTypes: [], bookers: [] };
// v21: what kind each room is - the Room list holds studios only (booths and holding rooms are added on top)
const _row = n => ((data.rooms || []).find(r => String((r.fields || {})['Room Name'] || '').trim() === n) || {}).fields || null;
const _kindOf = n => { const f = _row(n); if (/^M[1-8]$/.test(n)) return 'booth'; if (!f) return '';
  const k = [].concat(f['Room Type'] || []).map(x => String(x).toLowerCase());
  if (k.indexOf('conference room') !== -1 || k.indexOf('lobby') !== -1) return 'common'; return f['Vocal Booth'] === true ? 'vbooth' : 'studio'; };
const _main = n => s.kind === 'meeting' || s.kind === 'booth' || _kindOf(n) === 'studio';
const ST = (data.sessionTypes || []).find(r => String((r.fields || {}).Type || '').trim() === s.purpose) || null;"""),
    ("""const when = DOW[dt.getUTCDay()] + ', ' + MON[dt.getUTCMonth()] + ' ' + dt.getUTCDate() + ' · ' + fmtT(s.t0) + '–' + fmtT(s.t1);""",
     """const when = DOW[dt.getUTCDay()] + ', ' + MON[dt.getUTCMonth()] + ' ' + dt.getUTCDate() + ' · ' + (s.allDay ? 'All day' : fmtT(s.t0) + '–' + fmtT(s.t1));   // v21"""),
    ("""  const pri = ra.free_priority || [], last = ra.free_last_resort || [];""",
     """  const pri = (ra.free_priority || []).filter(_main), last = (ra.free_last_resort || []).filter(_main);   // v21: studios only"""),
    ("""  const taken = usual.filter(r => pri.indexOf(r) === -1);""",
     """  const taken = usual.filter(r => _main(r) && pri.indexOf(r) === -1);"""),
    ("""// v13: a series - each room says on how many of the dates it is free""",
     """// v21: booths and holding rooms on top of the studio (free on every date of a series)
const _req = String(((ST || {}).fields || {})['Room Requirements'] || '');
const needBooth = s.kind === 'loc' && /vocal booth/i.test(_req);
const offerBooth = s.kind === 'studio' && /recording/i.test(String(s.purpose || '')) && !needBooth;
const offerHold = s.kind === 'studio' && /holding|conference/i.test(_req);
const _nm = r => String((r.fields || {})['Room Name'] || '').trim();
const _num = (x, y) => x.localeCompare(y, 'en', { numeric: true });
const vbooths = (data.rooms || []).filter(r => (r.fields || {})['Vocal Booth'] === true).map(_nm).filter(n => n && !busyAny.has(n)).sort(_num);
const allVB = (data.rooms || []).filter(r => (r.fields || {})['Vocal Booth'] === true).map(_nm).filter(Boolean);
// "Paired with": "Studio A, B, or D, Can change using Dante" -> Studio A, Studio B, Studio D; a booth that names the studio comes first
const pairedOf = n => String((_row(n) || {})['Paired with'] || '').split(/can change/i)[0].replace(/\\bStudio\\s+/gi, '')
  .split(/,|\\bor\\b/i).map(x => x.trim()).filter(x => /^[A-Z0-9]$/i.test(x)).map(x => 'Studio ' + x.toUpperCase());
const boothOrder = studio => { const back = allVB.filter(b => new RegExp('\\\\b' + studio.replace(/\\s+/g, '\\\\s+') + '\\\\b', 'i').test(String((_row(b) || {})['Paired with'] || '')));
  const pref = back.concat(pairedOf(studio).filter(b => allVB.indexOf(b) !== -1 && back.indexOf(b) === -1));
  const usual = pref[0] || '';
  return { usual, list: pref.filter(b => vbooths.indexOf(b) !== -1).concat(vbooths.filter(b => pref.indexOf(b) === -1)) }; };
const BX = (needBooth || offerBooth) && ra.status === 'OK' ? { need: needBooth, list: vbooths, pair: {},
  inRoom: (data.rooms || []).filter(r => (r.fields || {})['Records Vocals In-Room'] === true).map(_nm).filter(Boolean) } : null;
if (BX) for (const o of rooms) BX.pair[o.value] = boothOrder(o.value);
const holds = offerHold && ra.status === 'OK' ? (data.rooms || []).filter(r => [].concat((r.fields || {})['Room Type'] || []).map(x => String(x).toLowerCase()).indexOf('conference room') !== -1)
  .map(_nm).filter(n => n && !busyAny.has(n)).sort(_num) : [];
// v13: a series - each room says on how many of the dates it is free"""),
    ("""  blocks.push(input('room', 'Room', { type: 'radio_buttons', action_id: 'room_radio', options: rooms, initial_option: preRoom || rooms[0] }));""",
     """  blocks.push(input(needBooth ? 'room' : 'room', needBooth ? 'Studio' : 'Room', { type: 'radio_buttons', action_id: 'room_radio', options: rooms, initial_option: preRoom || rooms[0] },
    BX ? { dispatch_action: true } : undefined));   // v21: a studio change resets the booth"""),
    ("""    options: [{ text: { type: 'plain_text', text: 'Use another room' }, value: 'room' }] }] });""",
     """    options: [{ text: { type: 'plain_text', text: 'Use another room' }, value: 'room' }] }] });
  // v21: the booth (Localization Dubbing: always; recording sessions: + Vocal booth) and the holding rooms (+ Holding room)
  if (BX && BX.need) blocks.push(...boothBlocks((preRoom || rooms[0]).value, BX));
  if (offerHold) blocks.push({ type: 'actions', block_id: 'add_holding', elements: [{ type: 'checkboxes', action_id: 'add_holding',
    options: [{ text: { type: 'mrkdwn', text: '_+ Holding room_' }, value: 'hold' }] }] });
  if (BX && !BX.need) blocks.push({ type: 'actions', block_id: 'add_booth', elements: [{ type: 'checkboxes', action_id: 'add_booth',
    options: [{ text: { type: 'mrkdwn', text: '_+ Vocal booth_' }, value: 'booth' }] }] });"""),
    ("""  } else if (s.kind === 'loc') {""",
     """  } else if (s.kind === 'post') {   // v21: Post Processing - the booker is set, a project title, no client
    blocks.push({ type: 'section', block_id: 'booker', text: md('*Booker*\\n' + POST_BOOKER) },
      input('project', 'Project title', iv({ type: 'plain_text_input', action_id: 'project_in' }, pre.pj)), notes);
  } else if (s.kind === 'loc') {"""),
    ("""close: { type: 'plain_text', text: 'Back' }, private_metadata: JSON.stringify(Object.assign({}, s, { when, label }, nu.length ? { nu } : {}, others.length ? { others } : {})), blocks };""",
     """close: { type: 'plain_text', text: 'Back' }, private_metadata: JSON.stringify(Object.assign({}, s, { when, label }, nu.length ? { nu } : {}, others.length ? { others } : {},
    BX ? { bx: BX } : {}, offerHold ? { holds } : {})), blocks };   // v21"""),
])
prepend("Build Step 2", "const POST_BOOKER = 'Dylan Diaz';   // v21: Post Processing's booker (Howard 15 Oct: Dilan, for now)")

# ---- 1 / 2 / 3 / 6: Note Toggle - route the new toggles and redraws
prepend("Note Toggle", BOOTH_JS)
patch("Note Toggle", [
    ("""const which = a.action_id === 'repeat_toggle' ? 'repeat_toggle' : a.action_id === 'details_toggle' ? 'details_toggle' : a.action_id === 'room_toggle' ? 'room_toggle' : 'note_toggle';
const OWN = which === 'repeat_toggle' ? ['rep_freq', 'rep_days', 'rep_count', 'rep_until', 'rep_note'] : which === 'details_toggle'
  ? ['det_project', 'det_client', 'det_code', 'det_title', 'det_engineer', 'det_arranger', 'det_none'] : which === 'room_toggle' ? ['room_other'] : ['notes'];""",
     """const WH = ['repeat_toggle', 'details_toggle', 'room_toggle', 'add_booth', 'add_holding', 'allday_toggle', 'purpose_pick', 'room_radio'];   // v21
const which = WH.indexOf(a.action_id) !== -1 ? a.action_id : 'note_toggle';
const OWN = which === 'repeat_toggle' ? ['rep_freq', 'rep_days', 'rep_count', 'rep_until', 'rep_note'] : which === 'details_toggle'
  ? ['det_project', 'det_client', 'det_code', 'det_title', 'det_engineer', 'det_arranger', 'det_none'] : which === 'room_toggle' ? ['room_other']
  : which === 'add_booth' ? ['booth'] : which === 'add_holding' ? ['holding'] : which === 'allday_toggle' ? (on ? ['start', 'end'] : [])
  : which === 'purpose_pick' ? ['allday_toggle'] : which === 'room_radio' ? [] : ['notes'];"""),
    ("""const at = blocks.findIndex(b => b.block_id === which);""",
     """const at = blocks.findIndex(b => b.block_id === ({ purpose_pick: 'purpose', room_radio: 'room' }[which] || which));"""),
    ("""  const cb = blocks[at].elements[0];""",
     """  const cb = (blocks[at].elements || [])[0] || {};   // v21: purpose / room are inputs, not boxes"""),
    ("""    const ro = [].concat(meta.others || []).map(n => ({ text: pt(n), value: n, description: pt(('not a usual room for ' + (meta.label || 'this')).slice(0, 75)) }));
    if (ro.length) blocks.splice(at + 1, 0, { type: 'input', block_id: 'room_other', label: pt('Another room'), element: { type: 'static_select', action_id: 'room_other_pick', placeholder: pt('Choose a room'), options: ro } });""",
     """    // v21: no option descriptions - Slack refuses them in a dropdown (the whole redraw failed)
    const ro = [].concat(meta.others || []).map(n => ({ text: pt(n), value: n }));
    if (ro.length) blocks.splice(at + 1, 0, { type: 'input', block_id: 'room_other', label: pt('Another room'), hint: pt(('Not a usual room for ' + (meta.label || 'this') + ' - booked as asked.').slice(0, 150)),
      element: { type: 'static_select', action_id: 'room_other_pick', placeholder: pt('Choose a room'), options: ro } });"""),
    ("""  if (on && which === 'repeat_toggle') {""",
     """  // v21: the booth, the holding rooms, a new studio (its booth reset), M booth all day
  let M2 = {}; try { M2 = JSON.parse(V.private_metadata || '{}'); } catch (e) {}
  const rb = blocks.find(b => b.block_id === 'room');
  const studioNow = (((st.room || {}).room_radio || {}).selected_option || {}).value || (((rb || {}).element || {}).initial_option || {}).value || '';
  if (on && which === 'add_booth') blocks.splice(at + 1, 0, ...boothBlocks(studioNow, M2.bx));
  if (on && which === 'add_holding') { const hs = [].concat(M2.holds || []);
    blocks.splice(at + 1, 0, hs.length ? { type: 'input', block_id: 'holding', optional: true, label: pt('Holding rooms'), hint: pt('One or more - booked with the studio.'),
      element: { type: 'checkboxes', action_id: 'holding_pick', options: hs.slice(0, 10).map(n => ({ text: pt(n), value: n })) } }
      : { type: 'context', block_id: 'holding', elements: [{ type: 'mrkdwn', text: '⚠️ No holding room is free then.' }] }); }
  if (which === 'room_radio') { const bi = blocks.findIndex(b => b.block_id === 'booth'); if (bi !== -1) blocks.splice(bi, 1, ...boothBlocks(studioNow, M2.bx)); }
  const ensureTimes = () => { if (blocks.some(b => b.block_id === 'start')) return;
    const times = []; for (let i = 0; i < 48; i++) { const mins = (8 * 60 + i * 30) % 1440, h = Math.floor(mins / 60), mm = mins % 60;
      times.push({ text: pt(((h % 12) || 12) + ':' + String(mm).padStart(2, '0') + ' ' + (h < 12 ? 'AM' : 'PM')), value: String(h).padStart(2, '0') + ':' + String(mm).padStart(2, '0') }); }
    const el = id => ({ type: 'static_select', action_id: id, placeholder: pt('Choose a time'), options: times });
    const di = blocks.findIndex(b => b.block_id === 'date');
    blocks.splice(di + 1, 0, { type: 'input', block_id: 'start', label: pt('Start'), element: el('start_pick') }, { type: 'input', block_id: 'end', label: pt('End'), element: el('end_pick') }); };
  if (which === 'purpose_pick') { if (String((a.selected_option || {}).value || '') === '__booth') blocks.splice(at + 1, 0, JSON.parse(JSON.stringify(ALLDAY_BLOCK))); else ensureTimes(); }
  if (which === 'allday_toggle' && !on) ensureTimes();
  if (on && which === 'repeat_toggle') {"""),
])

# ---- 2 / 3 / 5 / 6: Read Step 2 - every room on the booking, Post Processing's booker, all day
patch("Read Step 2", [
    ("""const room = val('room_other', 'room_other_pick') || val('room', 'room_radio');   // v19: "Use another room" wins""",
     """const room = val('room_other', 'room_other_pick') || val('room', 'room_radio');   // v19: "Use another room" wins
// v21: the booth and the holding rooms go on the same booking, after the studio
const booth = val('booth', 'booth_pick');
const holding = (((v.holding || {}).holding_pick || {}).selected_options || []).map(o => o.value);
const roomsAll = [room].concat(booth && booth !== room ? [booth] : []).concat(holding.filter(h => h && h !== room && h !== booth)).filter(Boolean);"""),
    ("""const engineerId = val('engineer', 'engineer_pick');""",
     """let engineerId = val('engineer', 'engineer_pick');   // v21: Post Processing - the booker below"""),
    ("""if (s.kind === 'studio' && !project) errors.project = 'What is the project called?';""",
     """if ((s.kind === 'studio' || s.kind === 'post') && !project) errors.project = 'What is the project called?';"""),
    ("""const who = id => bySlack[id] || null;""",
     """const who = id => bySlack[id] || null;
if (s.kind === 'post') { const pb = (data.bookers || []).map(b => b.fields || {}).find(f => String(f.Name || '').trim() === 'Dylan Diaz');   // v21
  engineerId = pb ? String(pb['Slack User ID'] || '').split(/[\\s,]+/).filter(Boolean)[0] || '' : '';
  if (!engineerId) errors.project = errors.project || 'Dylan Diaz isn’t in Bookers yet - ask for the booker to be added.'; }"""),
    ("""  (s.kind === 'booth' ? 'M booth' : s.purpose) + ' in ' + room + ' on ' + s.date + ' ' + fmt(s.t0) + '-' + fmt(s.t1),""",
     """  (s.kind === 'booth' ? 'M booth' : s.purpose) + ' in ' + roomsAll.join(', ') + ' on ' + s.date + ' ' + (s.allDay ? 'all day' : fmt(s.t0) + '-' + fmt(s.t1)),   // v21"""),
    ("""  (s.kind === 'studio') ? (client ? 'client ' + client : 'no client') : '',""",
     """  (s.kind === 'studio') ? (client ? 'client ' + client : 'no client') : s.kind === 'post' ? 'no client' : '',"""),
    ("""const team = [engineerId, arrangerId].filter(Boolean).join(' ');""",
     """const team = s.kind === 'post' ? '' : [engineerId, arrangerId].filter(Boolean).join(' ');   // v21: no notice for Post Processing's booker"""),
    ("""  mode: 'prepare', summary: calTitle, start_iso: s.date + 'T' + s.t0 + ':00+08:00', end_iso: s.date + 'T' + s.t1 + ':00+08:00',
  rooms: room, description: descParts.join(' | '), all_day: false, exclude_event_id: '', confirmed: false,""",
     """  mode: 'prepare', summary: calTitle, start_iso: s.date + 'T' + s.t0 + ':00+08:00',
  end_iso: s.allDay ? new Date(Date.parse(s.date + 'T12:00:00Z') + 86400000).toISOString().slice(0, 10) + 'T00:00:00+08:00' : s.date + 'T' + s.t1 + ':00+08:00',   // v21: all day
  rooms: roomsAll.join(', '), description: descParts.join(' | '), all_day: !!s.allDay, exclude_event_id: '', confirmed: false,"""),
    ("""    : [{ type: 'section', text: { type: 'mrkdwn', text: '⏳ *Booking ' + room + '…*\\n' + s.when } },""",
     """    : [{ type: 'section', text: { type: 'mrkdwn', text: '⏳ *Booking ' + roomsAll.join(' + ') + '…*\\n' + s.when } },"""),
    ("""return [{ json: { valid, calTitle, room, s, prep,""",
     """return [{ json: { valid, calTitle, room, rooms: roomsAll.join(', '), s, prep,"""),
])

# ---- the cards: "Studio F + Studio A" and "Holding room: Likha"
patch("After Book", [
    ("""  + '\\n*Room:* ' + (F['Room'] || R.room);""",
     """  + '\\n*Room:* ' + roomMain(F['Room'] || R.rooms || R.room) + (roomHold(F['Room'] || R.rooms || R.room) ? '\\n*Holding room:* ' + roomHold(F['Room'] || R.rooms || R.room) : '');   // v21"""),
    ("""  r: F['Room'] || R.room || '', t: title };""",
     """  r: F['Room'] || R.rooms || R.room || '', t: title };"""),
])
if "function roomMain" not in by["After Book Series"]["parameters"]["jsCode"]:
    prepend("After Book Series", ROOMS_FN)
patch("After Book Series", [
    ("""(T.rooms ? '\\n*Room:* ' + T.rooms : '')""",
     """(T.rooms ? '\\n*Room:* ' + roomMain(T.rooms) + (roomHold(T.rooms) ? '\\n*Holding room:* ' + roomHold(T.rooms) : '') : '')"""),
])

# ---- 3: Change keeps the booth and holding rooms when the studio changes
patch("To Move", [
    ("""  new_rooms: R.roomChanged ? R.n.r : '', requester: R.user, confirmed: true,   // v19: compared by the room's own name""",
     """  new_rooms: R.roomChanged ? [R.n.r].concat(roomExtras(R.b.r)).join(', ') : '', requester: R.user, confirmed: true,   // v19: compared by the room's own name; v21: the booth / holding rooms come along"""),
])
patch("Read Change", [
    ("""bkCard({ t: newTitle, d: n.d, s: n.s, e: n.e, r: canonRoom(n.r, roomLists(data)) }, '⏳ *Changing…*')""",
     """bkCard({ t: newTitle, d: n.d, s: n.s, e: n.e, r: [canonRoom(n.r, roomLists(data))].concat(roomExtras(b.r)).join(', ') }, '⏳ *Changing…*')"""),
])

wf["name"] = "Jessie — Slack Interactions — v21 (round 4: rooms, QC, post, all day)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes; cards", n_card, "rows", n_when, "canonRoom", n_canon)
