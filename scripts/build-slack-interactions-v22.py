#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v22.json - "Jessie — Slack Interactions", v22: round 5 of the Slack-test notes (15 Oct).

  1. Booth options no longer say "the engineer patches it (Dante)" (the usual one keeps "<studio>'s usual booth"); the hints
     lose "- the engineer patches it" too.
  2. "Use another room" is the last choice in the Room list ("_Another room…_"); picking it opens the dropdown under the list.
     The separate checkbox row (and its padding) is gone.
  3. Working lines: no "This takes a few seconds."; "You may close this window – we’ll notify you once it’s done."
  4. The Change form on an all-day booking (an M booth all day = 12:00 AM to 12:00 AM the next day): "All day booking" ticked,
     no Start / End; a room or date change keeps it all day; rows and cards say "All day", not "12:00 AM – 12:00 AM".
  5. Music Mixing / Music Vocal Recording: "No engineer" - an engineer, an arranger, or both, never neither.
  6. A booking's rooms in order - studio, booth, holding rooms: a "Rooms:" line in the description (written at booking, kept by
     Move Booking v32) and, for older bookings, Airtable's room kinds. The Change form for a booking with a booth / holding
     rooms shows Studio, Booth (or No booth) and Holding rooms, like Book. "Likha (Big Room)" reads "Likha".
Built on workflows/imported/slack-interactions-v21-imported.json (the live download). Needs Move Booking v32 (Rooms line).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v21-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v22.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:90], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


def everywhere(a, b, want):
    n_hit = 0
    for n in wf["nodes"]:
        js = n["parameters"].get("jsCode")
        if js and a in js:
            n["parameters"]["jsCode"] = js.replace(a, b); n_hit += 1
    assert n_hit == want, (a[:70], n_hit, want)


# ---- 1: booth wording (BOOTH_JS sits in Build Step 1, Build Step 2, Note Toggle)
everywhere("""  const opts = list.slice(0, 10).map(n => ({ text: pt(n), value: n, description: pt(n === P.usual ? studio + '’s usual booth' : 'the engineer patches it (Dante)') }));""",
           """  const opts = list.slice(0, 10).map(n => Object.assign({ text: pt(n), value: n }, n === P.usual ? { description: pt(studio + '’s usual booth') } : {}));   // v22: no "the engineer patches it" """, 3)
everywhere("""Any free booth works - the engineer patches it.""", """Any free booth works.""", 3)

# ---- 3: working lines
everywhere("""Checking availability for each date. This takes a few seconds.""", """Checking availability for each date.""", 1)
everywhere("""Your booking is being processed. This takes a few seconds. You may close this window. You’ll be notified when it’s done.""",
           """Your booking is being processed. You may close this window – we’ll notify you once it’s done.""", 1)
everywhere("""Processing your series of bookings. This may take a while. You may close this window. You’ll be notified when it’s done.""",
           """Processing your series of bookings. This may take a while. You may close this window – we’ll notify you once it’s done.""", 1)
everywhere("""This takes a few seconds. You may close this window. You’ll be notified when it’s done.""",
           """You may close this window – we’ll notify you once it’s done.""", 1)

# ---- 4 / 6: shared row helpers - all day, room names, rooms in order
everywhere("""function roomName(x) { return String(x || '').replace(/^KDC Plaza-Top Level-/i, '').replace(/\\s*\\([^)]*\\)\\s*$/, '').trim(); }""",
           """function roomName(x) { return String(x || '').replace(/^KDC Plaza-Top Level-/i, '').replace(/(?:\\s*\\([^)]*\\))+\\s*$/, '').trim(); }   // v22: "Likha (Big Room) (12)" -> Likha""", 13)
everywhere("""function evRoom(e) { const r = (e.attendees || []).filter(a => a.resource || /@resource\\.calendar\\.google\\.com$/i.test(String(a.email || '')))
  .map(a => roomName(a.displayName)).filter(Boolean);
  return r.length ? r.join(', ') : roomName(e.location); }""",
           """function evRoom(e) { const r = (e.attendees || []).filter(a => a.resource || /@resource\\.calendar\\.google\\.com$/i.test(String(a.email || '')))
  .map(a => roomName(a.displayName)).filter(Boolean);
  // v22: Google lists the rooms in its own order - the booking's "Rooms:" line keeps studio, booth, holding rooms
  const w = (String(e.description || '').match(/(?:^|\\|)\\s*Rooms:\\s*([^|\\n]+)/i) || [])[1];
  if (w && r.length) { const o = w.split(',').map(x => x.trim()).filter(Boolean), lc = a => a.map(x => x.toLowerCase()).sort().join();
    if (lc(o) === lc(r)) return r.slice().sort((x, y) => o.findIndex(z => z.toLowerCase() === x.toLowerCase()) - o.findIndex(z => z.toLowerCase() === y.toLowerCase())).join(', '); }
  return r.length ? r.join(', ') : roomName(e.location); }""", 13)
ALLDAY_T = """(b.s && !(b.s === '00:00' && b.e === '00:00') ? t12(b.s) + ' – ' + t12(b.e) : """
everywhere("""(b.s ? t12(b.s) + ' – ' + t12(b.e) : 'All day')""", ALLDAY_T + "'All day')", 13)
everywhere("""(b.s ? t12(b.s) + ' – ' + t12(b.e) : 'all day')""", ALLDAY_T + "'all day')", 13)
# rooms by kind (for bookings with no Rooms line): the room lists gain the vocal booths
everywhere("""function roomLists(data) {
  const all = [], common = [];
  for (const r of (data && data.rooms) || []) { const f = r.fields || {}; const n = String(f['Room Name'] || '').trim(); if (!n) continue; all.push(n);
    const k = [].concat(f['Room Type'] || []).map(x => String(x).toLowerCase()); if (k.indexOf('conference room') !== -1 || k.indexOf('lobby') !== -1) common.push(n); }
  return { all, common };
}""", """function roomLists(data) {
  const all = [], common = [], vb = [];
  for (const r of (data && data.rooms) || []) { const f = r.fields || {}; const n = String(f['Room Name'] || '').trim(); if (!n) continue; all.push(n);
    const k = [].concat(f['Room Type'] || []).map(x => String(x).toLowerCase()); if (k.indexOf('conference room') !== -1 || k.indexOf('lobby') !== -1) common.push(n);
    if (f['Vocal Booth'] === true) vb.push(n); }   // v22
  return { all, common, vb };
}
// v22: a booking's rooms by kind - the studio (or the one room), its booth(s), its holding rooms
function roomParts(r, rooms) {
  const all = (rooms && rooms.all) || [], cn = x => { const v = roomName(x); return all.find(a => a.toLowerCase() === v.toLowerCase()) || v; };
  const list = String(r || '').split(',').map(x => cn(x.trim())).filter(Boolean);
  const isC = n => ((rooms && rooms.common) || []).indexOf(n) !== -1, isB = n => ((rooms && rooms.vb) || []).indexOf(n) !== -1;
  const studio = list.find(n => !isC(n) && !isB(n)) || list[0] || '';
  return { studio, booths: list.filter(n => n !== studio && isB(n)), holds: list.filter(n => n !== studio && !isB(n)) };
}
function orderRooms(r, rooms) { const P = roomParts(r, rooms); return [P.studio].concat(P.booths, P.holds).filter(Boolean).join(', '); }""", 5)

# ---- 2: "Another room…" as the last choice in the Room list
patch("Build Step 2", [
    ("""  // v19: "Use another room" - the other free rooms of this kind (free on every date of a series), booked as asked (route 8)
  if (others.length) blocks.push({ type: 'actions', block_id: 'room_toggle', elements: [{ type: 'checkboxes', action_id: 'room_toggle',
    options: [{ text: { type: 'plain_text', text: 'Use another room' }, value: 'room' }] }] });""",
     """  // v22: "Another room…" is the last choice in the list (v19-v21: a separate "Use another room" box); picking it opens the
  // dropdown of the other free rooms of this kind (route 8, room_radio)"""),
    ("""  blocks.push(input(needBooth ? 'room' : 'room', needBooth ? 'Studio' : 'Room', { type: 'radio_buttons', action_id: 'room_radio', options: rooms, initial_option: preRoom || rooms[0] },
    BX ? { dispatch_action: true } : undefined));   // v21: a studio change resets the booth""",
     """  const roomOpts = others.length ? rooms.slice(0, 9).concat([{ text: md('_Another room…_'), value: '__other' }]) : rooms;   // v22
  blocks.push(input('room', needBooth ? 'Studio' : 'Room', { type: 'radio_buttons', action_id: 'room_radio', options: roomOpts,
    initial_option: roomOpts.find(o => o.value === (preRoom || rooms[0]).value) || roomOpts[0] },
    BX || others.length ? { dispatch_action: true } : undefined));   // v21: a studio change resets the booth; v22: Another room…"""),
])
patch("Note Toggle", [
    ("""  : which === 'purpose_pick' ? ['allday_toggle'] : which === 'room_radio' ? [] : ['notes'];""",
     """  : which === 'purpose_pick' ? ['allday_toggle'] : which === 'room_radio' ? ['room_other'] : ['notes'];   // v22: room_radio redraws Another room…"""),
    ("""  if (which === 'room_radio') { const bi = blocks.findIndex(b => b.block_id === 'booth'); if (bi !== -1) blocks.splice(bi, 1, ...boothBlocks(studioNow, M2.bx)); }""",
     """  if (which === 'room_radio' && studioNow !== '__other') { const bi = blocks.findIndex(b => b.block_id === 'booth'); if (bi !== -1) blocks.splice(bi, 1, ...boothBlocks(studioNow, M2.bx)); }
  // v22: "Another room…" picked -> the dropdown of the other free rooms right under the list
  if (which === 'room_radio' && studioNow === '__other') { const ro = [].concat(M2.others || []).map(n => ({ text: pt(n), value: n }));
    if (ro.length) blocks.splice(at + 1, 0, { type: 'input', block_id: 'room_other', label: pt('Another room'), hint: pt(('Not a usual room for ' + (M2.label || 'this') + ' - booked as asked.').slice(0, 150)),
      element: { type: 'static_select', action_id: 'room_other_pick', placeholder: pt('Choose a room'), options: ro } }); }"""),
])
patch("Read Step 2", [
    ("""const room = val('room_other', 'room_other_pick') || val('room', 'room_radio');   // v19: "Use another room" wins""",
     """const room0 = val('room_other', 'room_other_pick') || val('room', 'room_radio');   // v19: "Use another room" wins
const room = room0 === '__other' ? '' : room0;   // v22: "Another room…" with nothing picked"""),
])

# ---- 5: "No engineer" for Music Mixing / Music Vocal Recording - an engineer, an arranger, or both
patch("Build Step 2", [
    ("""  const engEl = { type: 'static_select', action_id: 'engineer_pick', placeholder: { type: 'plain_text', text: "Who's engineering?" }, options: engs.slice(0, 100).map(popt) };""",
     """  const noEng = /^music (?:mixing|vocal recording)$/i.test(String(s.purpose || ''));   // v22: the arranger can run it
  const engEl = { type: 'static_select', action_id: 'engineer_pick', placeholder: { type: 'plain_text', text: "Who's engineering?" },
    options: (noEng ? [{ text: { type: 'plain_text', text: 'No engineer' }, value: 'none' }] : []).concat(engs.slice(0, noEng ? 99 : 100).map(popt)) };"""),
])
patch("Read Step 2", [
    ("""let engineerId = val('engineer', 'engineer_pick');   // v21: Post Processing - the booker below""",
     """const engPick = val('engineer', 'engineer_pick');   // v22: "none" = No engineer (music)
let engineerId = engPick === 'none' ? '' : engPick;   // v21: Post Processing - the booker below"""),
    ("""if ((s.kind === 'studio' || s.kind === 'loc') && !engineerId) errors.engineer = 'Pick the engineer.';""",
     """if ((s.kind === 'studio' || s.kind === 'loc') && !engineerId && !(engPick === 'none' && arrangerId))
  errors.engineer = engPick === 'none' ? 'Pick an engineer or an arranger.' : 'Pick the engineer.';   // v22: never neither"""),
    ("""  engineerId ? 'engineer ' + nm(engineerId) : '',""",
     """  engineerId ? 'engineer ' + nm(engineerId) : (engPick === 'none' ? 'no engineer' : ''),   // v22: Book Session does not ask"""),
])

# ---- 6: the Rooms line at booking
patch("Read Step 2", [
    ("""const descParts = [engineerId ? 'Engineer: ' + nm(engineerId) : '', arrangerId ? 'Arranger: ' + nm(arrangerId) : '',""",
     """const descParts = [engineerId ? 'Engineer: ' + nm(engineerId) : '', arrangerId ? 'Arranger: ' + nm(arrangerId) : '',
  roomsAll.length > 1 ? 'Rooms: ' + roomsAll.join(', ') : '',   // v22: studio, booth, holding rooms - Google reorders the attendees"""),
])

# ---- 4 / 6: the Change form - all day; Studio + Booth + Holding rooms for a multi-room booking
CV_OLD_TIMES = """  blocks.push({ type: 'input', block_id: 'date', label: pt('Date'), element: Object.assign({ type: 'datepicker', action_id: 'date_pick' }, /^\\d{4}-\\d{2}-\\d{2}$/.test(cur.d || '') ? { initial_date: cur.d } : {}) },
    { type: 'input', block_id: 'start', label: pt('Start'), element: Object.assign({ type: 'static_select', action_id: 'start_pick', placeholder: pt('Choose a time'), options: times }, so ? { initial_option: so } : {}) },
    { type: 'input', block_id: 'end', label: pt('End'), element: Object.assign({ type: 'static_select', action_id: 'end_pick', placeholder: pt('Choose a time'), options: times }, eo ? { initial_option: eo } : {}) });"""
CV_NEW_TIMES = """  blocks.push({ type: 'input', block_id: 'date', label: pt('Date'), element: Object.assign({ type: 'datepicker', action_id: 'date_pick' }, /^\\d{4}-\\d{2}-\\d{2}$/.test(cur.d || '') ? { initial_date: cur.d } : {}) });
  // v22: an all-day booking (no times, or 12:00 AM to 12:00 AM) - the All day box ticked, no Start / End (unticking brings them)
  const allDay = cur.allDay === true || (cur.allDay !== false && ((!cur.s && !cur.e) || (cur.s === '00:00' && cur.e === '00:00')));
  if (allDay) { const ad = { type: 'actions', block_id: 'allday_toggle', elements: [{ type: 'checkboxes', action_id: 'allday_toggle',
      options: [{ text: pt('All day booking'), value: 'allday' }] }] }; ad.elements[0].initial_options = ad.elements[0].options; blocks.push(ad); }
  else blocks.push({ type: 'input', block_id: 'start', label: pt('Start'), element: Object.assign({ type: 'static_select', action_id: 'start_pick', placeholder: pt('Choose a time'), options: times }, so ? { initial_option: so } : {}) },
    { type: 'input', block_id: 'end', label: pt('End'), element: Object.assign({ type: 'static_select', action_id: 'end_pick', placeholder: pt('Choose a time'), options: times }, eo ? { initial_option: eo } : {}) });"""
everywhere(CV_OLD_TIMES, CV_NEW_TIMES, 5)
CV_OLD_ROOM = """  if (ropts.length) { const ro = ropts.find(o => o.value === (cr || br)) || ropts[0];
    blocks.push({ type: 'input', block_id: 'room', label: pt('Room'), element: { type: 'static_select', action_id: 'room_pick', options: ropts, initial_option: ro } }); }"""
CV_NEW_ROOM = """  // v22: a booking with a booth or holding rooms - Studio, Booth (or No booth), Holding rooms, like Book (Move checks them free)
  const RP = roomParts(cur.r || b.r, rooms), multi = RP.booths.length > 0 || RP.holds.length > 0;
  if (ropts.length) { const ro = ropts.find(o => o.value === (cr || br)) || ropts[0];
    blocks.push({ type: 'input', block_id: 'room', label: pt(multi && kind(br) === 'studio' ? 'Studio' : 'Room'), element: { type: 'static_select', action_id: 'room_pick', options: ropts, initial_option: ro } }); }
  if (multi && kind(br) === 'studio') {
    const sortN = a => a.slice().sort((x, y) => x.localeCompare(y, 'en', { numeric: true }));
    if (RP.booths.length) { const bo = [{ text: pt('No booth'), value: 'none' }].concat(sortN([].concat(rooms.vb || [])).map(n => ({ text: pt(n), value: n })));
      blocks.push({ type: 'input', block_id: 'booth_c', label: pt('Booth'), element: { type: 'static_select', action_id: 'booth_c_pick', options: bo.slice(0, 100),
        initial_option: bo.find(o => o.value === RP.booths[0]) || bo[0] } }); }
    if (RP.holds.length) { const ho = sortN([].concat(rooms.common || []).filter(n => !/^lobby$/i.test(n))).map(n => ({ text: pt(n), value: n })).slice(0, 10);
      const hi = ho.filter(o => RP.holds.indexOf(o.value) !== -1);
      blocks.push({ type: 'input', block_id: 'holding_c', optional: true, label: pt('Holding rooms'), element: Object.assign({ type: 'checkboxes', action_id: 'holding_c_pick', options: ho }, hi.length ? { initial_options: hi } : {}) }); }
  }"""
everywhere(CV_OLD_ROOM, CV_NEW_ROOM, 5)
# the Change form's room list: vocal booths are their own kind (v21 listed Studio A / B / D with the studios)
everywhere("""  const kind = n => /^M[1-8]$/.test(n) ? 'booth' : (rooms.common.indexOf(n) !== -1 ? 'common' : 'studio');""",
           """  const kind = n => /^M[1-8]$/.test(n) ? 'booth' : (rooms.common.indexOf(n) !== -1 ? 'common' : ((rooms.vb || []).indexOf(n) !== -1 ? 'vbooth' : 'studio'));   // v22""", 5)
# the Change form's details: No engineer too (an arranger can run a music session)
everywhere("""  const engs = st.filter(x => /\\bengineer\\b/i.test(x.info)).sort((x, y) => x.name.localeCompare(y.name)).slice(0, 100).map(popt);""",
           """  const engs = (O.kind === 'studio' ? [{ text: pt('No engineer'), value: 'none' }] : []).concat(st.filter(x => /\\bengineer\\b/i.test(x.info)).sort((x, y) => x.name.localeCompare(y.name)).slice(0, 99).map(popt));   // v22""", 5)
everywhere("""  const ei = d.en ? ini(d.en) : O.ei, ai""", """  const ei = d.en === 'none' ? '' : d.en ? ini(d.en) : O.ei, ai""", 5)

patch("Build Change", [
    ("""const data = readCache($('Read Cache 6').all().map(i => i.json || {}));""",
     """const data = readCache($('Read Cache 6').all().map(i => i.json || {}));
// v22: the rooms in order - studio, booth, holding rooms (older bookings have no Rooms line; Google reorders them)
if (data && b.r) { b.r = orderRooms(b.r, roomLists(data)); if (!(nIn && nIn.r)) cur.r = b.r; }"""),
])
patch("Read Change", [
    ("""const n = { d: (v.date && v.date.date_pick && v.date.date_pick.selected_date) || '', s: sel('start', 'start_pick'), e: sel('end', 'end_pick'), r: sel('room', 'room_pick') || b.r || '' };
const errors = {};
if (!n.d) errors.date = 'Pick a date.';
if (!n.s) errors.start = 'Pick a start time.';
if (!n.e) errors.end = 'Pick an end time.';
if (n.s && n.e && n.e <= n.s) errors.end = 'The end has to be after the start.';""",
     """const n = { d: (v.date && v.date.date_pick && v.date.date_pick.selected_date) || '', s: sel('start', 'start_pick'), e: sel('end', 'end_pick'), r: sel('room', 'room_pick') || b.r || '' };
// v22: all day - no Start / End on the form; the booking stays 12:00 AM to 12:00 AM the next day
const allDay = !!(v.allday_toggle && v.allday_toggle.allday_toggle && (v.allday_toggle.allday_toggle.selected_options || []).length);
if (allDay) { n.s = '00:00'; n.e = '00:00'; n.allDay = true; }
const errors = {};
if (!n.d) errors.date = 'Pick a date.';
if (!allDay && !n.s) errors.start = 'Pick a start time.';
if (!allDay && !n.e) errors.end = 'Pick an end time.';
if (!allDay && n.s && n.e && n.e <= n.s) errors.end = 'The end has to be after the start.';"""),
    ("""const roomChanged = canonRoom(n.r, roomLists(data)) !== canonRoom(b.r, roomLists(data));   // v19: "Likha (Big Room)" is Likha""",
     """// v22: the studio, booth and holding rooms - every room on the booking, in order
const RL = roomLists(data), P0 = roomParts(b.r, RL);
const bsel = sel('booth_c', 'booth_c_pick');
const hsel = v.holding_c ? (((v.holding_c.holding_c_pick || {}).selected_options) || []).map(o => o.value) : P0.holds;
const newRooms = [canonRoom(n.r, RL)].concat(v.booth_c ? (bsel && bsel !== 'none' ? [bsel] : []) : P0.booths, hsel).filter((x, i, a) => x && a.indexOf(x) === i);
const oldRooms = [P0.studio].concat(P0.booths, P0.holds).filter(Boolean);
const roomChanged = newRooms.join('|').toLowerCase() !== oldRooms.join('|').toLowerCase();   // v19: "Likha (Big Room)" is Likha; v22: every room"""),
    ("""  if ((O.kind === 'studio' || O.kind === 'loc') && !d.en) errors.det_engineer = 'Pick the engineer.';""",
     """  if ((O.kind === 'studio' || O.kind === 'loc') && !d.en) errors.det_engineer = 'Pick the engineer.';
  if (d.en === 'none' && !(d.ar && d.ar !== 'none')) errors.det_engineer = 'Pick an engineer or an arranger.';   // v22"""),
    ("""const newDetails = teamChanged ? { Engineer: nm(d.en), Arranger: d.ar && d.ar !== 'none' ? nm(d.ar) : '', team: [d.en, d.ar && d.ar !== 'none' ? d.ar : ''].filter(Boolean).join(' ') } : null;""",
     """const newDetails = teamChanged ? { Engineer: d.en === 'none' ? '' : nm(d.en), Arranger: d.ar && d.ar !== 'none' ? nm(d.ar) : '', team: [d.en === 'none' ? '' : d.en, d.ar && d.ar !== 'none' ? d.ar : ''].filter(Boolean).join(' ') } : null;"""),
    ("""bkCard({ t: newTitle, d: n.d, s: n.s, e: n.e, r: [canonRoom(n.r, roomLists(data))].concat(roomExtras(b.r)).join(', ') }, '⏳ *Changing…*')""",
     """bkCard({ t: newTitle, d: n.d, s: n.s, e: n.e, r: newRooms.join(', ') }, '⏳ *Changing…*')"""),
    ("""return [{ json: { valid, b, n, meta, viewId: V.id || '', user: c.user, d, newTitle, newDetails, clientTyped, roomChanged,""",
     """return [{ json: { valid, b, n, meta, viewId: V.id || '', user: c.user, d, newTitle, newDetails, clientTyped, roomChanged, newRooms: newRooms.join(', '),"""),
])
patch("To Move", [
    ("""  new_start_iso: R.n.d + 'T' + R.n.s + ':00+08:00', new_end_iso: R.n.d + 'T' + R.n.e + ':00+08:00',
  new_rooms: R.roomChanged ? [R.n.r].concat(roomExtras(R.b.r)).join(', ') : '', requester: R.user, confirmed: true,   // v19: compared by the room's own name; v21: the booth / holding rooms come along""",
     """  new_start_iso: R.n.d + 'T' + R.n.s + ':00+08:00',
  new_end_iso: (R.n.allDay || (R.n.s === '00:00' && R.n.e === '00:00') ? new Date(Date.parse(R.n.d + 'T12:00:00Z') + 86400000).toISOString().slice(0, 10) + 'T' + R.n.e : R.n.d + 'T' + R.n.e) + ':00+08:00',   // v22: all day
  new_rooms: R.roomChanged ? (R.newRooms || [R.n.r].concat(roomExtras(R.b.r)).join(', ')) : '', requester: R.user, confirmed: true,   // v19 / v21; v22: studio, booth, holding rooms as picked"""),
    ("""  new_summary: title !== R.b.t ? title : '', new_details: R.newDetails ? JSON.stringify(R.newDetails) : '' } }];""",
     """  new_summary: title !== R.b.t ? title : '',
  // v22: the Rooms line follows the rooms (Move Booking v32); a single room drops it
  new_details: (R.newDetails || R.roomChanged) ? JSON.stringify(Object.assign({}, R.newDetails || {},
    R.roomChanged ? { Rooms: String(R.newRooms || '').split(',').filter(x => x.trim()).length > 1 ? R.newRooms : '' } : {})) : '' } }];"""),
])
# Note Toggle reads the Change form too: its All day box (allday_toggle) and Start / End use the same ids - nothing to add.

wf["name"] = "Jessie — Slack Interactions — v22 (round 5: rooms in order, all day change, no engineer)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
