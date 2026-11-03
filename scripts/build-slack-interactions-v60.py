#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v60.json - Jessie — Slack Interactions — v60 (repeats counted live), 3 Nov.

Howard's Slack test, 3 Nov: Localization Dubbing from Nov 2, Weekdays, Or until Nov 5 showed "That is more than 16 dates" -
an error from an earlier Find rooms (the pre-filled "Or until", four weeks out, or a first date still in 2026) that Slack keeps
on screen until the next submit, so the form looked blocked. Changing a date re-checked nothing.

v60:
- every Repeats field (How often, On, How many times, Or until) and the first date redraw the form the moment they change -
  a redrawn form carries no old error - and the line under Repeats says what it books, live: "Books 4 dates: Tue 2, Wed 3,
  Thu 4, Fri 5 Nov", or the problem in words ("That's 21 dates – the most is 16 …"); Find rooms still refuses as a backstop;
- no pre-filled "Or until" (the four-week default was only so the picker opened in the QA year, and it overflowed for
  Weekdays / Daily);
- decided (Howard, 3 Nov): a series starts on the date chosen - that date is always the first booking, then the days ticked
  after it; a ticked day before it (Monday before a Tuesday start) is not booked.
The date list the form shows is the list booked (To Prepare Series sends it to Book Series as `dates`).
Built on workflows/imported/slack-interactions-v59-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v59-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


# one copy of the date rule and the live line, in Build Step 1, Note Toggle and Read Step 1
REP_FN = r"""// v60 (Howard, 3 Nov): a series starts on the date chosen - always its first booking - then the days ticked after it,
// until How many times or the end date (How many times wins). The form's live line and step 1's check use this one rule.
function repSeries(date, freq, days, count, until) {
  const K = { SU: 0, MO: 1, TU: 2, WE: 3, TH: 4, FR: 5, SA: 6 };
  let ds = [].concat(days || []);
  if (!ds.length && freq === 'weekdays') ds = ['MO', 'TU', 'WE', 'TH', 'FR'];
  if (!ds.length && freq === 'daily') ds = Object.keys(K);
  const want = new Set(ds.map(d => K[d]));
  const out = [];
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(date || ''))) return out;
  const cur = new Date(date + 'T12:00:00Z');
  for (let g = 0; g < 800; g++) {
    const d = cur.toISOString().slice(0, 10);
    if (until && d > until) break;
    if (g === 0 || want.has(cur.getUTCDay())) out.push(d);
    if (count && out.length >= count) break;
    if (!count && !until) break;
    cur.setUTCDate(cur.getUTCDate() + 1);
  }
  return out;
}
function repList(ds) {
  const W = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'], M = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const p = d => { const x = new Date(d + 'T12:00:00Z'); return { w: W[x.getUTCDay()], d: x.getUTCDate(), m: M[x.getUTCMonth()], y: x.getUTCFullYear() }; };
  if (ds.length > 8) { const a = p(ds[0]), b = p(ds[ds.length - 1]); return a.w + ' ' + a.d + ' ' + a.m + ' – ' + b.w + ' ' + b.d + ' ' + b.m + (a.y !== b.y ? ' ' + b.y : ''); }
  const parts = []; let cur = null;
  for (const d of ds) { const x = p(d); if (cur && cur.m !== x.m) parts[parts.length - 1] += ' ' + cur.m; parts.push(x.w + ' ' + x.d); cur = x; }
  if (cur) parts[parts.length - 1] += ' ' + cur.m;
  return parts.join(', ');
}
function repTooMany(n) { return 'That’s ' + n + ' dates – the most is 16. Pick an earlier end date or a number.'; }
function repNote(date, freq, days, count, until) {
  count = Number(count || 0); until = String(until || '');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(date || ''))) return 'Pick the first date. Up to 16 dates.';
  if (freq === 'weekly' && ![].concat(days || []).length) return 'Tick at least one day.';
  if (!count && !until) return 'Pick *How many times* or an end date. Up to 16 dates.';
  if (!count && until <= date) return 'The end date has to be after the first date.';
  const ds = repSeries(date, freq, days, count, count ? '' : until);
  if (ds.length > 16) return '⚠️ ' + repTooMany(ds.length);
  if (ds.length < 2) return 'That’s only one date – untick Repeats for a single booking.';
  return '🔁 *Books ' + ds.length + ' dates:* ' + repList(ds);
}
"""

for nm in ["Build Step 1", "Note Toggle"]:
    p = by[nm]["parameters"]
    js = p["jsCode"]
    js = sub(js, "function repBlocks(date, rep) {", REP_FN + "function repBlocks(date, rep) {")
    js = sub(js,
        "  // v15: \"Or until\" starts four weeks after the first date - the picker opens in the right year (QA runs a year ahead)\n"
        "  const u0 = /^\\d{4}-\\d{2}-\\d{2}$/.test(String(rep.u || '')) ? rep.u\n"
        "    : (/^\\d{4}-\\d{2}-\\d{2}$/.test(String(date || '')) ? new Date(Date.parse(date + 'T12:00:00Z') + 28 * 86400000).toISOString().slice(0, 10) : '');",
        "  // v60: no pre-filled \"Or until\" (v15 opened it four weeks out for the QA year; for Weekdays / Daily that was over 16 dates)\n"
        "  const u0 = /^\\d{4}-\\d{2}-\\d{2}$/.test(String(rep.u || '')) ? rep.u : '';")
    js = sub(js, "{ type: 'input', block_id: 'rep_count', optional: true, label: pt('How many times'),",
        "{ type: 'input', block_id: 'rep_count', optional: true, dispatch_action: true, label: pt('How many times'),")   # v60: redraws the line
    js = sub(js, "{ type: 'input', block_id: 'rep_until', optional: true, label: pt('Or until'),",
        "{ type: 'input', block_id: 'rep_until', optional: true, dispatch_action: true, label: pt('Or until'),")   # v60
    js = sub(js, "{ type: 'context', block_id: 'rep_note', elements: [{ type: 'mrkdwn', text: 'Up to 16 dates.' }] }];",
        "{ type: 'context', block_id: 'rep_note', elements: [{ type: 'mrkdwn', text: repNote(date, rep.f || 'weekly', days.length ? days : preset, rep.n, u0) }] }];   // v60: live")
    p["jsCode"] = js

# the first date redraws the line too (step 1 only - the Change forms' date pickers send nothing)
p = by["Build Step 1"]["parameters"]
p["jsCode"] = sub(p["jsCode"], "{ type: 'input', block_id: 'date', label: { type: 'plain_text', text: 'Date' },",
    "{ type: 'input', block_id: 'date', dispatch_action: true, label: { type: 'plain_text', text: 'Date' },")   # v60

p = by["Check Signature"]["parameters"]
p["jsCode"] = sub(p["jsCode"], "'rep_freq_pick', 'rep_days_pick', 'details_toggle'",
    "'rep_freq_pick', 'rep_days_pick', 'rep_count_pick', 'rep_until_pick', 'date_pick', 'details_toggle'")   # v60

p = by["Note Toggle"]["parameters"]
js = p["jsCode"]
js = sub(js, "const WH = ['repeat_toggle', 'rep_freq_pick', 'rep_days_pick',",
    "const WH = ['repeat_toggle', 'rep_freq_pick', 'rep_days_pick', 'rep_count_pick', 'rep_until_pick', 'date_pick',")   # v60
js = sub(js, "const which = WH.indexOf(a.action_id) !== -1 ? a.action_id : 'note_toggle';\n",
    "const which = WH.indexOf(a.action_id) !== -1 ? a.action_id : 'note_toggle';\n"
    "// v60: a new first date only matters to the Repeats line - with Repeats off, no redraw at all\n"
    "if (which === 'date_pick' && !(V.blocks || []).some(b => b.block_id === 'rep_note')) return [];\n")
js = sub(js, "rep_freq_pick: 'rep_freq', rep_days_pick: 'rep_days' }[which] || which)",
    "rep_freq_pick: 'rep_freq', rep_days_pick: 'rep_days', rep_count_pick: 'rep_count', rep_until_pick: 'rep_until', date_pick: 'date' }[which] || which)")
js = sub(js,
    "const view = { type: 'modal', callback_id: V.callback_id || 'book_step2', title: V.title, close: V.close, private_metadata: V.private_metadata || '', blocks };",
    "// v60: the Repeats line, from what the form now shows (every Repeats field and the first date redraw it, and a redrawn form\n"
    "// carries no old error)\n"
    "{ const ni = blocks.findIndex(b => b.block_id === 'rep_note');\n"
    "  if (ni !== -1) {\n"
    "    const el = s => (blocks.find(b => new RegExp('^' + s + '(~\\\\d+)?$').test(b.block_id || '')) || {}).element || {};\n"
    "    const f0 = (el('rep_freq').initial_option || {}).value || 'weekly';\n"
    "    const dy = (el('rep_days').initial_options || []).map(o => o.value);\n"
    "    const n0 = Number((el('rep_count').initial_option || {}).value || 0);\n"
    "    blocks[ni] = { type: 'context', block_id: 'rep_note', elements: [{ type: 'mrkdwn', text: repNote(el('date').initial_date || '', f0, dy, n0, el('rep_until').initial_date || '') }] };\n"
    "  } }\n"
    "const view = { type: 'modal', callback_id: V.callback_id || 'book_step2', title: V.title, close: V.close, private_metadata: V.private_metadata || '', blocks };")
p["jsCode"] = js

p = by["Read Step 1"]["parameters"]
js = p["jsCode"]
js = sub(js, "const rfK = Object.keys(v).find(k => /^rep_freq(~\\d+)?$/.test(k)) || '';",
    REP_FN + "const rfK = Object.keys(v).find(k => /^rep_freq(~\\d+)?$/.test(k)) || '';")
js = sub(js,
    "    const want = new Set(days.map(d => DOWK[d]));\n"
    "    const dates = []; const cur = new Date(date + 'T12:00:00Z');\n"
    "    for (let g = 0; g < 400 && dates.length < 17; g++) {\n"
    "      const d = cur.toISOString().slice(0, 10);\n"
    "      if (until && d > until) break;\n"
    "      if (want.has(cur.getUTCDay())) dates.push(d);   // v57: the days ticked\n"
    "      if (count && dates.length >= count) break;\n"
    "      cur.setUTCDate(cur.getUTCDate() + 1);\n"
    "    }\n"
    "    if (dates.length > 16) errors.rep_until = 'That is more than 16 dates - pick an earlier end date, or a number.';\n",
    "    // v60: the chosen date first, then the days ticked after it - the same rule as the form's live line\n"
    "    const dates = repSeries(date, freq, days, count, until);\n"
    "    if (dates.length > 16) errors.rep_until = repTooMany(dates.length);\n")
p["jsCode"] = js

wf["name"] = "Jessie — Slack Interactions — v60 (repeats counted live)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v60.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
