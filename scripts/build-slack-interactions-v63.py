#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v63.json - Jessie — Slack Interactions — v63 (repeat problems in the line), 3 Nov.

Howard's Slack test of v62, 3 Nov: a date picked in "Or until" still went back to "Select a date". v61 / v62 redraw How many
times, Or until and On under new block_ids on every change (to shed an old red error) - and Slack then shows the picker empty.
In v60 (ids unchanged) the picked end date stayed; its only fault was the red error from an earlier Find rooms, which Slack keeps
on a field whose id does not change.

v63 takes away what makes the red error:
- no more new ids - How many times, Or until and On keep their ids on every redraw (as in v60, so Slack keeps every pick);
- Find rooms never puts a red error on a Repeats field: a Repeats problem comes back as the same form (same ids, every pick
  written in) with the problem in the line under Repeats ("⚠️ That's 21 dates – the most is 16 …"); a problem elsewhere (time,
  booking type) is a field error as before, without the Repeats ones - the live line already says those;
- kept from v62: the field that sent the action takes the action's own value; Read Step 1 / Note Toggle still find the fields by
  stem (a window opened on v61 / v62 still carries "rep_until~…" ids).
Built on workflows/imported/slack-interactions-v62-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v62-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


p = by["Note Toggle"]["parameters"]
p["jsCode"] = sub(p["jsCode"],
    "    // v61: Slack keeps an input's error while its block_id is the same - new ids (values kept) leave an old error nothing to hold on to\n"
    "    for (const b of blocks) { const m = String(b.block_id || '').match(/^(rep_count|rep_until|rep_days)(?:~(\\d+))?$/);\n"
    "      if (m) b.block_id = m[1] + '~' + Math.max(Date.now(), (Number(m[2]) || 0) + 1); }\n",
    "    // v63: no new ids (v61 / v62 gave them, and Slack then showed a picked end date as empty) - Find rooms no longer puts red\n"
    "    // errors on the Repeats fields, so there is no old error to shed\n")

p = by["Read Step 1"]["parameters"]
p["jsCode"] = sub(p["jsCode"],
    "return [{ json: { valid, s,\n  answer: valid ? { response_action: 'push', view: loading } : { response_action: 'errors', errors } } }];",
    "// v63: a Repeats problem never comes back as a red field error (Slack keeps those on screen while the field keeps its id) - the\n"
    "// same form comes back, every pick written in, with the problem in the line under Repeats; other fields' errors as before\n"
    "let answer = valid ? { response_action: 'push', view: loading } : { response_action: 'errors', errors };\n"
    "if (!valid) {\n"
    "  const isRep = k => /^(rep_count|rep_until|rep_days)(~\\d+)?$/.test(k);\n"
    "  const repK = Object.keys(errors).filter(isRep), rest = Object.keys(errors).filter(k => !isRep(k));\n"
    "  const V0 = p.view || {}, bl = JSON.parse(JSON.stringify(V0.blocks || []));\n"
    "  const ni = bl.findIndex(b => b.block_id === 'rep_note');\n"
    "  if (repK.length && ni !== -1) {\n"
    "    if (rest.length) answer = { response_action: 'errors', errors: Object.fromEntries(rest.map(k => [k, errors[k]])) };\n"
    "    else {\n"
    "      for (const b of bl) {   // what the form shows now, written in (nothing left to Slack's memory)\n"
    "        if (b.type !== 'input' || !b.element) continue;\n"
    "        const e = b.element, sv = (v[b.block_id] || {})[e.action_id] || {};\n"
    "        if (e.type === 'datepicker' && sv.selected_date) e.initial_date = sv.selected_date;\n"
    "        else if ((e.type === 'static_select' || e.type === 'radio_buttons') && sv.selected_option) {\n"
    "          const all = (e.options || []).concat(...((e.option_groups || []).map(g => g.options || [])));\n"
    "          const o = all.find(x => x.value === sv.selected_option.value); if (o) e.initial_option = o; }\n"
    "        else if (e.type === 'checkboxes' && sv.selected_options) { const vals = sv.selected_options.map(o => o.value);\n"
    "          const o = (e.options || []).filter(x => vals.indexOf(x.value) !== -1); if (o.length) e.initial_options = o; else delete e.initial_options; }\n"
    "        else if (e.type === 'plain_text_input' && typeof sv.value === 'string') e.initial_value = sv.value;\n"
    "      }\n"
    "      bl[ni] = { type: 'context', block_id: 'rep_note', elements: [{ type: 'mrkdwn', text: '⚠️ ' + String(errors[repK[0]]).replace(/^⚠️\\s*/, '') }] };\n"
    "      answer = { response_action: 'update', view: Object.assign({ type: 'modal', callback_id: V0.callback_id || 'book_step1', title: V0.title, close: V0.close,\n"
    "        private_metadata: V0.private_metadata || '', blocks: bl }, V0.submit ? { submit: V0.submit } : {}) };\n"
    "    }\n"
    "  }\n"
    "}\n"
    "return [{ json: { valid, s, answer } }];")

wf["name"] = "Jessie — Slack Interactions — v63 (repeat problems in the line)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v63.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
