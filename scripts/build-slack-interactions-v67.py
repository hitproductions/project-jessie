#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v67.json - Jessie — Slack Interactions — v67 (moved dates choosable), 4 Nov.

Howard's Slack test of the review (4 Nov ~14:50): "for nov 10, is there a way where i can choose? because it chose for me studio 2".
With Book Series v11, a date moved to another room shows as a dropdown already set to Jessie's room ("Studio 2 instead of Studio 6")
- Book all books it as before - with the other suitable rooms free then, the nearest free times in the rooms asked, and skip.
The picks are read as mv_<date> (moved) and ch_<date> (taken), and To Book Series applies either: another room or time, or skip
(a moved date skipped is taken out). An older Book Series' moved dates (no options) show as the list, as v66.
Built on workflows/imported/slack-interactions-v66-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v66-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:160])
    return js.replace(a, b)


def code(name, f):
    p = by[name]["parameters"]
    p["jsCode"] = f(p["jsCode"])


code("After Prepare Series", lambda js: sub(js,
    "  if (mvI.length) { const L = mvI.slice(0, 25).map(x => '- ' + sh(x.d) + ' · ' + x.note);\n"
    "    if (mvI.length > 25) L.push('…and ' + (mvI.length - 25) + ' more in another room');\n"
    "    blocks.push({ type: 'section', block_id: 'moved', text: md('🔄 *Another room (' + mvI.length + '):*\\n' + L.join('\\n')) }); }",
    "  // v67 (Howard, 4 Nov: \"is there a way where i can choose?\"): a moved date with options (Book Series v11) is a dropdown set to\n"
    "  // Jessie's room - change it or leave it; more than 25, or an older Book Series, as the list\n"
    "  const mvO = mvI.filter(x => Array.isArray(x.options) && x.options.length > 1).slice(0, 25), mvL = mvI.filter(x => mvO.indexOf(x) === -1);\n"
    "  if (mvO.length) {\n"
    "    blocks.push({ type: 'section', block_id: 'moved', text: md('🔄 *Another room (' + mvI.length + ') – change it if you like:*') });\n"
    "    for (const x of mvO) { const os = x.options.map(o => ({ text: { type: 'plain_text', text: String(o.label).slice(0, 75) }, value: o.v }));\n"
    "      blocks.push({ type: 'input', block_id: 'mv_' + x.d, label: pt(sh(x.d) + ' – ' + ((t => t.join(' and ') + (t.length > 1 ? ' are' : ' is'))(String(x.note || '').split(', ').map(q => q.split(' instead of ')[1] || '').filter(Boolean))) + ' taken then'),\n"
    "        element: { type: 'static_select', action_id: 'ch_pick', options: os, initial_option: os.find(o => o.value === (x.dflt || 'r0')) || os[0] } }); }\n"
    "  }\n"
    "  if (mvL.length) { const L = mvL.slice(0, 25).map(x => '- ' + sh(x.d) + ' · ' + x.note);\n"
    "    if (mvL.length > 25) L.push('…and ' + (mvL.length - 25) + ' more in another room');\n"
    "    blocks.push({ type: 'section', block_id: mvO.length ? 'moved_more' : 'moved', text: md((mvO.length ? '' : '🔄 *Another room (' + mvI.length + '):*\\n') + L.join('\\n')) }); }"))

code("Read Series Confirm", lambda js: sub(js,
    "for (const k of Object.keys(_sv)) { const m = k.match(/^ch_(\\d{4}-\\d{2}-\\d{2})$/); const o = m && ((_sv[k] || {}).ch_pick || {}).selected_option; if (o) choices[m[1]] = o.value; }\n"
    "const n = Number(meta.n || 0) + Object.keys(choices).filter(k => choices[k] !== 'skip').length;",
    "// v67: mv_<date> too - a moved date's room (already counted in meta.n; skipping it takes one off)\n"
    "const _mv = {};\n"
    "for (const k of Object.keys(_sv)) { const m = k.match(/^(ch|mv)_(\\d{4}-\\d{2}-\\d{2})$/); const o = m && ((_sv[k] || {}).ch_pick || {}).selected_option; if (o) { choices[m[2]] = o.value; if (m[1] === 'mv') _mv[m[2]] = 1; } }\n"
    "const n = Number(meta.n || 0) + Object.keys(choices).filter(k => !_mv[k] && choices[k] !== 'skip').length - Object.keys(choices).filter(k => _mv[k] && choices[k] === 'skip').length;"))

code("To Book Series", lambda js: sub(js,
    "for (const d of Object.keys(__ch)) { const o = [].concat(__ch[d] || []).find(x => x && x.v === __pick[d] && x.v !== 'skip' && x.start && x.end);\n"
    "  if (o) { if (__ds.indexOf(d) === -1) __ds.push(d); __per[d] = { rooms: o.rooms, start: o.start, end: o.end }; } else skipped_review.push(d); }",
    "// v67: a moved date's options too (Book Series v11) - another room (no time), another time, or skip; no pick keeps Jessie's room\n"
    "for (const d of Object.keys(__ch)) { const o = [].concat(__ch[d] || []).find(x => x && x.v === __pick[d] && x.v !== 'skip' && (x.rooms || (x.start && x.end)));\n"
    "  const _in = __ds.indexOf(d) !== -1;\n"
    "  if (o) { if (!_in) __ds.push(d); __per[d] = { rooms: o.rooms || '', start: o.start || '', end: o.end || '' }; }\n"
    "  else if (_in && __pick[d] !== 'skip') { /* moved, not picked (or an option never offered): Jessie's room, as stored */ }\n"
    "  else { if (_in) __ds.splice(__ds.indexOf(d), 1); delete __per[d]; skipped_review.push(d); } }"))

wf["name"] = "Jessie — Slack Interactions — v67 (moved dates choosable)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v67.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
