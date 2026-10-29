#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v57.json - Jessie — Slack Interactions — v57 (repeat days ticked), 29 Oct.

Howard's Slack test, 29 Oct: Repeats -> How often? Weekdays, and the On boxes still showed only Fri ticked (the first date's day).
Step 1 then booked Monday to Friday anyway - for Weekdays and Daily the ticks were ignored (v13-v56) - so what the form showed and
what was booked disagreed.

v57: picking How often? redraws On with its days ticked - Weekly the first date's day, Weekdays Mon-Fri, Daily all seven - and
step 1 books the days ticked, whatever How often says (none ticked: Weekdays Mon-Fri, Daily every day, Weekly asks for a day).
How often? sends its pick at once (dispatch_action); the redrawn On gets a new block_id ("rep_days~<ms>") because Slack keeps a
control's ticks across views.update while its block_id is the same (gotcha 47), and step 1 / the toggles find it by its stem.
A typed series (main v268, Build Step 1's pre.rep) gets the same preset. Built on
workflows/imported/slack-interactions-v56-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v56-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


# repBlocks (Build Step 1 and Note Toggle): the On ticks follow How often; How often sends its pick at once
for nm in ["Build Step 1", "Note Toggle"]:
    p = by[nm]["parameters"]
    p["jsCode"] = sub(p["jsCode"],
        "  const dIni = dayOpts.filter(o => (days.length ? days : [K[wd]]).indexOf(o.value) !== -1);",
        "  // v57: none given -> How often's days: Weekly the first date's day, Weekdays Mon-Fri, Daily all seven\n"
        "  const preset = rep.f === 'weekdays' ? ['MO', 'TU', 'WE', 'TH', 'FR'] : rep.f === 'daily' ? K.slice() : [K[wd]];\n"
        "  const dIni = dayOpts.filter(o => (days.length ? days : preset).indexOf(o.value) !== -1);")
    p["jsCode"] = sub(p["jsCode"],
        "    { type: 'input', block_id: 'rep_freq', label: pt('How often?'), element:",
        "    { type: 'input', block_id: 'rep_freq', dispatch_action: true, label: pt('How often?'), element:")   # v57: the pick redraws On

p = by["Check Signature"]["parameters"]
p["jsCode"] = sub(p["jsCode"], "'note_toggle', 'repeat_toggle', 'details", "'note_toggle', 'repeat_toggle', 'rep_freq_pick', 'details")   # v57

p = by["Note Toggle"]["parameters"]
js = p["jsCode"]
js = sub(js, "const WH = ['repeat_toggle'", "const WH = ['repeat_toggle', 'rep_freq_pick'")   # v57
js = sub(js, ".filter(b => OWN.indexOf(b.block_id) === -1)",
    ".filter(b => OWN.indexOf(String(b.block_id || '').split('~')[0]) === -1)")   # v57: a redrawn On ("rep_days~…") goes with Repeats
js = sub(js, "({ purpose_pick: 'purpose', room_radio: 'room', room_other_pick: 'room_other' }[which] || which)",
    "({ purpose_pick: 'purpose', room_radio: 'room', room_other_pick: 'room_other', rep_freq_pick: 'rep_freq' }[which] || which)")
js = sub(js,
    "    blocks.splice(at + 1, 0, ...repBlocks(date, null));\n  }\n}\n",
    "    blocks.splice(at + 1, 0, ...repBlocks(date, null));\n  }\n"
    "  // v57 (Howard, 29 Oct): How often? picked -> On redrawn with its days ticked (Weekdays Mon-Fri, Daily all seven, Weekly the\n"
    "  // first date's day), under a new block_id so Slack shows the new ticks (gotcha 47)\n"
    "  if (which === 'rep_freq_pick') {\n"
    "    const di = blocks.findIndex(b => /^rep_days(~\\d+)?$/.test(b.block_id || ''));\n"
    "    const f = (a.selected_option && a.selected_option.value) || 'weekly';\n"
    "    const date = ((st.date || {}).date_pick || {}).selected_date || ((blocks.find(b => b.block_id === 'date') || {}).element || {}).initial_date || '';\n"
    "    const fresh = repBlocks(date, { f }).find(b => b.block_id === 'rep_days');\n"
    "    if (di !== -1 && fresh) { fresh.block_id = 'rep_days~' + Date.now(); blocks[di] = fresh; }\n"
    "  }\n}\n")
p["jsCode"] = js

p = by["Read Step 1"]["parameters"]
js = p["jsCode"]
js = sub(js,
    "  let days = ((v.rep_days && v.rep_days.rep_days_pick && v.rep_days.rep_days_pick.selected_options) || []).map(o => o.value);\n"
    "  if (freq === 'weekdays') days = ['MO', 'TU', 'WE', 'TH', 'FR'];\n",
    "  // v57: the days ticked are the days booked, whatever How often says (the On box may be redrawn as \"rep_days~<ms>\");\n"
    "  // none ticked -> Weekdays Mon-Fri, Daily every day (Weekly asks for one). v13-v56 ignored the ticks for Weekdays / Daily.\n"
    "  const rdK = Object.keys(v).find(k => /^rep_days(~\\d+)?$/.test(k)) || 'rep_days';\n"
    "  let days = ((v[rdK] && v[rdK].rep_days_pick && v[rdK].rep_days_pick.selected_options) || []).map(o => o.value);\n"
    "  if (!days.length && freq === 'weekdays') days = ['MO', 'TU', 'WE', 'TH', 'FR'];\n"
    "  if (!days.length && freq === 'daily') days = ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'];\n")
js = sub(js, "if (freq === 'weekly' && !days.length) errors.rep_days = 'Pick at least one day.';",
    "if (freq === 'weekly' && !days.length) errors[rdK] = 'Pick at least one day.';")
js = sub(js, "      if (freq === 'daily' || want.has(cur.getUTCDay())) dates.push(d);",
    "      if (want.has(cur.getUTCDay())) dates.push(d);   // v57: the days ticked")
p["jsCode"] = js

wf["name"] = "Jessie — Slack Interactions — v57 (repeat days ticked)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v57.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
