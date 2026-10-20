#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v30.json - "Jessie — Slack Interactions", v30 (round 12: form fixes), 20 Oct.

  2. Change form: **Vocal booth** and **Holding rooms** whenever the booking type offers them on Book (Build Step 2's rules:
     a booth for studio "...Recording" types and Localization types needing one; holding rooms when the type's Room
     Requirements mention holding / conference - Celebrity Recording), not only when the booking already has one. Empty by
     default ("No booth"). Changing "What's it for?" on the form adds / removes them (picks kept). Read Change already reads
     both whenever they are on the form; Move checks the added rooms are free.
  3. Project code (Book step 2 and Change): a plain text box - no Enter, so Slack's "Press 'enter' to submit" is gone. The
     Enter used to show the project's line and preset the engineer from Localization Projects; the engineer is now picked.
  4. Post Processing: **Booker** is a dropdown (everyone in Bookers), set to the person booking - was fixed text "Dylan Diaz".
     The Change form's "Booker: Dylan Diaz" line is a dropdown too, set to the booking's booker (its title initials). A form
     opened before the import still books as Dylan. A new Post Processing booker is not sent an engineer notice.
  5. Repeats: "How often?" with Weekly / Weekdays / Daily (labels only - the values stay weekly / weekdays / daily).
Built on workflows/imported/slack-interactions-v29-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "slack-interactions-v29-imported.json")
OUT = os.path.join(ROOT, "workflows", "slack-interactions-v30.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
CHANGE = ["Build Change", "Read Change", "To Move", "After Move", "Note Toggle"]   # the five copies of changeView / detBlocks


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:100], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


def patch_all(nodes, pairs):
    for n in nodes:
        patch(n, pairs)


# ---- 2: Vocal booth / Holding rooms on the Change form ------------------------------------------------------------------
PAIR_JS = r"""// v30 (round 12, Howard 20 Oct): the Change form offers a Vocal booth / Holding rooms whenever the booking type offers them
// on Book (Build Step 2's rules), not only when the booking already has one; empty = none
function pairOfferC(T, data) { const K = typeKind(T); if (K !== 'studio' && K !== 'loc') return { booth: false, hold: false };
  const ST = ((data && data.sessionTypes) || []).find(r => String((r.fields || {}).Type || '').trim().toLowerCase() === String(T || '').trim().toLowerCase());
  const req = String(((ST || {}).fields || {})['Room Requirements'] || '');
  const need = K === 'loc' && /vocal booth/i.test(req);
  return { booth: need || (K === 'studio' && /recording/i.test(String(T || '')) && !onlyRoom(T)), hold: K === 'studio' && /holding|conference/i.test(req) }; }
function pairBlocksC(T, data, rooms, RP, pickB, pickH) {
  const pt = x => ({ type: 'plain_text', text: x }), off = pairOfferC(T, data), out = [];
  const sortN = a => a.slice().sort((x, y) => x.localeCompare(y, 'en', { numeric: true }));
  const bNow = pickB != null ? pickB : (RP.booths[0] || ''), hNow = pickH != null ? pickH : RP.holds;
  const bo = sortN([].concat(rooms.vb || [])).map(n => ({ text: pt(n), value: n })).slice(0, 100);
  if ((off.booth || RP.booths.length) && bo.length) { const bi = bo.find(o => o.value === bNow);   // v26: optional, empty = no booth
    out.push({ type: 'input', block_id: 'booth_c', optional: true, label: pt('Vocal booth'), element: Object.assign({ type: 'static_select', action_id: 'booth_c_pick', placeholder: pt('No booth'), options: bo }, bi ? { initial_option: bi } : {}) }); }
  const ho = sortN([].concat(rooms.common || []).filter(n => !/^lobby$/i.test(n))).map(n => ({ text: pt(n), value: n })).slice(0, 10);
  if ((off.hold || RP.holds.length) && ho.length) { const hi = ho.filter(o => [].concat(hNow || []).indexOf(o.value) !== -1);   // v25: a dropdown
    out.push({ type: 'input', block_id: 'holding_c', optional: true, label: pt('Holding rooms'), element: Object.assign({ type: 'multi_static_select', action_id: 'holding_c_pick', placeholder: pt('Select holding rooms'), options: ho }, hi.length ? { initial_options: hi } : {}) }); }
  return out; }
"""
OLD_MULTI = """  const RP = roomParts(cur.r || b.r, rooms), multi = RP.booths.length > 0 || RP.holds.length > 0;"""
NEW_MULTI = """  const RP = roomParts(cur.r || b.r, rooms), PB = kind(br) === 'studio' ? pairBlocksC(T0, det && det.data, rooms, RP, null, null) : [], multi = PB.length > 0;   // v30"""
OLD_PAIR = """  if (multi && kind(br) === 'studio') {
    const sortN = a => a.slice().sort((x, y) => x.localeCompare(y, 'en', { numeric: true }));
    if (RP.booths.length) { const bo = sortN([].concat(rooms.vb || [])).map(n => ({ text: pt(n), value: n }));   // v26: optional, empty = no booth
      const bi = bo.find(o => o.value === RP.booths[0]);
      blocks.push({ type: 'input', block_id: 'booth_c', optional: true, label: pt('Vocal booth'), element: Object.assign({ type: 'static_select', action_id: 'booth_c_pick', placeholder: pt('No booth'), options: bo.slice(0, 100) }, bi ? { initial_option: bi } : {}) }); }
    if (RP.holds.length) { const ho = sortN([].concat(rooms.common || []).filter(n => !/^lobby$/i.test(n))).map(n => ({ text: pt(n), value: n })).slice(0, 10);
      const hi = ho.filter(o => RP.holds.indexOf(o.value) !== -1);
      blocks.push({ type: 'input', block_id: 'holding_c', optional: true, label: pt('Holding rooms'), element: Object.assign({ type: 'multi_static_select', action_id: 'holding_c_pick', placeholder: pt('Select holding rooms'), options: ho }, hi.length ? { initial_options: hi } : {}) }); }   // v25: a dropdown
  }"""
NEW_PAIR = """  if (PB.length) blocks.push(...PB);   // v30: the booth / holding rooms the booking type offers (pairBlocksC)"""
for n in CHANGE:
    patch(n, [("function changeView(b, cur, warn, meta, rooms, det) {", PAIR_JS + "function changeView(b, cur, warn, meta, rooms, det) {"),
              (OLD_MULTI, NEW_MULTI), (OLD_PAIR, NEW_PAIR)])
patch("Note Toggle", [(
    "    blocks.splice(ai === -1 ? blocks.length : ai + 1, 0, ...detBlocks(M2.b || {}, D9, keep));\n  }",
    "    blocks.splice(ai === -1 ? blocks.length : ai + 1, 0, ...detBlocks(M2.b || {}, D9, keep));\n"
    "    // v30 (round 12): the Vocal booth / Holding rooms follow the type picked (picks kept)\n"
    "    const RLp = roomLists(D9), bb = M2.b || {};\n"
    "    const pickB = st.booth_c ? ((((st.booth_c || {}).booth_c_pick || {}).selected_option || {}).value || '') : null;\n"
    "    const pickH = st.holding_c ? ((((st.holding_c || {}).holding_c_pick || {}).selected_options) || []).map(o => o.value) : null;\n"
    "    for (let k = blocks.length - 1; k >= 0; k--) if (blocks[k].block_id === 'booth_c' || blocks[k].block_id === 'holding_c') blocks.splice(k, 1);\n"
    "    const ri = blocks.findIndex(x => x.block_id === 'room');\n"
    "    if (ri !== -1 && keep.st) blocks.splice(ri + 1, 0, ...pairBlocksC(keep.st, D9, RLp, roomParts(String(bb.r || ''), RLp), pickB, pickH));\n"
    "  }")])

# ---- 3: the project code is a plain text box ---------------------------------------------------------------------------
patch("Build Step 2", [("blocks.push(input('code', 'Project code', txtIn('code_in', cd, { dispatch_action_config: { trigger_actions_on: ['on_enter_pressed'] } }), { dispatch_action: true }));",
                        "blocks.push(input('code', 'Project code', txtIn('code_in', cd)));   // v30: no Enter (Slack's \"Press 'enter' to submit\")")])
patch_all(CHANGE, [("return [Object.assign(inp('det_code', 'Project code', txt('det_code_in', code, { dispatch_action_config: { trigger_actions_on: ['on_enter_pressed'] } })), { dispatch_action: true }),",
                    "return [inp('det_code', 'Project code', txt('det_code_in', code)),   // v30: no Enter")])

# ---- 4: Post Processing's booker is a dropdown ------------------------------------------------------------------------
patch("Build Step 2", [
    ("const POST_BOOKER = 'Dylan Diaz';   // v21: Post Processing's booker (Howard 15 Oct: Dilan, for now)",
     "// v30 (round 12): Post Processing's Booker is a dropdown set to the person booking (v21-v29: fixed text, Dylan Diaz)"),
    ("""  } else if (s.kind === 'post') {   // v21: Post Processing - the booker is set, a project title, no client
    blocks.push({ type: 'section', block_id: 'booker', text: md('*Booker*\\n' + POST_BOOKER) },
      input('project', 'Project title', txtIn('project_in', pre.pj)), notes);""",
     """  } else if (s.kind === 'post') {   // v21: Post Processing - a project title, no client; v30: Booker is a dropdown (everyone in Bookers)
    const bks = people.slice().sort((a, b) => a.name.localeCompare(b.name)), meB = bks.find(p => p.slack === (pre.en || s.requester));
    const bopts = (meB && bks.indexOf(meB) >= 100 ? [meB].concat(bks.filter(p => p !== meB)) : bks).slice(0, 100).map(popt);
    const bIni = meB ? bopts.find(o => o.value === meB.slack) : null;
    blocks.push(input('booker', 'Booker', Object.assign({ type: 'static_select', action_id: 'booker_pick', placeholder: { type: 'plain_text', text: 'Select a booker' }, options: bopts }, bIni ? { initial_option: bIni } : {})),
      input('project', 'Project title', txtIn('project_in', pre.pj)), notes);"""),
])
patch("Read Step 2", [(
    "if (s.kind === 'post') { const pb = (data.bookers || []).map(b => b.fields || {}).find(f => String(f.Name || '').trim() === 'Dylan Diaz');   // v21\n"
    "  engineerId = pb ? String(pb['Slack User ID'] || '').split(/[\\s,]+/).filter(Boolean)[0] || '' : '';\n"
    "  if (!engineerId) errors.project = errors.project || 'Dylan Diaz isn’t in Bookers yet - ask for the booker to be added.'; }",
    "if (s.kind === 'post' && val('booker', 'booker_pick')) engineerId = val('booker', 'booker_pick');   // v30: the Booker picked\n"
    "else if (s.kind === 'post') { const pb = (data.bookers || []).map(b => b.fields || {}).find(f => String(f.Name || '').trim() === 'Dylan Diaz');   // v21 (a form opened before v30)\n"
    "  engineerId = pb ? String(pb['Slack User ID'] || '').split(/[\\s,]+/).filter(Boolean)[0] || '' : '';\n"
    "  if (!engineerId) errors.project = errors.project || 'Dylan Diaz isn’t in Bookers yet - ask for the booker to be added.'; }")])
patch_all(CHANGE, [(
    "  if (K === 'post') return [inp('det_project', 'Project title', txt('det_project_in', V.project)),\n"
    "    { type: 'context', block_id: 'det_booker', elements: [{ type: 'mrkdwn', text: 'Booker: Dylan Diaz' }] }, notes];",
    "  if (K === 'post') { const bks = st.slice().sort((x, y) => x.name.localeCompare(y.name)).slice(0, 100).map(popt);   // v30: Booker is a dropdown,\n"
    "    const dyl = st.find(x => x.name === 'Dylan Diaz');                                                                     // set to the booking's booker\n"
    "    return [inp('det_project', 'Project title', txt('det_project_in', V.project)), inp('det_engineer', 'Booker', sel('det_engineer_pick', bks, V.en || (dyl ? dyl.slack : ''), 'Select a booker')), notes]; }")])
patch_all(CHANGE, [("K === 'post' ? '' : String(d.client != null ? d.client : (O.client || '')).trim(), K === 'post' ? (O.ei || ei) : inits].filter(Boolean).join(' / ');",
                    "K === 'post' ? '' : String(d.client != null ? d.client : (O.client || '')).trim(), K === 'post' ? (ei || O.ei) : inits].filter(Boolean).join(' / ');   // v30: the Booker picked")])
patch("Read Change", [(
    "const newDetails0 = teamChanged ? { Engineer: d.en === 'none' ? '' : nm(d.en), Arranger: d.ar && d.ar !== 'none' ? nm(d.ar) : '', team: [d.en === 'none' ? '' : d.en, d.ar && d.ar !== 'none' ? d.ar : ''].filter(Boolean).join(' ') } : null;",
    "const newDetails0 = teamChanged ? { Engineer: d.en === 'none' ? '' : nm(d.en), Arranger: d.ar && d.ar !== 'none' ? nm(d.ar) : '',\n"
    "  team: typeKind(d.st || b.st || '') === 'post' ? '' : [d.en === 'none' ? '' : d.en, d.ar && d.ar !== 'none' ? d.ar : ''].filter(Boolean).join(' ') } : null;   // v30: a Post Processing booker gets no engineer notice")])

# ---- 5: Repeats wording -------------------------------------------------------------------------------------------------
for n in ["Build Step 1", "Note Toggle"]:
    patch(n, [("label: pt('How often'), element:", "label: pt('How often?'), element:"),
              ("const freq = [{ text: pt('Every week'), value: 'weekly' }, { text: pt('Every weekday (Mon–Fri)'), value: 'weekdays' }, { text: pt('Every day'), value: 'daily' }];",
               "const freq = [{ text: pt('Weekly'), value: 'weekly' }, { text: pt('Weekdays'), value: 'weekdays' }, { text: pt('Daily'), value: 'daily' }];   // v30: shorter labels, same values")])

wf["name"] = "Jessie — Slack Interactions — v30 (round 12: form fixes)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
