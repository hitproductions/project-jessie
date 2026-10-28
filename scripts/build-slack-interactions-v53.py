#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v53.json - Jessie — Slack Interactions — v53 (multiple studios), 28 Oct.

Howard, 28 Oct afternoon: one project that needs several studios must be one booking - one calendar event with every studio on
it as a room (like NET-TSTING's Studio 3 + Studio A), never duplicate events - and it must be possible to add or take one off on
Change. For every booking type except Van Recording, Atmos and Post Processing (one room each); meetings and events too (several
rooms). And a session that can have a vocal booth can have several.

Book Session, Move Booking and Cancel already hold several rooms on one event (each checked free, every room moved / cancelled
with it); only the forms offered one studio. v53:
1. **Book a room, step 2 (Build Step 2):** "+ Multiple studios" (meetings and events: "+ Multiple rooms") - a multi-select of the
   other rooms of that kind free then (free on every date of a series), after the booth / holding rooms; empty = just the one.
   Not for Van Recording, Atmos, Post Processing or M booths. Read Step 2 puts them on the booking after the first room (the title
   and the room checks follow the first room, as today); one that is not a usual room for the type is booked as asked
   (room_override, as Choose a different room does) - only when the type has a room ranking at all. Not with a room request.
2. **Vocal booths:** the Vocal booth dropdown becomes "Vocal booths", a multi-select (Book and Change) - the usual booth preset
   when the session needs one (Localization Dubbing: at least one, Slack enforces it); empty = no booth (a phone can remove a
   pick, so no "No booth" item is needed). An older form still open (one booth) is still read.
3. **Change:** "+ Multiple studios" / "+ Multiple rooms" with the booking's other studios (rooms) picked - add or take off;
   Move checks each one free. A booking's rooms are now split studio / other studios / booths / holding rooms (a second studio
   was counted as a holding room, so a Change with Holding rooms on the form dropped it). A meeting's first room is its room.
   "Nothing changed" compares the first room, then the rest in any order.
4. **Cards:** a meeting in several rooms reads "Room: Likha + Katha" (not "Holding room: Katha"); a session's studios read
   "Room: Studio 7 + Studio 8" as before.
Built on workflows/imported/slack-interactions-v52-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v52-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b, n=1):
    assert js.count(a) == n, (js.count(a), a[:140])
    return js.replace(a, b)


def code(name):
    return by[name]["parameters"]["jsCode"]


def setc(name, js):
    by[name]["parameters"]["jsCode"] = js


CHANGE_NODES = ["Note Toggle", "Read Change", "Build Change", "Build Change C", "To Move", "After Move"]

# ── 4. card helpers (every copy) ──────────────────────────────────────────────────────────────────────────────────────────
RM_OLD = "function roomMain(r) { const a = roomList(r); return [a[0]].concat(a.slice(1).filter(x => /^(?:Studio\\s|M\\d)/i.test(x))).filter(Boolean).join(' + '); }"
RM_NEW = ("function roomMain(r) { const a = roomList(r); if (a[0] && !/^(?:Studio\\s|M\\d)/i.test(a[0])) return a.join(' + ');   // v53: a meeting in several rooms (\"Likha + Katha\")\n"
          "  return [a[0]].concat(a.slice(1).filter(x => /^(?:Studio\\s|M\\d)/i.test(x))).filter(Boolean).join(' + '); }")
RH_OLD = "function roomHold(r) { return roomList(r).slice(1).filter(x => !/^(?:Studio\\s|M\\d)/i.test(x)).join(', '); }"
RH_NEW = ("function roomHold(r) { const a = roomList(r); if (a[0] && !/^(?:Studio\\s|M\\d)/i.test(a[0])) return '';   // v53: a meeting's rooms are all its rooms\n"
          "  return a.slice(1).filter(x => !/^(?:Studio\\s|M\\d)/i.test(x)).join(', '); }")
n_cards = 0
for n in wf["nodes"]:
    js = n["parameters"].get("jsCode")
    if js and RM_OLD in js:
        js = sub(js, RM_OLD, RM_NEW)
        js = sub(js, RH_OLD, RH_NEW)
        n["parameters"]["jsCode"] = js
        n_cards += 1
assert n_cards == 15, n_cards

# ── 2. vocal booths on Book (boothBlocks - every copy) ────────────────────────────────────────────────────────────────────
BB_OLD = ("  const opts = list.slice(0, 99).map(n => ({ text: pt(n + (n === usual ? ' (usual)' : '')), value: n })).concat(BX.need ? [] : [{ text: { type: 'plain_text', text: 'No booth' }, value: 'none' }]);   // v39: \"No booth\" back - a phone shows no \"Clear selection\"\n"
          "  const el = Object.assign({ type: 'static_select', action_id: 'booth_pick', placeholder: pt(BX.need ? 'Select a booth' : 'No booth'), options: opts }, { initial_option: BX.need ? opts[0] : opts[opts.length - 1] });   // v39: \"No booth\" picked\n"
          "  return [{ type: 'input', block_id: bid, label: pt('Vocal booth'), element: el }];   // v39: required (no Slack \"Clear selection\"), \"No booth\" picked\n")
BB_NEW = ("  // v53 (Howard, 28 Oct): several vocal booths - a multi-select; the usual booth preset when the session needs one (then at least\n"
          "  // one - a required field), else empty = no booth (a picked booth can be removed on a phone too, so no \"No booth\" item). The\n"
          "  // engineer / arranger dropdowns stay v39's: required (no Slack \"Clear selection\"), \"No …\" picked - a phone shows no clear line\n"
          "  const opts = list.slice(0, 100).map(n => ({ text: pt(n + (n === usual ? ' (usual)' : '')), value: n }));\n"
          "  const el = Object.assign({ type: 'multi_static_select', action_id: 'booth_pick', placeholder: pt(BX.need ? 'Select a booth' : 'No booth'), options: opts }, BX.need ? { initial_options: [opts[0]] } : {});\n"
          "  return [Object.assign({ type: 'input', block_id: bid, label: pt('Vocal booths'), element: el }, BX.need ? {} : { optional: true })];\n")
for nm in ["Build Step 1", "Build Step 2", "Note Toggle"]:
    setc(nm, sub(code(nm), BB_OLD, BB_NEW))

# ── 1. Book a room, step 2: + Multiple studios / rooms ────────────────────────────────────────────────────────────────────
js = code("Build Step 2")
js = sub(js, "  blocks.push({ type: 'divider' });\n  // v24: the details each kind of booking needs",
    "  // v53 (Howard, 28 Oct): one project in several studios is ONE booking - every studio on the same calendar event. Meetings and\n"
    "  // events: several rooms. The other rooms of that kind free then (every date of a series); not for Van Recording, Atmos, Post\n"
    "  // Processing (one room each) or M booths. Read Step 2 adds them after the first room.\n"
    "  const MORE = ra.status === 'OK' && !ONLY && ini && (s.kind === 'studio' || s.kind === 'loc' || s.kind === 'meeting')\n"
    "    ? (data.rooms || []).map(_nm).filter((n, i, a) => n && a.indexOf(n) === i && sameKind(n) && !busyAny.has(n) && (s.kind === 'meeting' || kindOfRoom(n) === 'studio'))\n"
    "        .sort((x, y) => (s.kind === 'meeting' ? (kindOfRoom(x) === 'common' ? 0 : 1) - (kindOfRoom(y) === 'common' ? 0 : 1) : 0) || _num(x, y)) : [];\n"
    "  if (MORE.length > 1) blocks.push({ type: 'input', block_id: 'more_rooms', optional: true, label: { type: 'plain_text', text: s.kind === 'meeting' ? '+ Multiple rooms' : '+ Multiple studios' },\n"
    "    element: { type: 'multi_static_select', action_id: 'more_rooms_pick', placeholder: { type: 'plain_text', text: s.kind === 'meeting' ? 'Select more rooms' : 'Select more studios' },\n"
    "      options: MORE.slice(0, 100).map(n => opt(n, n)) } });\n"
    "  blocks.push({ type: 'divider' });\n  // v24: the details each kind of booking needs")
setc("Build Step 2", js)

js = code("Read Step 2")
js = sub(js, "const booth = (b0 => b0 === 'none' ? '' : b0)(valA('booth_pick'));   // v25: a dropdown, \"No booth\"\n",
    "// v53: the vocal booths - a multi-select (an older form still open: one booth, or \"No booth\")\n"
    "const valsA = a => { for (const k of Object.keys(v)) { const x = (v[k] || {})[a]; if (x && Array.isArray(x.selected_options)) return x.selected_options.map(o => o.value).filter(Boolean);\n"
    "  if (x && x.selected_option && x.selected_option.value) return [x.selected_option.value]; } return []; };\n"
    "const booths = valsA('booth_pick').filter(b => b && b !== 'none' && b !== room);\n"
    "const booth = booths[0] || '';\n")
js = sub(js, "const roomsAll = [room].concat(booth && booth !== room ? [booth] : []).concat(holding.filter(h => h && h !== room && h !== booth)).filter(Boolean);\n",
    "// v53 (Howard, 28 Oct): + Multiple studios / rooms - on the same booking, after the first room (one event, every room on it)\n"
    "const moreRooms = (((v.more_rooms || {}).more_rooms_pick || {}).selected_options || []).map(o => o.value).filter(x => x && x !== room && booths.indexOf(x) === -1);\n"
    "const roomsAll = [room].concat(moreRooms, booths, holding.filter(h => h && h !== room && booths.indexOf(h) === -1 && moreRooms.indexOf(h) === -1)).filter((x, i, a) => x && a.indexOf(x) === i);\n")
js = sub(js, "if (s.kind === 'meeting' && !title) errors.title = 'Give the meeting a title.';\n",
    "if (s.kind === 'meeting' && !title) errors.title = 'Give the meeting a title.';\n"
    "if (askK && moreRooms.length) errors.more_rooms = 'A request is for one room - pick a free room to book several, or send the request on its own.';   // v53\n")
js = sub(js, "if ([].concat(s.others || []).indexOf(room) !== -1) notUsual = true;   // v19: another room, booked as asked\n",
    "if ([].concat(s.others || []).indexOf(room) !== -1) notUsual = true;   // v19: another room, booked as asked\n"
    "// v53: an added studio / room that is not one of the type's usual rooms is booked as asked, like Choose a different room - only\n"
    "// when the type has a room ranking (Book Session checks rooms only then; room_override also skips a standing hold)\n"
    "try { const _st = (data.sessionTypes || []).find(r => String((r.fields || {}).Type || '').trim() === s.purpose), _f = (_st || {}).fields || {}, _nmr = {};\n"
    "  for (const r of data.rooms || []) _nmr[r.id] = String((r.fields || {})['Room Name'] || '').trim();\n"
    "  const _pri = [].concat(_f.Priority || []).map(id => _nmr[id]).filter(Boolean), _lst = [].concat(_f['Last Resort'] || []).map(id => _nmr[id]).filter(Boolean);\n"
    "  if ((_pri.length || _lst.length) && moreRooms.some(x => _pri.indexOf(x) === -1)) notUsual = true; } catch (e) {}\n")
setc("Read Step 2", js)

# ── 3. Change: room split, + Multiple studios / rooms, vocal booths ───────────────────────────────────────────────────────
RP_OLD = ("function roomParts(r, rooms) {\n"
          "  const all = (rooms && rooms.all) || [], cn = x => { const v = roomName(x); return all.find(a => a.toLowerCase() === v.toLowerCase()) || v; };\n"
          "  const list = String(r || '').split(',').map(x => cn(x.trim())).filter(Boolean);\n"
          "  const isC = n => ((rooms && rooms.common) || []).indexOf(n) !== -1, isB = n => ((rooms && rooms.vb) || []).indexOf(n) !== -1;\n"
          "  const studio = list.find(n => !isC(n) && !isB(n)) || list[0] || '';\n"
          "  return { studio, booths: list.filter(n => n !== studio && isB(n)), holds: list.filter(n => n !== studio && !isB(n)) };\n"
          "}\n"
          "function orderRooms(r, rooms) { const P = roomParts(r, rooms); return [P.studio].concat(P.booths, P.holds).filter(Boolean).join(', '); }")
RP_NEW = ("// v53: + the other studios (a second studio was counted as a holding room); a meeting's first room is its room (meet)\n"
          "function roomParts(r, rooms, meet) {\n"
          "  const all = (rooms && rooms.all) || [], cn = x => { const v = roomName(x); return all.find(a => a.toLowerCase() === v.toLowerCase()) || v; };\n"
          "  const list = String(r || '').split(',').map(x => cn(x.trim())).filter(Boolean);\n"
          "  const isC = n => ((rooms && rooms.common) || []).indexOf(n) !== -1, isB = n => ((rooms && rooms.vb) || []).indexOf(n) !== -1;\n"
          "  const isS = n => !isC(n) && !isB(n) && !/^M[1-8]$/.test(n) && all.indexOf(n) !== -1;\n"
          "  const studio = meet ? (list[0] || '') : (list.find(n => !isC(n) && !isB(n)) || list[0] || '');\n"
          "  const rest = list.filter(n => n !== studio);\n"
          "  return { studio, studios: rest.filter(isS), booths: rest.filter(isB), holds: rest.filter(n => !isB(n) && !isS(n)) };\n"
          "}\n"
          "function orderRooms(r, rooms, meet) { const P = roomParts(r, rooms, meet); return [P.studio].concat(P.studios, P.booths, P.holds).filter(Boolean).join(', '); }")
PB_SIG_OLD = "function pairBlocksC(T, data, rooms, RP, pickB, pickH) {"
PB_SIG_NEW = "function pairBlocksC(T, data, rooms, RP, pickB, pickH, pickM, meet) {   // v53: pickM / meet - + Multiple studios / rooms"
BNOW_OLD = "  const bNow = pickB != null ? pickB : (RP.booths[0] || ''), hNow = pickH != null ? pickH : RP.holds;"
BNOW_NEW = "  const bNow = pickB != null ? [].concat(pickB) : RP.booths, hNow = pickH != null ? pickH : RP.holds;   // v53: the booths (several)"
BOOTH_C_OLD = ("  if ((off.booth || RP.booths.length) && bo.length) { const bi = bo.find(o => o.value === bNow);   // v26: optional, empty = no booth\n"
               "    out.push({ type: 'input', block_id: 'booth_c', label: pt('Vocal booth'), element: Object.assign({ type: 'static_select', action_id: 'booth_c_pick', placeholder: pt('No booth'), options: bo.concat([{ text: { type: 'plain_text', text: 'No booth' }, value: 'none' }]) }, { initial_option: bi || { text: { type: 'plain_text', text: 'No booth' }, value: 'none' } }) }); }   // v39: required, \"No booth\" picked   // v39: \"No booth\" back\n")
BOOTH_C_NEW = ("  if (!meet && (off.booth || RP.booths.length) && bo.length) { const bi = bo.filter(o => bNow.indexOf(o.value) !== -1);   // v53: several booths, empty = no booth\n"
               "    out.push({ type: 'input', block_id: 'booth_c', optional: true, label: pt('Vocal booths'), element: Object.assign({ type: 'multi_static_select', action_id: 'booth_c_pick', placeholder: pt('No booth'), options: bo }, bi.length ? { initial_options: bi } : {}) }); }\n")
HOLD_C_OLD = "  if ((off.hold || RP.holds.length) && ho.length) { const hi = ho.filter(o => [].concat(hNow || []).indexOf(o.value) !== -1);   // v25: a dropdown\n"
HOLD_C_NEW = "  if (!meet && (off.hold || RP.holds.length) && ho.length) { const hi = ho.filter(o => [].concat(hNow || []).indexOf(o.value) !== -1);   // v25: a dropdown (v53: a meeting's rooms below)\n"
PB_END_OLD = "hi.length ? { initial_options: hi } : {}) }); }\n  return out; }"
PB_END_NEW = ("hi.length ? { initial_options: hi } : {}) }); }\n"
              "  // v53 (Howard, 28 Oct): one booking in several studios (a meeting / event: several rooms) - one calendar event, every room on\n"
              "  // it; added or taken off here (Move checks each one free). Not for Van Recording, Atmos or Post Processing (one room each).\n"
              "  const K = typeKind(T), more = meet ? 'rooms' : ((K === 'studio' || K === 'loc') && !onlyRoom(T)) ? 'studios' : '';\n"
              "  const isS = n => [].concat(rooms.common || []).indexOf(n) === -1 && [].concat(rooms.vb || []).indexOf(n) === -1 && !/^M[1-8]$/.test(n);\n"
              "  const mNow = pickM != null ? [].concat(pickM) : (meet ? RP.studios.concat(RP.holds) : RP.studios);\n"
              "  const pool = (meet ? sortN([].concat(rooms.common || [])) : []).concat(sortN([].concat(rooms.all || []).filter(isS))).concat(mNow)\n"
              "    .filter((n, i, a) => n && a.indexOf(n) === i && n !== RP.studio && (mNow.indexOf(n) !== -1 || roomAllowed(n, T)));\n"
              "  if ((more || mNow.length) && pool.length) { const mo = pool.slice(0, 100).map(n => ({ text: pt(n), value: n })), mi = mo.filter(o => mNow.indexOf(o.value) !== -1);\n"
              "    out.push({ type: 'input', block_id: meet ? 'rooms_c' : 'studios_c', optional: true, label: pt(meet ? '+ Multiple rooms' : '+ Multiple studios'),\n"
              "      element: Object.assign({ type: 'multi_static_select', action_id: 'more_c_pick', placeholder: pt(meet ? 'Select more rooms' : 'Select more studios'), options: mo }, mi.length ? { initial_options: mi } : {}) }); }\n"
              "  return out; }")
CV_OLD = "  const RP = roomParts(cur.r || b.r, rooms), PB = kind(br) === 'studio' ? pairBlocksC(T0, det && det.data, rooms, RP, null, null) : [], multi = PB.length > 0;   // v30"
CV_NEW = ("  const meetC = kind(br) === 'common' || typeKind(T0) === 'meeting';   // v53: a meeting / event - + Multiple rooms\n"
          "  const RP = roomParts(cur.r || b.r, rooms, meetC), PB = (kind(br) === 'studio' || meetC) ? pairBlocksC(T0, det && det.data, rooms, RP, null, null, null, meetC) : [],\n"
          "    multi = PB.some(x => x.block_id === 'booth_c' || x.block_id === 'holding_c');   // v30; v53: the Studio label as before")
for nm in CHANGE_NODES:
    js = code(nm)
    js = sub(js, RP_OLD, RP_NEW)
    js = sub(js, PB_SIG_OLD, PB_SIG_NEW)
    js = sub(js, BNOW_OLD, BNOW_NEW)
    js = sub(js, BOOTH_C_OLD, BOOTH_C_NEW)
    js = sub(js, HOLD_C_OLD, HOLD_C_NEW)
    js = sub(js, PB_END_OLD, PB_END_NEW)
    js = sub(js, CV_OLD, CV_NEW)
    setc(nm, js)

for nm in ["Build Change", "Build Change C"]:
    setc(nm, sub(code(nm), "if (data && b.r) { b.r = orderRooms(b.r, roomLists(data));",
        "if (data && b.r) { b.r = orderRooms(b.r, roomLists(data), parseTitle(b).kind === 'meeting' || typeKind(b.st || '') === 'meeting');   // v53: a meeting's first room stays first\n "))

js = code("Read Change")
js = sub(js, "const RL = roomLists(data), P0 = roomParts(b.r, RL);\nconst bsel = sel('booth_c', 'booth_c_pick');\n",
    "const meet0 = O.kind === 'meeting' || typeKind(b.st || '') === 'meeting';   // v53: a meeting / event - its first room is its room\n"
    "const RL = roomLists(data), P0 = roomParts(b.r, RL, meet0);\n"
    "// v53: the vocal booths (a multi-select; an older form still open: one booth or \"No booth\") and + Multiple studios / rooms\n"
    "const multiOf = (bl, a) => { const x = (v[bl] || {})[a] || {}; return Array.isArray(x.selected_options) ? x.selected_options.map(o => o.value).filter(y => y && y !== 'none')\n"
    "  : (x.selected_option && x.selected_option.value && x.selected_option.value !== 'none' ? [x.selected_option.value] : []); };\n"
    "const bsels = v.booth_c ? multiOf('booth_c', 'booth_c_pick') : P0.booths;\n"
    "const msel = v.rooms_c ? multiOf('rooms_c', 'more_c_pick') : v.studios_c ? multiOf('studios_c', 'more_c_pick') : (meet0 ? P0.studios.concat(P0.holds) : P0.studios);\n")
js = sub(js, "const newRooms = [canonRoom(n.r, RL)].concat(v.booth_c ? (bsel && bsel !== 'none' ? [bsel] : []) : P0.booths, hsel).filter((x, i, a) => x && a.indexOf(x) === i);\n"
             "const oldRooms = [P0.studio].concat(P0.booths, P0.holds).filter(Boolean);\n"
             "const roomChanged = newRooms.join('|').toLowerCase() !== oldRooms.join('|').toLowerCase();",
    "const newRooms = [canonRoom(n.r, RL)].concat(msel, bsels, meet0 ? [] : hsel).filter((x, i, a) => x && a.indexOf(x) === i);\n"
    "const oldRooms = [P0.studio].concat(P0.studios, P0.booths, P0.holds).filter((x, i, a) => x && a.indexOf(x) === i);\n"
    "const _rk = a => [String(a[0] || '')].concat(a.slice(1).map(String).sort()).join('|').toLowerCase();   // v53: the first room, then the rest in any order\n"
    "const roomChanged = _rk(newRooms) !== _rk(oldRooms);")
setc("Read Change", js)

js = code("Note Toggle")
js = sub(js, "    const pickB = st.booth_c ? ((((st.booth_c || {}).booth_c_pick || {}).selected_option || {}).value || '') : null;\n",
    "    const _ms = x => x ? (Array.isArray(x.selected_options) ? x.selected_options.map(o => o.value) : (x.selected_option && x.selected_option.value ? [x.selected_option.value] : [])).filter(y => y && y !== 'none') : null;   // v53\n"
    "    const pickB = st.booth_c ? _ms((st.booth_c || {}).booth_c_pick) : null;\n"
    "    const pickM = st.studios_c ? _ms((st.studios_c || {}).more_c_pick) : st.rooms_c ? _ms((st.rooms_c || {}).more_c_pick) : null, meetP = typeKind(keep.st) === 'meeting';   // v53\n")
js = sub(js, "    for (let k = blocks.length - 1; k >= 0; k--) if (blocks[k].block_id === 'booth_c' || blocks[k].block_id === 'holding_c') blocks.splice(k, 1);\n",
    "    for (let k = blocks.length - 1; k >= 0; k--) if (['booth_c', 'holding_c', 'studios_c', 'rooms_c'].indexOf(blocks[k].block_id) !== -1) blocks.splice(k, 1);   // v53: + Multiple studios / rooms\n")
js = sub(js, "...pairBlocksC(keep.st, D9, RLp, roomParts(String(bb.r || ''), RLp), pickB, pickH));",
    "...pairBlocksC(keep.st, D9, RLp, roomParts(String(bb.r || ''), RLp, meetP), pickB, pickH, pickM, meetP));")
setc("Note Toggle", js)

wf["name"] = "Jessie — Slack Interactions — v53 (multiple studios)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v53.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes;", n_cards, "card helpers")
