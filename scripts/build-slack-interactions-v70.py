#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v70.json - Jessie — Slack Interactions — v70 (several engineers), 6 Nov.

Howard, 6 Nov: "make all engineers and arrangers in dropdowns multi-select ... if engineers are Howard and Eli for a VO Recording
session, it should be 'HL AEG'" - decided: "HL AEG x MV", every engineer / arranger told, Localization stays one engineer.
- Book a room (step 2) and Change: Engineer and Arranger are multi-selects outside Localization (a cleared field is none - no
  "No engineer" option needed, a phone can clear a multi-select); pre-filled as before; "Picked: …" under two or more (v64).
- Several people travel as a comma list in the same fields (engineerId "U1,U2", d.en, the form's again / prefill), so one
  engineer is exactly as before; the name / initials helpers read lists: the title "HL AEG x MV", "Engineer: Howard Luistro,
  Elijah Gan", team: every id.
- Booked and Change notices go to each engineer / arranger; Series Notices and My bookings read the names as a list.
With Book Session v128 (resolves every name, the title check takes "HL AEG x MV"), Reminders v10, Open Consent Request v15 and
Request Messages v7 (the Engineer line read as a list).
Built on workflows/imported/slack-interactions-v69-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v69-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}
CHANGE_NODES = ("Build Change", "Read Change", "To Move", "After Move", "Note Toggle", "Build Change C")


def sub(js, a, b, n=1):
    assert js.count(a) == n, (js.count(a), a[:160])
    return js.replace(a, b)


def code(name, f):
    p = by[name]["parameters"]
    p["jsCode"] = f(p["jsCode"])


NEW_ACT = ("'engineer_pick', 'arranger_pick', 'det_engineer_pick', 'det_arranger_pick'")
OLD_LIST = "'booth_pick', 'more_rooms_pick', 'holding_pick', 'booth_c_pick', 'holding_c_pick', 'more_c_pick'"

# ---- the Picked: line and the routing for the new multi-selects
for name in ("Build Step 2",) + CHANGE_NODES:
    code(name, lambda js: sub(js, "const ACT = [" + OLD_LIST + "];", "const ACT = [" + OLD_LIST + ", " + NEW_ACT + "];   // v70: + people"))
code("Check Signature", lambda js: sub(js, OLD_LIST + "].indexOf(action) !== -1) route = ROUTES.note_toggle;",
    OLD_LIST + ", " + NEW_ACT + "].indexOf(action) !== -1) route = ROUTES.note_toggle;   // v70: + the people multi-selects"))
code("Note Toggle", lambda js: sub(js, "if ([" + OLD_LIST + "].indexOf(a.action_id) !== -1) {",
    "if ([" + OLD_LIST + ", " + NEW_ACT + "].indexOf(a.action_id) !== -1) {   // v70"))

# ---- step 2: Engineer / Arranger as multi-selects (not Localization)
code("Build Step 2", lambda js: sub(js,
    "  const arranger = arrs.length ? input('arranger', 'Arranger', arrEl, {}) : null;   // v33: required when it is the only role\n",
    "  const arranger = arrs.length ? input('arranger', 'Arranger', arrEl, {}) : null;   // v33: required when it is the only role\n"
    "  // v70 (Howard, 6 Nov): several engineers / arrangers - multi-selects (cleared = none); Localization keeps one engineer\n"
    "  if (s.kind !== 'loc') {\n"
    "    const _pre = x => String(x || '').split(',').map(y => y.trim()).filter(y => y && y !== 'none');\n"
    "    const toMulti = (blk, el, ids, ph, opt) => { if (!blk) return; const os = (el.options || []).filter(o => o.value !== 'none');\n"
    "      const ini = ids.length ? os.filter(o => ids.indexOf(o.value) !== -1) : (el.initial_option && el.initial_option.value !== 'none' ? os.filter(o => o.value === el.initial_option.value) : []);\n"
    "      blk.element = Object.assign({ type: 'multi_static_select', action_id: el.action_id, placeholder: { type: 'plain_text', text: ph }, options: os }, ini.length ? { initial_options: ini } : {});\n"
    "      blk.dispatch_action = true; if (opt) blk.optional = true; else delete blk.optional; };\n"
    "    toMulti(engineer, engEl, _pre(pre.en).length > 1 ? _pre(pre.en) : [], RR.either ? 'No engineer' : 'Select engineers', RR.either);\n"
    "    toMulti(arranger, arrEl, _pre(pre.ar).length > 1 ? _pre(pre.ar) : [], 'No arranger', !(RR.known && RR.arr && !RR.eng));\n"
    "  }\n"))

# ---- Read Step 2: lists in the same fields
def rs2(js):
    js = sub(js, "const engPick = val('engineer', 'engineer_pick');",
        "// v70: a multi-select sends selected_options - kept as a comma list in the same fields (one person: as before)\n"
        "const __mv = (b, a) => ((v[b] && v[b][a] && v[b][a].selected_options) || []).map(o => o.value).filter(x => x && x !== 'none').join(',');\n"
        "const engPick = val('engineer', 'engineer_pick') || __mv('engineer', 'engineer_pick');")
    js = sub(js, "const arrPick = val('arranger', 'arranger_pick');", "const arrPick = val('arranger', 'arranger_pick') || __mv('arranger', 'arranger_pick');")
    js = sub(js, "const nm = id => { const f = who(id); return f ? String(f.Name || '').trim() : ''; };",
        "const nm = id => String(id || '').split(',').map(x => { const f = who(x.trim()); return f ? String(f.Name || '').trim() : ''; }).filter(Boolean).join(', ');   // v70: lists")
    js = sub(js, "const ini = id => { const f = who(id); return f ? String(f.Initials || '').trim() : ''; };",
        "const ini = id => String(id || '').split(',').map(x => { const f = who(x.trim()); return f ? String(f.Initials || '').trim() : ''; }).filter(Boolean).join(' ');   // v70: \"HL AEG\"")
    js = sub(js, "if (engineerId && !who(engineerId)) errors.engineer =", "if (engineerId && String(engineerId).split(',').some(x => !who(x.trim()))) errors.engineer =")
    js = sub(js, "else if (engineerId) { const r = ofPerson(engineerId);", "else if (engineerId) { const r = ofPerson(String(engineerId).split(',')[0]);")
    js = sub(js, "const team = s.kind === 'post' ? '' : [engineerId, arrangerId, forId].filter((x, k, a) => x && a.indexOf(x) === k).join(' ');",
        "const team = s.kind === 'post' ? '' : [].concat(String(engineerId || '').split(','), String(arrangerId || '').split(','), [forId]).map(x => String(x || '').trim()).filter((x, k, a) => x && a.indexOf(x) === k).join(' ');   // v70: everyone")
    return js
code("Read Step 2", rs2)

# ---- Booked Notices: each engineer / arranger
code("Booked Notices", lambda js: sub(js,
    "return notices([Object.assign({ id: R.engineerId, role: 'engineer', verb: 'booked', name: whoIs(data, R.engineerId) }, R.s.kind === 'post' ? { line: 'booked this for you' } : {}),   // v36: Post Processing's Who is it for?\n"
    "                { id: R.arrangerId, role: 'arranger', verb: 'booked', name: whoIs(data, R.arrangerId) },\n"
    "                { id: R.forId, line: 'booked this for you', name: whoIs(data, R.forId) }], me, whoIs(data, me) || 'Someone', body, bk);",
    "const _ids = x => String(x || '').split(',').map(y => y.trim()).filter(Boolean);   // v70: several engineers / arrangers\n"
    "return notices([].concat(_ids(R.engineerId).map(id => Object.assign({ id, role: 'engineer', verb: 'booked', name: whoIs(data, id) }, R.s.kind === 'post' ? { line: 'booked this for you' } : {})),   // v36: Post Processing's Who is it for?\n"
    "                _ids(R.arrangerId).map(id => ({ id, role: 'arranger', verb: 'booked', name: whoIs(data, id) })),\n"
    "                [{ id: R.forId, line: 'booked this for you', name: whoIs(data, R.forId) }]), me, whoIs(data, me) || 'Someone', body, bk);"))

# ---- the Change form (the helper is in six nodes)
DETORIG_OLD = ("function detOrig(b, data) { const P = parseTitle(b), st = staffOf(data), e = byIni(st, P.ei), a = byIni(st, P.ai);\n"
               "  return Object.assign({}, P, { en: P.kind === 'post' ? oneBooker(data, P.name) : (e ? e.slack : ''), ar: a ? a.slack : (P.kind === 'studio' ? 'none' : '') }); }")
DETORIG_NEW = ("function detOrig(b, data) { const P = parseTitle(b), st = staffOf(data);\n"
               "  const _ids = s => String(s || '').trim().split(/\\s+/).map(x => byIni(st, x)).filter(Boolean).map(x => x.slack).join(',');   // v70: \"HL AEG\" -> both\n"
               "  return Object.assign({}, P, { en: P.kind === 'post' ? oneBooker(data, P.name) : _ids(P.ei), ar: _ids(P.ai) || (P.kind === 'studio' ? 'none' : '') }); }")
MSEL = ("  // v70: several engineers / arrangers (not Localization) - a multi-select, its picks from a comma list (no \"none\")\n"
        "  const msel = (aid, opts, val, ph) => { const w = String(val || '').split(',').map(x => x.trim()).filter(x => x && x !== 'none'), os = opts.filter(x => x.value !== 'none');\n"
        "    const io = os.filter(x => w.indexOf(x.value) !== -1); return Object.assign({ type: 'multi_static_select', action_id: aid, placeholder: pt(ph), options: os }, io.length ? { initial_options: io } : {}); };\n")
ENGIN_OLD = ("const engIn = opt => inp('det_engineer', 'Engineer', sel('det_engineer_pick', opt ? engs.concat([{ text: { type: 'plain_text', text: 'No engineer' }, value: 'none' }]) : engs, "
             "opt ? (V.en || 'none') : V.en, opt ? 'No engineer' : 'Select an engineer'), false)")
ENGIN_NEW = ("const engIn = opt => K === 'loc' ? inp('det_engineer', 'Engineer', sel('det_engineer_pick', opt ? engs.concat([{ text: { type: 'plain_text', text: 'No engineer' }, value: 'none' }]) : engs, "
             "opt ? (V.en || 'none') : V.en, opt ? 'No engineer' : 'Select an engineer'), false)\n"
             "    : inp('det_engineer', 'Engineer', msel('det_engineer_pick', engs, V.en, opt ? 'No engineer' : 'Select engineers'), !!opt)   /* v70: several */")
ARR_OLD = ("inp('det_arranger', 'Arranger', sel('det_arranger_pick', arrs.concat([{ text: { type: 'plain_text', text: 'No arranger' }, value: 'none' }]), V.ar || 'none', 'No arranger'), false)")
ARR_NEW = ("(K === 'loc' ? " + ARR_OLD + " : inp('det_arranger', 'Arranger', msel('det_arranger_pick', arrs, V.ar, 'No arranger'), true))   /* v70: several */")
INP_OLD = "const inp = (bid, label, el, opt) => Object.assign({ type: 'input', block_id: bid, label: pt(label), element: el }, opt ? { optional: true } : {});"
INP_NEW = ("const inp = (bid, label, el, opt) => Object.assign({ type: 'input', block_id: bid, label: pt(label), element: el }, opt ? { optional: true } : {},\n"
           "    el && el.type === 'multi_static_select' ? { dispatch_action: true } : {});   // v70: a multi-select names its picks (Picked:)")
INI_OLD = "ini = id => { const x = st.find(y => y.slack === id); return x ? x.ini : ''; };"
INI_NEW = "ini = id => String(id || '').split(',').map(z => { const x = st.find(y => y.slack === z.trim()); return x ? x.ini : ''; }).filter(Boolean).join(' ');   // v70: \"HL AEG\""
for name in CHANGE_NODES:
    def f(js):
        js = sub(js, DETORIG_OLD, DETORIG_NEW)
        js = sub(js, "(listable(x) || x.slack === V.en)", "(listable(x) || String(V.en || '').split(',').indexOf(x.slack) !== -1)")
        js = sub(js, "(listable(x) || x.slack === V.ar)", "(listable(x) || String(V.ar || '').split(',').indexOf(x.slack) !== -1)")
        js = sub(js, "  const sel = (aid, opts, val, ph) => {", MSEL + "  const sel = (aid, opts, val, ph) => {")
        js = sub(js, ENGIN_OLD, ENGIN_NEW)
        js = sub(js, ARR_OLD, ARR_NEW)
        js = sub(js, INP_OLD, INP_NEW)
        js = sub(js, INI_OLD, INI_NEW)
        return js
    code(name, f)

# ---- Read Change: the picks as lists; names, team, who was on it
def rc(js):
    js = sub(js, "const sel = (bl, a) => (v[bl] && v[bl][a] && v[bl][a].selected_option && v[bl][a].selected_option.value) || '';",
        "const sel = (bl, a) => (v[bl] && v[bl][a] && v[bl][a].selected_option && v[bl][a].selected_option.value) || '';\n"
        "const pmsel = (bl, a) => ((v[bl] && v[bl][a] && v[bl][a].selected_options) || []).map(o => o.value).filter(x => x && x !== 'none').join(',');   // v70: the people multi-selects")
    js = sub(js, "en: sel('det_engineer', 'det_engineer_pick'), ar: sel('det_arranger', 'det_arranger_pick') || (O.kind === 'studio' ? 'none' : '') };",
        "en: sel('det_engineer', 'det_engineer_pick') || pmsel('det_engineer', 'det_engineer_pick'),\n"
        "        ar: sel('det_arranger', 'det_arranger_pick') || pmsel('det_arranger', 'det_arranger_pick') || (O.kind === 'studio' ? 'none' : '') };   // v70: lists")
    js = sub(js, "nm = id => { const x = st.find(y => y.slack === id); return x ? x.name : ''; };",
        "nm = id => String(id || '').split(',').map(z => { const x = st.find(y => y.slack === z.trim()); return x ? x.name : ''; }).filter(Boolean).join(', ');   // v70")
    js = sub(js, "[d.en === 'none' ? '' : d.en, d.ar && d.ar !== 'none' ? d.ar : ''].filter(Boolean).join(' '),",
        "[d.en === 'none' ? '' : d.en, d.ar && d.ar !== 'none' ? d.ar : ''].filter(Boolean).join(' ').replace(/,/g, ' '),   // v70: every id")
    js = sub(js, "teamWas: [O.en, O.ar].filter(x => x && x !== 'none') }", "teamWas: [O.en, O.ar].filter(x => x && x !== 'none').join(',').split(',').filter(Boolean) }")
    js = sub(js, "oldTeam: [O.en, O.ar].filter(x => x && x !== 'none'),", "oldTeam: [O.en, O.ar].filter(x => x && x !== 'none').join(',').split(',').filter(Boolean),   // v70")
    return js
code("Read Change", rc)
code("Change Notices", lambda js: sub(js, "role: id === (R.d || {}).en ? 'engineer' : 'arranger'",
    "role: String((R.d || {}).en || '').split(',').indexOf(id) !== -1 ? 'engineer' : 'arranger'"))

# ---- readers of the Engineer line: a list of names
code("Series Notices", lambda js: sub(js, "if (lc && lc === engName) return", "if (lc && engName.split(/\\s*,\\s*/).indexOf(lc) !== -1) return   /* v70 */"))
code("Render My Bookings", lambda js: sub(sub(js, "(myName && eng === myName)", "(myName && eng.split(/\\s*,\\s*/).indexOf(myName) !== -1)"),
    "(myName && arr === myName)", "(myName && arr.split(/\\s*,\\s*/).indexOf(myName) !== -1)"))

wf["name"] = "Jessie — Slack Interactions — v70 (several engineers)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v70.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
