#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v64.json - Jessie — Slack Interactions — v64 (Localization feedback), 4 Nov.

The Localization coordinator's first week (3 Nov), as Howard passed it on:
- On a phone, a multi-select with two or more picks shows "2 items". Vocal booths, + Multiple studios / rooms and Holding rooms
  (Book a room and Change) now send an action when changed (dispatch_action), and a line under the field names the picks
  ("Picked: Studio A, Studio E"). The line is also drawn when the form opens with two or more picks, and redrawn from the form's
  state whenever the form is redrawn for another reason (stale lines dropped).
- "You can close this window" during the series date check is gone: that check's answer only shows in the window ("Keep this window
  open - the dates show here."). The room search says the same. Booking, booking a series and Change keep it (each has a DM).
- My bookings: the headline reads "🗓️ *Your bookings:*" then "*Nov 4 – Nov 10*" (the year when it is not this year), and a
  "Jump to a date" picker sits beside Previous / Next 7 days (action my_page_jump - the same route, My Window reads its date).
- Studio E is a vocal booth in Airtable since 3 Nov (paired with a Localization studio). Step 2 and Change still treat it as the
  room itself for Post Processing, so Post Processing keeps Studio E in its room list.
Built on workflows/imported/slack-interactions-v63-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v63-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b, n=1):
    assert js.count(a) == n, (js.count(a), a[:140])
    return js.replace(a, b)


MULTI = ["booth_pick", "more_rooms_pick", "holding_pick", "booth_c_pick", "holding_c_pick", "more_c_pick"]

PICKED = r"""// v64 (Localization, 3 Nov): on a phone a multi-select with several picks reads "2 items" - a line under it names them. From the
// action's own picks (the field just changed), else the form's state (same block_id), else what the field was drawn with.
function pickedLines(bl, stv, act) {
  const ACT = ['booth_pick', 'more_rooms_pick', 'holding_pick', 'booth_c_pick', 'holding_c_pick', 'more_c_pick'];
  for (let i = bl.length - 1; i >= 0; i--) if (/_picked$/.test(String((bl[i] || {}).block_id || ''))) bl.splice(i, 1);
  for (let i = bl.length - 1; i >= 0; i--) {
    const b = bl[i] || {}, e = b.element || {};
    if (b.type !== 'input' || e.type !== 'multi_static_select' || ACT.indexOf(e.action_id) === -1) continue;
    const sv = ((stv || {})[b.block_id] || {})[e.action_id];
    const os = act && act.action_id === e.action_id ? (act.selected_options || [])
      : sv && Array.isArray(sv.selected_options) ? sv.selected_options : (e.initial_options || []);
    if (os.length >= 2) bl.splice(i + 1, 0, { type: 'context', block_id: String(b.block_id || '').split('~')[0] + '_picked',
      elements: [{ type: 'mrkdwn', text: 'Picked: ' + os.map(o => String((o.text && o.text.text) || o.value).replace(/\s*\(usual\)$/, '')).join(', ') }] });
  }
  return bl;
}
"""

# ---- Check Signature: the six multi-selects go to Note Toggle
p = by["Check Signature"]["parameters"]
p["jsCode"] = sub(p["jsCode"], "'room_other_pick', 'code_in', 'det_code_in'].indexOf(action) !== -1) route = ROUTES.note_toggle;",
    "'room_other_pick', 'code_in', 'det_code_in', " + ", ".join("'" + x + "'" for x in MULTI)
    + "].indexOf(action) !== -1) route = ROUTES.note_toggle;   // v64: the multi-selects (Picked: line)")

# ---- dispatch_action on every multi-select input
BOOTH = "return [Object.assign({ type: 'input', block_id: bid, label: pt('Vocal booths'), element: el }, BX.need ? {} : { optional: true })];"
for name in ("Build Step 1", "Build Step 2", "Note Toggle"):
    p = by[name]["parameters"]
    p["jsCode"] = sub(p["jsCode"], BOOTH, BOOTH.replace("{ type: 'input', block_id: bid,", "{ type: 'input', dispatch_action: true, block_id: bid,"))
p = by["Build Step 2"]["parameters"]
p["jsCode"] = sub(p["jsCode"], "{ type: 'input', block_id: 'holding', optional: true, label: { type: 'plain_text', text: 'Holding rooms' },",
    "{ type: 'input', dispatch_action: true, block_id: 'holding', optional: true, label: { type: 'plain_text', text: 'Holding rooms' },")
p["jsCode"] = sub(p["jsCode"], "{ type: 'input', block_id: 'more_rooms', optional: true,", "{ type: 'input', dispatch_action: true, block_id: 'more_rooms', optional: true,")
CHANGE_NODES = ("Build Change", "Read Change", "To Move", "After Move", "Note Toggle", "Build Change C")
for name in CHANGE_NODES:
    p = by[name]["parameters"]
    js = p["jsCode"]
    for bid in ("block_id: 'booth_c', optional: true,", "block_id: 'holding_c', optional: true,", "block_id: meet ? 'rooms_c' : 'studios_c', optional: true,"):
        js = sub(js, "out.push({ type: 'input', " + bid, "out.push({ type: 'input', dispatch_action: true, " + bid)
    # the Picked: line when the Change form is drawn
    js = sub(js, "options: mo }, mi.length ? { initial_options: mi } : {}) }); }\n  return out; }",
        "options: mo }, mi.length ? { initial_options: mi } : {}) }); }\n  pickedLines(out, null, null);   // v64\n  return out; }")
    p["jsCode"] = PICKED + js

# ---- Build Step 2: the Picked: lines on the first draw; Studio E stays Post Processing's room
p = by["Build Step 2"]["parameters"]
js = p["jsCode"]
js = sub(js, "const view = { type: 'modal', callback_id: 'book_step2'", "pickedLines(blocks, null, null);   // v64\nconst view = { type: 'modal', callback_id: 'book_step2'")
js = sub(js, "return f['Vocal Booth'] === true ? 'vbooth' : 'studio'; };",
    "return f['Vocal Booth'] === true && !(/^studio e$/i.test(n) && /^post processing$/i.test(String(s.purpose || ''))) ? 'vbooth' : 'studio'; };   // v64: Studio E is a booth, but Post Processing's room", n=2)
p["jsCode"] = PICKED + js

# ---- Change: Studio E is the room itself for Post Processing (it is a vocal booth for everything else)
KIND = "  const kind = n => /^M[1-8]$/.test(n) ? 'booth' : (rooms.common.indexOf(n) !== -1 ? 'common' : ((rooms.vb || []).indexOf(n) !== -1 ? 'vbooth' : 'studio'));   // v22\n"
KIND2 = ("  const kind = n => /^M[1-8]$/.test(n) ? 'booth' : (rooms.common.indexOf(n) !== -1 ? 'common' : ((rooms.vb || []).indexOf(n) !== -1"
         " && !(/^studio e$/i.test(n) && /^post processing$/i.test(String(T0 || ''))) ? 'vbooth' : 'studio'));   // v22; v64: Studio E for Post Processing\n")
for name in CHANGE_NODES:
    p = by[name]["parameters"]
    p["jsCode"] = sub(p["jsCode"], KIND, KIND2)

# ---- Note Toggle: a multi-select changed -> the same form, its Picked: line redrawn; every other redraw redraws the lines too
p = by["Note Toggle"]["parameters"]
js = p["jsCode"]
js = sub(js, "const a = (p.actions || [])[0] || {};\nconst on = (a.selected_options || []).length > 0;\nconst WH = ",
    "const a = (p.actions || [])[0] || {};\n"
    "// v64: a multi-select changed - nothing else on the form moves; only the line under it (Slack keeps every pick: same block_ids)\n"
    "if (" + json.dumps(MULTI).replace('"', "'") + ".indexOf(a.action_id) !== -1) {\n"
    "  const _bl = pickedLines(JSON.parse(JSON.stringify(V.blocks || [])), st, a);\n"
    "  const _v = { type: 'modal', callback_id: V.callback_id || 'book_step2', title: V.title, close: V.close, private_metadata: V.private_metadata || '', blocks: _bl };\n"
    "  if (V.submit) _v.submit = V.submit;\n"
    "  return [{ json: { view_id: V.id || '', hash: V.hash || '', view: _v, ok: !!V.id } }];\n"
    "}\n"
    "const on = (a.selected_options || []).length > 0;\nconst WH = ")
js = sub(js, "const view = { type: 'modal', callback_id: V.callback_id || 'book_step2', title: V.title, close: V.close, private_metadata: V.private_metadata || '', blocks };",
    "pickedLines(blocks, st, null);   // v64: the lines follow the form as it is now\n"
    "const view = { type: 'modal', callback_id: V.callback_id || 'book_step2', title: V.title, close: V.close, private_metadata: V.private_metadata || '', blocks };")
p["jsCode"] = js   # PICKED already prepended above (Note Toggle is a Change node)

# ---- My Window: Jump to a date
p = by["My Window"]["parameters"]
js = p["jsCode"]
js = sub(js, "const page = /^my_page/.test(String(a.action_id || '')) && /^\\d{4}-\\d{2}-\\d{2}$/.test(String(a.value || ''));   // v16\nlet start = page ? String(a.value) : '';",
    "const _pv = String(a.value || a.selected_date || '');   // v64: Jump to a date sends selected_date\n"
    "const page = /^my_page/.test(String(a.action_id || '')) && /^\\d{4}-\\d{2}-\\d{2}$/.test(_pv);   // v16\nlet start = page ? _pv : '';")
p["jsCode"] = js

# ---- Render My Bookings: the headline, Jump to a date
p = by["Render My Bookings"]["parameters"]
js = p["jsCode"]
js = sub(js, "const blocks = [{ type: 'section', text: md('*Your bookings* · ' + dayShort(W.start) + ' – ' + dayShort(addDays(W.end, -1))) }];",
    "// v64 (Localization, 3 Nov): \"🗓️ Your bookings:\" over the dates; the year when it is not this year\n"
    "const _md = d => { const x = new Date(d + 'T12:00:00Z'); return _MS[x.getUTCMonth()] + ' ' + x.getUTCDate(); };\n"
    "const _last = addDays(W.end, -1), _yNow = String(new Date(Date.now() + 8 * 3600000).getUTCFullYear());\n"
    "const _head = _md(W.start) + ' – ' + _md(_last) + (_last.slice(0, 4) !== _yNow ? ', ' + _last.slice(0, 4) : '');\n"
    "const blocks = [{ type: 'section', text: md('🗓️ *Your bookings:*\\n*' + _head + '*') }];")
js = sub(js, "  { type: 'button', action_id: 'my_page_next', value: addDays(W.start, 7), text: { type: 'plain_text', text: 'Next 7 days →' } } ] });\n"
    "blocks.push({ type: 'context', elements: [md('Further ahead? Type it, like _\"what do I have in November?\"_')] });",
    "  { type: 'button', action_id: 'my_page_next', value: addDays(W.start, 7), text: { type: 'plain_text', text: 'Next 7 days →' } },\n"
    "  { type: 'datepicker', action_id: 'my_page_jump', initial_date: W.start, placeholder: { type: 'plain_text', text: 'Jump to a date' } } ] });   // v64\n"
    "blocks.push({ type: 'context', elements: [md('Further ahead? Pick a date, or type it, like _\"what do I have in November next year?\"_')] });")
js = sub(js, "text: 'Your bookings' } }];", "text: 'Your bookings: ' + _head } }];")
p["jsCode"] = js

# ---- "You can close this window": not while the dates or rooms are being checked (the answer shows only in the window)
p = by["Read Step 2"]["parameters"]
p["jsCode"] = sub(p["jsCode"], "'Checking availability for each date. ' + _wait + ' You can close this window – we’ll let you know in your DM.'",
    "'Checking availability for each date. ' + _wait + ' Keep this window open – the dates show here.'   /* v64: closing it lost the check */")
p = by["Read Step 1"]["parameters"]
p["jsCode"] = sub(p["jsCode"], "{ type: 'context', elements: [{ type: 'mrkdwn', text: _wait }] }] };   // v31",
    "{ type: 'context', elements: [{ type: 'mrkdwn', text: _wait + (series ? ' Keep this window open – the dates show here.' : ' Keep this window open – the free rooms show here.') }] }] };   // v31; v64")

wf["name"] = "Jessie — Slack Interactions — v64 (Localization feedback)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v64.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
