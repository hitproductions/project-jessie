#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v61.json - Jessie — Slack Interactions — v61 (old repeat errors cleared), 3 Nov.

Howard's Slack test of v60, 3 Nov: the live line under Repeats updated ("Books 3 dates: Wed 3, Thu 4, Fri 5 Nov") but the red
"The end date has to be after the first date." from an earlier Find rooms stayed under Or until. Slack keeps an input's error
across views.update while its block_id stays the same (as it keeps the pick - gotcha 47), so v60's redraw alone did not clear it.

v61: every redraw while Repeats is on gives How many times, Or until and On a new block_id ("rep_until~<ms>", strictly increasing),
values kept - an old error has nothing to attach to. Note Toggle finds How many times / Or until by their stem; Read Step 1 reads
them, and puts its errors, by stem (rep_count~…, rep_until~…). Nothing else changes.
Built on workflows/imported/slack-interactions-v60-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v60-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


p = by["Note Toggle"]["parameters"]
js = p["jsCode"]
js = sub(js, "(which === 'room_radio' || which === 'room_other_pick' || which === 'rep_freq_pick' || which === 'rep_days_pick') ? new RegExp(",
    "(which === 'room_radio' || which === 'room_other_pick' || which === 'rep_freq_pick' || which === 'rep_days_pick' || which === 'rep_count_pick' || which === 'rep_until_pick') ? new RegExp(")   # v61: re-keyed
js = sub(js,
    "{ const ni = blocks.findIndex(b => b.block_id === 'rep_note');\n  if (ni !== -1) {\n",
    "{ const ni = blocks.findIndex(b => b.block_id === 'rep_note');\n  if (ni !== -1) {\n"
    "    // v61: Slack keeps an input's error while its block_id is the same - new ids (values kept) leave an old error nothing to hold on to\n"
    "    for (const b of blocks) { const m = String(b.block_id || '').match(/^(rep_count|rep_until|rep_days)(?:~(\\d+))?$/);\n"
    "      if (m) b.block_id = m[1] + '~' + Math.max(Date.now(), (Number(m[2]) || 0) + 1); }\n")
p["jsCode"] = js

p = by["Read Step 1"]["parameters"]
js = p["jsCode"]
js = sub(js,
    "  const count = Number((v.rep_count && v.rep_count.rep_count_pick && v.rep_count.rep_count_pick.selected_option && v.rep_count.rep_count_pick.selected_option.value) || 0);\n",
    "  // v61: How many times / Or until may be redrawn under a new block_id (\"rep_until~<ms>\") - read them, and put errors, by stem\n"
    "  const rcK = Object.keys(v).find(k => /^rep_count(~\\d+)?$/.test(k)) || 'rep_count';\n"
    "  const ruK = Object.keys(v).find(k => /^rep_until(~\\d+)?$/.test(k)) || 'rep_until';\n"
    "  const count = Number((v[rcK] && v[rcK].rep_count_pick && v[rcK].rep_count_pick.selected_option && v[rcK].rep_count_pick.selected_option.value) || 0);\n")
js = sub(js,
    "  const until = count ? '' : ((v.rep_until && v.rep_until.rep_until_pick && v.rep_until.rep_until_pick.selected_date) || '');",
    "  const until = count ? '' : ((v[ruK] && v[ruK].rep_until_pick && v[ruK].rep_until_pick.selected_date) || '');")
js = sub(js, "else if (!count && !until) errors.rep_count = 'How many times - or pick an end date.';",
    "else if (!count && !until) errors[rcK] = 'How many times - or pick an end date.';")
js = sub(js, "else if (until && until <= date) errors.rep_until = 'The end date has to be after the first date.';",
    "else if (until && until <= date) errors[ruK] = 'The end date has to be after the first date.';")
js = sub(js, "if (dates.length > 16) errors.rep_until = repTooMany(dates.length);",
    "if (dates.length > 16) errors[until ? ruK : rcK] = repTooMany(dates.length);")
js = sub(js, "else if (dates.length < 2) errors[until ? 'rep_until' : 'rep_count'] =",
    "else if (dates.length < 2) errors[until ? ruK : rcK] =")
p["jsCode"] = js

wf["name"] = "Jessie — Slack Interactions — v61 (old repeat errors cleared)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v61.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
