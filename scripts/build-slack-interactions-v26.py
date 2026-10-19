#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v26.json - "Jessie — Slack Interactions", v26: round 9 (Howard's notes on round 8, 19 Oct).

  1. The year on long dates: the Booking… window ("Tuesday, October 19, 2027"), "Your booking details:" on the message, and
     step 2's header ("Wednesday, Oct 20, 2027 · …"). List rows stay short.
  2. No "Not a usual room …" anywhere in the forms (the hint under the other-room dropdown, the room list's labels).
  3. No usual room free -> the list is "Available rooms:" with "The usual rooms for this type of booking are not available in
     your chosen schedule" under it (the rooms are still booked as asked).
  4. Studio E only for Post Processing - like Studio M for Van Recording (one rule: roomAllowed).
  5. Vocal booth, Engineer (where an arranger also counts) and Arranger: optional, no "No …" options; empty reads "No booth" /
     "No engineer" / "No arranger" (the placeholder - Slack's own clearing line then reads "--No booth--"). Book and Change.
  6. No "Engineer and arranger: pick one or both." (the rule stays: neither -> "Pick an engineer or an arranger.").
  7. "Recommended rooms:" (Localization Dubbing: "Recommended studios:") with no "Recommended" line - the top one ticked;
     "Another room" -> "Choose a different room".
  8. At most 6 rooms in the list; the other free ones under "Choose a different room".
Built on workflows/imported/slack-interactions-v25-imported.json (the live download). With main v276 and Book Session v113.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v25-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v26.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:100], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


def everywhere(a, b, want=None):
    hit = 0
    for n in wf["nodes"]:
        js = n["parameters"].get("jsCode")
        if js and a in js:
            n["parameters"]["jsCode"] = js.replace(a, b)
            hit += 1
    assert want is None or hit == want, (a[:80], hit, want)
    return hit


# ---- 4: one rule for the rooms that belong to one booking type -------------------------------------------------------
everywhere("function cap1(x) {",
           "// v26: rooms that belong to one booking type - Studio M (the van) to Van Recording, Studio E to Post Processing (19 Oct)\n"
           "function roomAllowed(n, t) { const X = { 'studio m': 'van recording', 'studio e': 'post processing' }; const k = String(n || '').trim().toLowerCase();\n"
           "  return !X[k] || X[k] === String(t || '').trim().toLowerCase(); }\n"
           "function cap1(x) {", want=8)

# ---- 5: the booth dropdown - optional, no "No booth", empty reads "No booth" ------------------------------------------
everywhere("""  const opts = (BX.need ? [] : [{ text: pt('No booth'), value: 'none' }]).concat(list.slice(0, 99).map(n => ({ text: pt(n + (n === usual ? ' (usual)' : '')), value: n })));
  const el = Object.assign({ type: 'static_select', action_id: 'booth_pick', placeholder: pt('Select a booth'), options: opts }, BX.need ? { initial_option: opts[0] } : {});""",
           """  const opts = list.slice(0, 100).map(n => ({ text: pt(n + (n === usual ? ' (usual)' : '')), value: n }));   // v26: no "No booth" - empty is no booth
  const el = Object.assign({ type: 'static_select', action_id: 'booth_pick', placeholder: pt(BX.need ? 'Select a booth' : 'No booth'), options: opts }, BX.need ? { initial_option: opts[0] } : {});""",
           want=3)

# ---- step 2 ------------------------------------------------------------------------------------------------------------
patch("Build Step 2", [
    # 1: the year in the header
    ("const when = DOW[dt.getUTCDay()] + ', ' + MON[dt.getUTCMonth()] + ' ' + dt.getUTCDate() + ' · '",
     "const when = DOW[dt.getUTCDay()] + ', ' + MON[dt.getUTCMonth()] + ' ' + dt.getUTCDate() + ', ' + dt.getUTCFullYear() + ' · '"),
    # 4
    ("const noM = n => ONLY === 'Studio M' || n !== 'Studio M';   // v25: Studio M (the van) is only for Van Recording",
     "const noM = n => roomAllowed(n, s.purpose);   // v25: Studio M only for Van Recording; v26: Studio E only for Post Processing"),
    # 7 / 3: no descriptions on the list; the top one ticked
    ("  if (free) rooms = [opt(ONLY, ONLY, 'Recommended')]; else note = ONLY + ' is taken then - pick another date or time.';",
     "  if (free) rooms = [opt(ONLY, ONLY)]; else note = ONLY + ' is taken then - pick another date or time.';"),
    ("  rooms = pri.map((r, i) => i === 0 ? opt(r, r, 'Recommended') : opt(r, r));\n"
     "  if (!rooms.length) { rooms = last.map((r, i) => i === 0 ? opt(r, r, 'Not a usual room for ' + rmLabel) : opt(r, r)); nu.push(...last); }",
     "  rooms = pri.map(r => opt(r, r));   // v26: no \"Recommended\" line - the list's label says it, the top one is ticked\n"
     "  if (!rooms.length) { rooms = last.map(r => opt(r, r)); nu.push(...last); }   // v26: said once above the list (noUsual)"),
    ("    preRoom = opt(pre.r, pre.r, 'Not a usual room for ' + rmLabel); rooms.unshift(preRoom); nu.push(pre.r); }",
     "    preRoom = opt(pre.r, pre.r); rooms.unshift(preRoom); nu.push(pre.r); }"),
    ("  else if (sameKind(pre.r) && !busyAny.has(pre.r)) { preRoom = opt(pre.r, pre.r, 'Not a usual room for ' + rmLabel); rooms.unshift(preRoom); nu.push(pre.r);",
     "  else if (sameKind(pre.r) && !busyAny.has(pre.r)) { preRoom = opt(pre.r, pre.r); rooms.unshift(preRoom); nu.push(pre.r);"),
    # 8: at most 6 in the list
    ("  if (i !== -1) { preRoom = rooms[i]; if (i >= 10) { rooms.splice(i, 1); rooms.unshift(preRoom); } }",
     "  if (i !== -1) { preRoom = rooms[i]; if (i >= 6) { rooms.splice(i, 1); rooms.unshift(preRoom); } }   // v26: the list holds 6"),
    ("rooms = rooms.slice(0, 10);", "rooms = rooms.slice(0, 6);   // v26: at most 6 in the list - the other free ones under Choose a different room"),
    # 7: series descriptions only say what the label cannot
    ("    const d = o.description ? o.description.text + ' · ' + tail : (k >= N ? '' : tail);",
     "    const d = k >= N ? '' : tail;   // v26: only \"free on k of N dates\""),
    # 7 / 3 / 2: the labels; the line when no usual room is free; no hint under the other-room dropdown
    ("  blocks.push({ type: 'section', block_id: 'room_label', text: md('*' + (needBooth ? 'Studio' : 'Room') + '*') },",
     "  // v26: \"Recommended rooms:\" (studios for Localization Dubbing); none of the usual ones free -> \"Available rooms:\" and why\n"
     "  const noUsual = s.kind !== 'booth' && !ONLY && nu.length > 0 && rooms.every(o => nu.indexOf(o.value) !== -1);\n"
     "  blocks.push({ type: 'section', block_id: 'room_label', text: md('*' + (noUsual ? 'Available rooms:' : needBooth ? 'Recommended studios:' : 'Recommended rooms:') + '*') },\n"
     "    ...(noUsual ? [{ type: 'context', block_id: 'room_why', elements: [md('The usual rooms for this type of booking are not available in your chosen schedule')] }] : []),"),
    ("  if (others.length) blocks.push({ type: 'input', block_id: 'room_other', optional: true, dispatch_action: true, label: { type: 'plain_text', text: 'Another room' },\n"
     "    hint: { type: 'plain_text', text: ('Not a usual room for ' + rmLabel + '.').slice(0, 150) },\n",
     "  if (others.length) blocks.push({ type: 'input', block_id: 'room_other', optional: true, dispatch_action: true, label: { type: 'plain_text', text: 'Choose a different room' },   // v26: no hint\n"),
    # 5 / 6: engineer and arranger - no "No …" options, empty reads "No engineer" / "No arranger"; no "pick one or both"
    ("  const engEl = { type: 'static_select', action_id: 'engineer_pick', placeholder: { type: 'plain_text', text: 'Select an engineer' }, options: (RR.either ? [NONE_E] : []).concat(engOrder.slice(0, RR.either ? 99 : 100).map(popt)) };",
     "  const engEl = { type: 'static_select', action_id: 'engineer_pick', placeholder: { type: 'plain_text', text: RR.either ? 'No engineer' : 'Select an engineer' }, options: engOrder.slice(0, 100).map(popt) };   // v26: no \"No engineer\""),
    ("  const arrEl = { type: 'static_select', action_id: 'arranger_pick', placeholder: { type: 'plain_text', text: 'Select an arranger' }, options: [NONE_A].concat(arrs.slice(0, 99).map(popt)) };",
     "  const arrEl = { type: 'static_select', action_id: 'arranger_pick', placeholder: { type: 'plain_text', text: 'No arranger' }, options: arrs.slice(0, 100).map(popt) };   // v26: no \"No arranger\""),
    ("  const team = [].concat(RR.either ? [{ type: 'context', block_id: 'team_note', elements: [md('Engineer and arranger: pick one or both.')] }] : [])\n    .concat(RR.eng || !RR.known ? [engineer] : [])",
     "  // v26: no \"pick one or both\" line\n  const team = [].concat(RR.eng || !RR.known ? [engineer] : [])"),
])

# ---- Read Step 2: the year in the Booking… window --------------------------------------------------------------------
patch("Read Step 2", [("         return DL[x.getUTCDay()] + ', ' + ML[x.getUTCMonth()] + ' ' + x.getUTCDate() + '\\n' + (s.allDay ? 'All day' : t(s.t0) + ' – ' + t(s.t1)); })() } },",
                       "         return DL[x.getUTCDay()] + ', ' + ML[x.getUTCMonth()] + ' ' + x.getUTCDate() + ', ' + x.getUTCFullYear() + '\\n' + (s.allDay ? 'All day' : t(s.t0) + ' – ' + t(s.t1)); })() } },   // v26: the year")])
# "Your booking details:" with the year
everywhere("+ ['January','February','March','April','May','June','July','August','September','October','November','December'][x.getUTCMonth()] + ' ' + x.getUTCDate(); }",
           "+ ['January','February','March','April','May','June','July','August','September','October','November','December'][x.getUTCMonth()] + ' ' + x.getUTCDate() + ', ' + x.getUTCFullYear(); }   // v26: the year",
           want=4)

# ---- the Change form --------------------------------------------------------------------------------------------------
everywhere("""    .filter(n => only ? n === only : n !== 'Studio M');""",
           """    .filter(n => only ? n === only : roomAllowed(n, T0));   // v26: Studio E only for Post Processing too""", want=5)
everywhere("""    if (RP.booths.length) { const bo = [{ text: pt('No booth'), value: 'none' }].concat(sortN([].concat(rooms.vb || [])).map(n => ({ text: pt(n), value: n })));
      blocks.push({ type: 'input', block_id: 'booth_c', label: pt('Vocal booth'), element: { type: 'static_select', action_id: 'booth_c_pick', placeholder: pt('Select a booth'), options: bo.slice(0, 100),
        initial_option: bo.find(o => o.value === RP.booths[0]) || bo[0] } }); }""",
           """    if (RP.booths.length) { const bo = sortN([].concat(rooms.vb || [])).map(n => ({ text: pt(n), value: n }));   // v26: optional, empty = no booth
      const bi = bo.find(o => o.value === RP.booths[0]);
      blocks.push({ type: 'input', block_id: 'booth_c', optional: true, label: pt('Vocal booth'), element: Object.assign({ type: 'static_select', action_id: 'booth_c_pick', placeholder: pt('No booth'), options: bo.slice(0, 100) }, bi ? { initial_option: bi } : {}) }); }""",
           want=5)
everywhere("""  const engs = (R.either ? [{ text: pt('No engineer'), value: 'none' }] : []).concat(st.filter(x => /\\bengineer\\b/i.test(x.info)).sort((x, y) => x.name.localeCompare(y.name)).slice(0, R.either ? 99 : 100).map(popt));
  const arrs = [{ text: pt('No arranger'), value: 'none' }].concat(st.filter(x => /\\barranger\\b/i.test(x.info)).sort((x, y) => x.name.localeCompare(y.name)).slice(0, 99).map(popt));   // a picked dropdown cannot be emptied""",
           """  const engs = st.filter(x => /\\bengineer\\b/i.test(x.info)).sort((x, y) => x.name.localeCompare(y.name)).slice(0, 100).map(popt);   // v26: no "No engineer" / "No arranger" -
  const arrs = st.filter(x => /\\barranger\\b/i.test(x.info)).sort((x, y) => x.name.localeCompare(y.name)).slice(0, 100).map(popt);    // an optional dropdown empties itself""",
           want=5)
everywhere("""  const engIn = opt => inp('det_engineer', 'Engineer', sel('det_engineer_pick', engs, V.en, 'Select an engineer'), opt);""",
           """  const engIn = opt => inp('det_engineer', 'Engineer', sel('det_engineer_pick', engs, V.en, opt ? 'No engineer' : 'Select an engineer'), opt);""", want=5)
everywhere("""  if (R.either) out.push({ type: 'context', block_id: 'team_note', elements: [{ type: 'mrkdwn', text: 'Engineer and arranger: pick one or both.' }] });
""", "", want=5)
everywhere("""  if (R.arr) out.push(inp('det_arranger', 'Arranger', sel('det_arranger_pick', arrs, V.ar, 'Select an arranger'), true));""",
           """  if (R.arr) out.push(inp('det_arranger', 'Arranger', sel('det_arranger_pick', arrs, V.ar, 'No arranger'), true));""", want=5)

# ---- the older redraws (a v24 / v25 form still open) say the same ------------------------------------------------------
everywhere("hint: pt(('Not a usual room for ' + (meta.label || 'this') + '.').slice(0, 150)),", "", want=1)
everywhere("hint: pt(('Not a usual room for ' + (M2.label || 'this') + ' - booked as asked.').slice(0, 150)),", "", want=1)
everywhere("{ type: 'input', block_id: 'room_other', label: pt('Another room'),", "{ type: 'input', block_id: 'room_other', label: pt('Choose a different room'),", want=1)

wf["name"] = "Jessie — Slack Interactions — v26 (round 9: rooms, dropdowns, dates)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
