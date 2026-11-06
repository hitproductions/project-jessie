#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v72.json - Jessie — Slack Interactions — v72 (Multiple studios tick), 6 Nov.

Howard, 6 Nov: "change 'Add more engineers' to 'Multiple engineers'; hide + Multiple studios behind a tickbox as well, 'Multiple
studios'".
- The engineers tick reads "Multiple engineers".
- Book a room (step 2) and Change: "+ Multiple studios" (or "+ Multiple rooms" for a meeting) is now a tick, "Multiple studios" /
  "Multiple rooms"; ticked, a "More studios" / "More rooms" multi-select opens under it (Note Toggle draws it from the list the tick
  carries in its value - "mr:S1,S2,SF" / "mm:Likha,…"); unticked, it goes. Picks already there (a typed "studio 1 and 2", a saved
  form, a booking with several studios) -> ticked and shown. On Change, unticking takes the extra studios off.
Built on workflows/imported/slack-interactions-v71-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v71-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}
CHANGE_NODES = ("Build Change", "Read Change", "To Move", "After Move", "Note Toggle", "Build Change C")


def sub(js, a, b, n=1):
    assert js.count(a) == n, (js.count(a), a[:160])
    return js.replace(a, b)


def code(name, f):
    p = by[name]["parameters"]
    p["jsCode"] = f(p["jsCode"])


ENC = ("const __mrEnc = n => /^Studio [0-9A-Z]$/.test(n) ? 'S' + n.slice(7) : n;   // v72: the tick carries its room list (\"Studio 1\" -> \"S1\")\n")

# ---- "Multiple engineers"
code("Build Step 2", lambda js: sub(js, "text: { type: 'plain_text', text: 'Add more engineers' }", "text: { type: 'plain_text', text: 'Multiple engineers' }"))
for name in CHANGE_NODES:
    code(name, lambda js: sub(js, "text: pt('Add more engineers')", "text: pt('Multiple engineers')"))

# ---- step 2: + Multiple studios behind a tick
code("Build Step 2", lambda js: ENC + sub(js,
    "  if (MORE.length > 1) blocks.push({ type: 'input', dispatch_action: true, block_id: 'more_rooms', optional: true, label: { type: 'plain_text', text: s.kind === 'meeting' ? '+ Multiple rooms' : '+ Multiple studios' },\n"
    "    element: { type: 'multi_static_select', action_id: 'more_rooms_pick', placeholder: { type: 'plain_text', text: s.kind === 'meeting' ? 'Select more rooms' : 'Select more studios' },\n"
    "      options: MORE.slice(0, 100).map(n => opt(n, n)) } });\n"
    "  if (MORE.length > 1) _repick(blocks[blocks.length - 1], 'mr');   // v54\n",
    "  // v72 (Howard, 6 Nov): behind a tick, \"Multiple studios\" / \"Multiple rooms\" - ticked, the list opens (Note Toggle)\n"
    "  if (MORE.length > 1) {\n"
    "    const _mb = { type: 'input', dispatch_action: true, block_id: 'more_rooms', optional: true, label: { type: 'plain_text', text: s.kind === 'meeting' ? 'More rooms' : 'More studios' },\n"
    "      element: { type: 'multi_static_select', action_id: 'more_rooms_pick', placeholder: { type: 'plain_text', text: s.kind === 'meeting' ? 'Select more rooms' : 'Select more studios' },\n"
    "        options: MORE.slice(0, 100).map(n => opt(n, n)) } };\n"
    "    _repick(_mb, 'mr');   // v54\n"
    "    const _val = (s.kind === 'meeting' ? 'mm:' : 'mr:') + MORE.slice(0, 100).map(__mrEnc).join(',');\n"
    "    if (_val.length > 150) blocks.push(_mb);   // too many to carry - the list as before\n"
    "    else { const _tk = { type: 'actions', block_id: 'more_rooms_toggle', elements: [{ type: 'checkboxes', action_id: 'more_rooms_toggle',\n"
    "        options: [{ text: { type: 'plain_text', text: s.kind === 'meeting' ? 'Multiple rooms' : 'Multiple studios' }, value: _val }] }] };\n"
    "      blocks.push(_tk);\n"
    "      if ((_mb.element.initial_options || []).length) { _tk.elements[0].initial_options = _tk.elements[0].options; blocks.push(_mb); } }\n"
    "  }\n"))

# ---- Change: the same tick (pairBlocksC, six copies)
PAIR_HEAD_OLD = ("    out.push({ type: 'input', dispatch_action: true, block_id: meet ? 'rooms_c' : 'studios_c', optional: true, label: pt(meet ? '+ Multiple rooms' : '+ Multiple studios'),")
PAIR_HEAD_NEW = ("    const _mb = ({ type: 'input', dispatch_action: true, block_id: meet ? 'rooms_c' : 'studios_c', optional: true, label: pt(meet ? 'More rooms' : 'More studios'),")
PAIR_TAIL_OLD = ("options: mo }, mi.length ? { initial_options: mi } : {}) }); }\n  pickedLines(out, null, null);")
PAIR_TAIL_NEW = ("options: mo }, mi.length ? { initial_options: mi } : {}) });\n"
                 "    // v72 (Howard, 6 Nov): behind a tick - \"Multiple studios\" / \"Multiple rooms\"; the studios on the booking -> ticked and shown\n"
                 "    const _enc = n => /^Studio [0-9A-Z]$/.test(n) ? 'S' + n.slice(7) : n, _val = (meet ? 'mm:' : 'mr:') + pool.slice(0, 100).map(_enc).join(',');\n"
                 "    if (_val.length > 150) out.push(_mb);\n"
                 "    else { const _tk = { type: 'actions', block_id: 'more_rooms_c_toggle', elements: [{ type: 'checkboxes', action_id: 'more_rooms_c_toggle',\n"
                 "        options: [{ text: pt(meet ? 'Multiple rooms' : 'Multiple studios'), value: _val }] }] };\n"
                 "      out.push(_tk); if (mi.length) { _tk.elements[0].initial_options = _tk.elements[0].options; out.push(_mb); } } }\n"
                 "  pickedLines(out, null, null);")
for name in CHANGE_NODES:
    def f(js):
        js = sub(js, PAIR_HEAD_OLD, PAIR_HEAD_NEW)
        js = sub(js, PAIR_TAIL_OLD, PAIR_TAIL_NEW)
        return js
    code(name, f)

# ---- Read Change: the tick there and unticked = no extra studios (not "keep the booking's")
code("Read Change", lambda js: sub(js,
    "const msel = v.rooms_c ? multiOf('rooms_c', 'more_c_pick') : v.studios_c ? multiOf('studios_c', 'more_c_pick') : (meet0 ? P0.studios.concat(P0.holds) : P0.studios);",
    "const msel = v.rooms_c ? multiOf('rooms_c', 'more_c_pick') : v.studios_c ? multiOf('studios_c', 'more_c_pick')\n"
    "  : (v.more_rooms_c_toggle && !(((v.more_rooms_c_toggle || {}).more_rooms_c_toggle || {}).selected_options || []).length) ? []   // v72: the tick shown and unticked - none\n"
    "  : (meet0 ? P0.studios.concat(P0.holds) : P0.studios);"))

# ---- Note Toggle: the tick opens / closes the list it carries
TICK = r"""// v72 (Howard, 6 Nov): "Multiple studios" / "Multiple rooms" ticked -> the list under it (from the tick's value, "mr:S1,S2,SF");
// unticked -> it goes. Nothing else on the form moves.
if (a.action_id === 'more_rooms_toggle' || a.action_id === 'more_rooms_c_toggle') {
  const _c = a.action_id === 'more_rooms_c_toggle', _bl = JSON.parse(JSON.stringify(V.blocks || []));
  const _gone = _c ? /^(?:studios_c|rooms_c)(?:_picked)?$/ : /^more_rooms(?:_picked)?$/;
  for (let i = _bl.length - 1; i >= 0; i--) if (_gone.test(String((_bl[i] || {}).block_id || ''))) _bl.splice(i, 1);
  const _ti = _bl.findIndex(b => b.block_id === a.action_id), _o = (a.selected_options || [])[0];
  if (_o && _ti !== -1) {
    const _meet = /^mm:/.test(String(_o.value || '')), _dec = x => /^S[0-9A-Z]$/.test(x) ? 'Studio ' + x.slice(1) : x;
    const _rooms = String(_o.value || '').replace(/^m[mr]:/, '').split(',').map(x => x.trim()).filter(Boolean).map(_dec);
    _bl.splice(_ti + 1, 0, { type: 'input', block_id: _c ? (_meet ? 'rooms_c' : 'studios_c') : 'more_rooms', optional: true, dispatch_action: true,
      label: { type: 'plain_text', text: _meet ? 'More rooms' : 'More studios' },
      element: { type: 'multi_static_select', action_id: _c ? 'more_c_pick' : 'more_rooms_pick', placeholder: { type: 'plain_text', text: _meet ? 'Select more rooms' : 'Select more studios' },
        options: _rooms.slice(0, 100).map(n => ({ text: { type: 'plain_text', text: n }, value: n })) } });
  }
  const _v = { type: 'modal', callback_id: V.callback_id || 'book_step2', title: V.title, close: V.close, private_metadata: V.private_metadata || '', blocks: _bl };
  if (V.submit) _v.submit = V.submit;
  return [{ json: { view_id: V.id || '', hash: V.hash || '', view: _v, ok: !!V.id } }];
}
"""
code("Note Toggle", lambda js: sub(js, "// v71 (Howard, 6 Nov): \"Add more engineers\" ticked", TICK + "// v71 (Howard, 6 Nov): \"Add more engineers\" ticked"))
code("Check Signature", lambda js: sub(js, "'more_eng_toggle', 'more_eng_c_toggle'].indexOf(action) !== -1) route = ROUTES.note_toggle;",
    "'more_eng_toggle', 'more_eng_c_toggle', 'more_rooms_toggle', 'more_rooms_c_toggle'].indexOf(action) !== -1) route = ROUTES.note_toggle;   // v72"))

wf["name"] = "Jessie — Slack Interactions — v72 (Multiple studios tick)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v72.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
