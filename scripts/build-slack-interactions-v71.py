#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v71.json - Jessie — Slack Interactions — v71 (one engineer + a tick), 6 Nov.

Howard's phone test of v70 (6 Nov 4:16 PM): a multi-select with one pick reads "1 selected" on iPhone, not the name. Decided: "usually,
only one engineer is booked. so let's revert to using only one selection for engineer. but add a small tick underneath that, which will
open a multi-select for additional engineers. for arrangers, keep it multi-select. for music session types, just have the single select
engineer."
- Book a room (step 2) and Change: Engineer is one dropdown again (its name shows on a phone); under it "Add more engineers" - ticked,
  a "More engineers" multi-select opens below (Note Toggle draws it from the engineer list; unticked, it goes). Not for Music types
  (an arranger role or "music" / "band" in the name) and not Localization: the one dropdown only.
- A saved / typed list ("U1,U5") opens with the first as the engineer, the box ticked and the rest picked.
- Read Step 2 / Read Change join the engineer and the extras into the same comma list v70 uses (title "HL AEG", "Engineer: A, B",
  team: everyone) - nothing else changes downstream.
- Arranger stays a multi-select; its "Picked:" line shows from one pick (a phone shows "1 selected").
Built on workflows/imported/slack-interactions-v70-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v70-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}
CHANGE_NODES = ("Build Change", "Read Change", "To Move", "After Move", "Note Toggle", "Build Change C")


def sub(js, a, b, n=1):
    assert js.count(a) == n, (js.count(a), a[:160])
    return js.replace(a, b)


def code(name, f):
    p = by[name]["parameters"]
    p["jsCode"] = f(p["jsCode"])


OLD_LIST = "'booth_pick', 'more_rooms_pick', 'holding_pick', 'booth_c_pick', 'holding_c_pick', 'more_c_pick'"
V70_ACT = "'engineer_pick', 'arranger_pick', 'det_engineer_pick', 'det_arranger_pick'"
V71_ADD = "'more_eng_pick', 'more_eng_c_pick'"

# ---- the Picked: line: + the extra engineers; arrangers from one pick
for name in ("Build Step 2",) + CHANGE_NODES:
    def f(js):
        js = sub(js, "const ACT = [" + OLD_LIST + ", " + V70_ACT + "];", "const ACT = [" + OLD_LIST + ", " + V70_ACT + ", " + V71_ADD + "];")
        js = sub(js, "    if (os.length >= 2) bl.splice(i + 1, 0,",
                 "    if (os.length >= (/arranger_/.test(String(e.action_id)) ? 1 : 2)) bl.splice(i + 1, 0,   /* v71: an arranger from one pick (a phone shows \"1 selected\") */")
        return js
    code(name, f)
code("Check Signature", lambda js: sub(js, OLD_LIST + ", " + V70_ACT + "].indexOf(action) !== -1) route = ROUTES.note_toggle;",
    OLD_LIST + ", " + V70_ACT + ", " + V71_ADD + ", 'more_eng_toggle', 'more_eng_c_toggle'].indexOf(action) !== -1) route = ROUTES.note_toggle;   // v71: the tick"))

# ---- Note Toggle: the tick opens / closes "More engineers"; its picks get the Picked: line
TICK = r"""// v71 (Howard, 6 Nov): "Add more engineers" ticked -> a "More engineers" multi-select under it, from the engineer list (not the one
// picked); unticked -> it goes. Nothing else on the form moves.
if (a.action_id === 'more_eng_toggle' || a.action_id === 'more_eng_c_toggle') {
  const _c = a.action_id === 'more_eng_c_toggle', _bl = JSON.parse(JSON.stringify(V.blocks || []));
  for (let i = _bl.length - 1; i >= 0; i--) if (/^(?:more_eng|det_more_eng)(?:_picked)?$/.test(String((_bl[i] || {}).block_id || ''))) _bl.splice(i, 1);
  const _ti = _bl.findIndex(b => b.block_id === a.action_id);
  if ((a.selected_options || []).length && _ti !== -1) {
    const _eb = _bl.find(b => b.block_id === (_c ? 'det_engineer' : 'engineer')) || {}, _ek = _c ? 'det_engineer_pick' : 'engineer_pick';
    const _main = ((((st[_c ? 'det_engineer' : 'engineer'] || {})[_ek] || {}).selected_option) || ((_eb.element || {}).initial_option) || {}).value || '';
    const _os = ((_eb.element || {}).options || []).filter(o => o.value !== 'none' && o.value !== _main).slice(0, 100);
    _bl.splice(_ti + 1, 0, { type: 'input', block_id: _c ? 'det_more_eng' : 'more_eng', optional: true, dispatch_action: true, label: { type: 'plain_text', text: 'More engineers' },
      element: { type: 'multi_static_select', action_id: _c ? 'more_eng_c_pick' : 'more_eng_pick', placeholder: { type: 'plain_text', text: 'Select engineers' }, options: _os } });
  }
  const _v = { type: 'modal', callback_id: V.callback_id || 'book_step2', title: V.title, close: V.close, private_metadata: V.private_metadata || '', blocks: _bl };
  if (V.submit) _v.submit = V.submit;
  return [{ json: { view_id: V.id || '', hash: V.hash || '', view: _v, ok: !!V.id } }];
}
"""
code("Note Toggle", lambda js: sub(sub(js, "// v64: a multi-select changed - nothing else on the form moves",
    TICK + "// v64: a multi-select changed - nothing else on the form moves"),
    "if ([" + OLD_LIST + ", " + V70_ACT + "].indexOf(a.action_id) !== -1) {", "if ([" + OLD_LIST + ", " + V70_ACT + ", " + V71_ADD + "].indexOf(a.action_id) !== -1) {"))

# ---- step 2: one engineer + the tick
def bs2(js):
    js = sub(js, "    toMulti(engineer, engEl, _pre(pre.en).length > 1 ? _pre(pre.en) : [], RR.either ? 'No engineer' : 'Select engineers', RR.either);\n",
             "    // v71: the engineer stays one dropdown (a phone shows its name) - extra engineers under the tick below\n")
    js = sub(js, "typed = engs.find(p => p.slack === pre.en)", "typed = engs.find(p => p.slack === String(pre.en || '').split(',')[0].trim())   /* v71: the first of a list */")
    js = sub(js, "  if (arrFirst(data, s.purpose)) team = team.slice().reverse();   // v33: Music - the Arranger first\n",
        "  if (arrFirst(data, s.purpose)) team = team.slice().reverse();   // v33: Music - the Arranger first\n"
        "  // v71 (Howard, 6 Nov): extra engineers behind \"Add more engineers\" - not Localization, not Music (one engineer there)\n"
        "  if (s.kind !== 'loc' && !(RR.arr || /music|band/i.test(String(s.purpose || ''))) && team.indexOf(engineer) !== -1) {\n"
        "    const _x = String(pre.en || '').split(',').map(x => x.trim()).filter(x => x && x !== 'none').slice(1);\n"
        "    const _tick = { type: 'actions', block_id: 'more_eng_toggle', elements: [{ type: 'checkboxes', action_id: 'more_eng_toggle', options: [{ text: { type: 'plain_text', text: 'Add more engineers' }, value: 'more' }] }] };\n"
        "    const _bl = [_tick];\n"
        "    if (_x.length) { _tick.elements[0].initial_options = _tick.elements[0].options;\n"
        "      const os = engOrder.slice(0, 99).map(popt).filter(o => o.value !== String(pre.en || '').split(',')[0].trim()), io = os.filter(o => _x.indexOf(o.value) !== -1);\n"
        "      _bl.push({ type: 'input', block_id: 'more_eng', optional: true, dispatch_action: true, label: { type: 'plain_text', text: 'More engineers' },\n"
        "        element: Object.assign({ type: 'multi_static_select', action_id: 'more_eng_pick', placeholder: { type: 'plain_text', text: 'Select engineers' }, options: os }, io.length ? { initial_options: io } : {}) }); }\n"
        "    team.splice(team.indexOf(engineer) + 1, 0, ..._bl);\n"
        "  }\n")
    return js
code("Build Step 2", bs2)

# ---- Read Step 2: the engineer + the extras, one comma list (as v70)
code("Read Step 2", lambda js: sub(js, "let engineerId = engPick === 'none' ? '' : engPick;",
    "let engineerId = engPick === 'none' ? '' : engPick;\n"
    "{ const _x = __mv('more_eng', 'more_eng_pick'); if (_x) engineerId = [engineerId].concat(_x.split(',')).map(x => String(x || '').trim()).filter((x, i, a) => x && a.indexOf(x) === i).join(','); }   // v71: the extras (the tick)"))

# ---- the Change form (six copies of the helper): one engineer + the tick
ENGIN_V70 = ("const engIn = opt => K === 'loc' ? inp('det_engineer', 'Engineer', sel('det_engineer_pick', opt ? engs.concat([{ text: { type: 'plain_text', text: 'No engineer' }, value: 'none' }]) : engs, "
             "opt ? (V.en || 'none') : V.en, opt ? 'No engineer' : 'Select an engineer'), false)\n"
             "    : inp('det_engineer', 'Engineer', msel('det_engineer_pick', engs, V.en, opt ? 'No engineer' : 'Select engineers'), !!opt)   /* v70: several */")
ENGIN_V71 = ("const _en0 = String(V.en || '').split(',')[0].trim();   // v71: one engineer - the first of a list; the rest under the tick\n"
             "  const engIn = opt => inp('det_engineer', 'Engineer', sel('det_engineer_pick', opt ? engs.concat([{ text: { type: 'plain_text', text: 'No engineer' }, value: 'none' }]) : engs, "
             "opt ? (_en0 || 'none') : _en0, opt ? 'No engineer' : 'Select an engineer'), false)")
TEAM_TAIL = "  out.push(...(arrFirst(data, T) ? _team.slice().reverse() : _team));   // v33: Music - the Arranger first"
TICK_C = ("  // v71 (Howard, 6 Nov): extra engineers behind \"Add more engineers\" - not Localization, not Music\n"
          "  if (K !== 'loc' && !(R.arr || /music|band/i.test(String(T || '')))) { const _ei = _team.findIndex(b => b.block_id === 'det_engineer');\n"
          "    const _x = String(V.en || '').split(',').map(x => x.trim()).filter(x => x && x !== 'none').slice(1);\n"
          "    const _tick = { type: 'actions', block_id: 'more_eng_c_toggle', elements: [{ type: 'checkboxes', action_id: 'more_eng_c_toggle', options: [{ text: pt('Add more engineers'), value: 'more' }] }] };\n"
          "    const _bl = [_tick];\n"
          "    if (_x.length) { _tick.elements[0].initial_options = _tick.elements[0].options;\n"
          "      _bl.push(inp('det_more_eng', 'More engineers', msel('more_eng_c_pick', engs.filter(o => o.value !== _en0), _x.join(','), 'Select engineers'), true)); }\n"
          "    if (_ei !== -1) _team.splice(_ei + 1, 0, ..._bl); }\n")
for name in CHANGE_NODES:
    def f(js):
        js = sub(js, ENGIN_V70, ENGIN_V71)
        js = sub(js, TEAM_TAIL, TICK_C + TEAM_TAIL)
        return js
    code(name, f)

# ---- Read Change: the engineer + the extras
code("Read Change", lambda js: sub(js, "en: sel('det_engineer', 'det_engineer_pick') || pmsel('det_engineer', 'det_engineer_pick'),",
    "en: (function () { const m = sel('det_engineer', 'det_engineer_pick'), x = pmsel('det_more_eng', 'more_eng_c_pick');   // v71: + the extras (the tick)\n"
    "          const l = [m].concat(x.split(',')).map(y => String(y || '').trim()).filter((y, i, a) => y && y !== 'none' && a.indexOf(y) === i); return l.length ? l.join(',') : m; })(),"))

wf["name"] = "Jessie — Slack Interactions — v71 (one engineer + a tick)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v71.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
