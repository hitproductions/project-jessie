#!/usr/bin/env python3
"""Builds two candidates, 29 Oct (Howard: "build v58 with all three"):

  workflows/slack-interactions-v58.json     - Jessie — Slack Interactions — v58 (ticks + deadlines)
  workflows/open-consent-request-v13.json   - Jessie — Open Consent Request — v13 (all day deadlines)

1. How often follows the ticks (Slack Interactions). v57 made How often tick its days and step 1 book the days ticked; unticking
   some under Daily / Weekdays left the dropdown saying Daily. Now every tick sends its pick (dispatch_action on On) and How often
   is redrawn to match: Mon-Fri -> Weekdays, all seven -> Daily, anything else -> Weekly - under a new block_id ("rep_freq~<ms>",
   gotcha 47), only when it changes. Step 1 finds How often by its stem.

2. All-day request deadlines (both). An all-day booking starts at 12:00 AM and a deadline never fell after the start, so a request
   for an M booth all day today gave the holder no time at all (Consent Sweep handed it over within ~10 minutes) and tomorrow all
   day gave midnight tonight. Decided 29 Oct: an all-day request is settled before its day - 2+ days ahead 24 h (never past the
   day's 12:00 AM), tomorrow 6:00 PM the evening before (at least 1 h, never past midnight), today 1 h. Timed requests unchanged
   (same day 3 h, tomorrow 10:00 AM, later 24 h, never past the start; priority requests 24 h, at least 1 h before the start).
   Open Consent Request (the deadline that is stored and acted on) knows all day from the request (all_day in the payload, a
   date-only start, or 12:00 AM to 12:00 AM); the form's preview line from the booking it shows.

3. Deadlines in QA (both). The booking is a year ahead (YEAR_SHIFT) while the clock is real, so every request looked 2+ days away
   and got 24 h ("reply by tomorrow" for a booth needed today). The deadline is now worked out on the booking's real-year date
   (start minus YEAR_SHIFT years, unless that is already past) - a new LAUNCH SWITCH `const YEAR_SHIFT = 1;` in Open Consent
   Request's Build Request and Slack Interactions' Build Step 2 and Note Toggle, flipped to 0 by flip-launch-switches with the
   others (check-launch-switches finds every `const YEAR_SHIFT`).

Built on the live downloads: workflows/imported/slack-interactions-v57-imported.json and open-consent-request-v12-imported.json.
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


OLD_DL = """function mboothDeadline(nowISO, startISO, cfg) {
  const k = cfg || {};
  const sameDayH = k.sameDayH == null ? 3 : k.sameDayH;
  const farWindowH = k.farWindowH == null ? 24 : k.farWindowH;
  const dayBeforeHour = k.dayBeforeHour == null ? 10 : k.dayBeforeHour;
  const now = new Date(nowISO).getTime();
  const start = new Date(startISO).getTime();
  const daysAhead = manilaDayIndex(start) - manilaDayIndex(now);
  let deadline;
  if (daysAhead >= 2) deadline = now + farWindowH * 3600 * 1000;
  else if (daysAhead === 1) deadline = (manilaDayIndex(start) * 86400000 - MNL_TZ) + dayBeforeHour * 3600 * 1000;
  else deadline = now + sameDayH * 3600 * 1000;
  deadline = Math.max(now, Math.min(deadline, start));
  return new Date(deadline).toISOString();
}
function requestDeadline(kind, nowISO, startISO) {
  return String(kind || '').toUpperCase() === 'MBOOTH' ? mboothDeadline(nowISO, startISO) : computeDeadline(nowISO, startISO, { maxWindowH: 24, minLeadMin: 60 });
}
"""

NEW_DL = """// v58 (decided 29 Oct): an all-day request is settled before its day starts - 2+ days ahead 24 h (never past the day's 12:00 AM),
// tomorrow 6:00 PM the evening before (at least 1 h, never past midnight), today 1 h (the day has begun; before v58 an all-day
// start of 12:00 AM capped it at "now", and the Sweep handed the booth over within minutes). Timed requests as before.
function mboothDeadline(nowISO, startISO, cfg, allDay) {
  const k = cfg || {};
  const sameDayH = k.sameDayH == null ? 3 : k.sameDayH;
  const farWindowH = k.farWindowH == null ? 24 : k.farWindowH;
  const dayBeforeHour = k.dayBeforeHour == null ? 10 : k.dayBeforeHour;
  const H = 3600 * 1000;
  const now = new Date(nowISO).getTime();
  let start = new Date(startISO).getTime();
  if (/^\\d{4}-\\d{2}-\\d{2}$/.test(String(startISO || '').trim())) { start = Date.parse(String(startISO).trim() + 'T00:00:00+08:00'); allDay = true; }   // a date-only start is all day
  const daysAhead = manilaDayIndex(start) - manilaDayIndex(now);
  let deadline;
  if (allDay) {
    const day0 = manilaDayIndex(start) * 86400000 - MNL_TZ;   // 12:00 AM of the booked day, Manila
    if (daysAhead >= 2) deadline = Math.min(now + farWindowH * H, day0);
    else if (daysAhead === 1) deadline = Math.min(Math.max(day0 - 6 * H, now + H), day0);   // 6:00 PM the evening before
    else deadline = now + H;
    return new Date(Math.max(now, deadline)).toISOString();
  }
  if (daysAhead >= 2) deadline = now + farWindowH * H;
  else if (daysAhead === 1) deadline = (manilaDayIndex(start) * 86400000 - MNL_TZ) + dayBeforeHour * H;
  else deadline = now + sameDayH * H;
  deadline = Math.max(now, Math.min(deadline, start));
  return new Date(deadline).toISOString();
}
// LAUNCH SWITCH (v58): YEAR_SHIFT 1 while testing, 0 at launch (scripts/flip-launch-switches). The booking is a year ahead while
// the clock is real, so the deadline is worked out on its real-year date - otherwise every request looks 2+ days away (24 h).
const YEAR_SHIFT = 1;
function realYear(iso, nowISO) {
  const s = String(iso || '').trim();
  if (!YEAR_SHIFT || !/^\\d{4}-/.test(s)) return s;
  const back = String(Number(s.slice(0, 4)) - YEAR_SHIFT) + s.slice(4);
  const b = /^\\d{4}-\\d{2}-\\d{2}$/.test(back) ? Date.parse(back + 'T00:00:00+08:00') : Date.parse(back);
  return manilaDayIndex(b) >= manilaDayIndex(new Date(nowISO).getTime()) ? back : s;   // already past in the real year -> as is
}
function requestDeadline(kind, nowISO, startISO, allDay) {
  const st = realYear(startISO, nowISO);
  return String(kind || '').toUpperCase() === 'MBOOTH' ? mboothDeadline(nowISO, st, null, !!allDay) : computeDeadline(nowISO, st, { maxWindowH: 24, minLeadMin: 60 });
}
"""

# ---------------- Open Consent Request v13 ----------------
oc = json.load(open(os.path.join(ROOT, "workflows", "imported", "open-consent-request-v12-imported.json")))
ob = {n["name"]: n for n in oc["nodes"]}
p = ob["Build Request"]["parameters"]
js = sub(p["jsCode"], OLD_DL, NEW_DL)
js = sub(js, "const deadline = requestDeadline(kind, now, c.reqStart);",
    "// v58: all day - the booking's own flag, a date-only start, or 12:00 AM to 12:00 AM (whole days)\n"
    "const _allDay = (() => { let pl = {}; try { pl = JSON.parse(c.reqPayload || '{}') || {}; } catch (e) { pl = {}; }\n"
    "  if (pl.all_day === true || String(pl.all_day) === 'true') return true;\n"
    "  const s = String(c.reqStart || '').trim(), e = String(c.reqEnd || '').trim();\n"
    "  if (/^\\d{4}-\\d{2}-\\d{2}$/.test(s)) return true;\n"
    "  const a = Date.parse(s), b = Date.parse(e), mid = x => ((x + MNL_TZ) % 86400000) === 0;\n"
    "  return Number.isFinite(a) && Number.isFinite(b) && b > a && mid(a) && mid(b); })();\n"
    "const deadline = requestDeadline(kind, now, c.reqStart, _allDay);")
p["jsCode"] = js
oc["name"] = "Jessie — Open Consent Request — v13 (all day deadlines)"
out = os.path.join(ROOT, "workflows", "open-consent-request-v13.json")
with open(out, "w") as f:
    json.dump(oc, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(oc["nodes"]), "nodes")

# ---------------- Slack Interactions v58 ----------------
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v57-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}

for nm in ["Build Step 2", "Note Toggle"]:
    p = by[nm]["parameters"]
    js = sub(p["jsCode"], OLD_DL, NEW_DL)
    js = sub(js, "const dl = _deadlineText(requestDeadline(k === 'M' ? 'MBOOTH' : 'PREEMPT', new Date().toISOString(), start));",
        "const dl = _deadlineText(requestDeadline(k === 'M' ? 'MBOOTH' : 'PREEMPT', new Date().toISOString(), start, !!m.allDay));   // v58: all day")
    p["jsCode"] = js

# 1. the On ticks send their picks; How often follows them
for nm in ["Build Step 1", "Note Toggle"]:
    p = by[nm]["parameters"]
    p["jsCode"] = sub(p["jsCode"], "    { type: 'input', block_id: 'rep_days', optional: true, label: pt('On'),",
        "    { type: 'input', block_id: 'rep_days', optional: true, dispatch_action: true, label: pt('On'),")   # v58: a tick relabels How often

p = by["Check Signature"]["parameters"]
p["jsCode"] = sub(p["jsCode"], "'repeat_toggle', 'rep_freq_pick', 'details", "'repeat_toggle', 'rep_freq_pick', 'rep_days_pick', 'details")   # v58

p = by["Note Toggle"]["parameters"]
js = p["jsCode"]
js = sub(js, "const WH = ['repeat_toggle', 'rep_freq_pick'", "const WH = ['repeat_toggle', 'rep_freq_pick', 'rep_days_pick'")
js = sub(js, "room_other_pick: 'room_other', rep_freq_pick: 'rep_freq' }[which] || which)",
    "room_other_pick: 'room_other', rep_freq_pick: 'rep_freq', rep_days_pick: 'rep_days' }[which] || which)")
js = sub(js, "const at = blocks.findIndex(b => (which === 'room_radio' || which === 'room_other_pick') ? new RegExp",
    "const at = blocks.findIndex(b => (which === 'room_radio' || which === 'room_other_pick' || which === 'rep_freq_pick' || which === 'rep_days_pick') ? new RegExp")   # v58: rep_freq / rep_days may be redrawn
js = sub(js,
    "    if (di !== -1 && fresh) { fresh.block_id = 'rep_days~' + Date.now(); blocks[di] = fresh; }\n  }\n}\n",
    "    if (di !== -1 && fresh) { fresh.block_id = 'rep_days~' + Date.now(); blocks[di] = fresh; }\n  }\n"
    "  // v58 (Howard, 29 Oct): a day ticked or unticked -> How often says what the ticks are: Mon-Fri Weekdays, all seven Daily,\n"
    "  // anything else Weekly; redrawn under a new block_id only when it changes (gotcha 47) - the ticks themselves stay as picked\n"
    "  if (which === 'rep_days_pick') {\n"
    "    const fi = blocks.findIndex(b => /^rep_freq(~\\d+)?$/.test(b.block_id || ''));\n"
    "    const t = (a.selected_options || []).map(o => o.value).sort().join();\n"
    "    const f = t === 'FR,MO,TH,TU,WE' ? 'weekdays' : t === 'FR,MO,SA,SU,TH,TU,WE' ? 'daily' : 'weekly';\n"
    "    const cur = fi !== -1 ? (((blocks[fi].element || {}).initial_option) || {}).value || 'weekly' : '';\n"
    "    const fresh = repBlocks('', { f }).find(b => b.block_id === 'rep_freq');\n"
    "    if (fi !== -1 && fresh && cur !== f) { fresh.block_id = 'rep_freq~' + Math.max(Date.now(), (Number(String(blocks[fi].block_id).split('~')[1]) || 0) + 1); blocks[fi] = fresh; }   // always a new id\n"
    "  }\n}\n")
p["jsCode"] = js

p = by["Read Step 1"]["parameters"]
js = p["jsCode"]
js = sub(js, "(v.repeat_toggle.repeat_toggle.selected_options || []).length) && !!v.rep_freq;",
    "(v.repeat_toggle.repeat_toggle.selected_options || []).length) && !!rfK;")
js = sub(js, "const repOn = ",
    "const rfK = Object.keys(v).find(k => /^rep_freq(~\\d+)?$/.test(k)) || '';   // v58: How often may be redrawn (\"rep_freq~<ms>\")\nconst repOn = ")
js = sub(js, "  const freq = (v.rep_freq.rep_freq_pick && v.rep_freq.rep_freq_pick.selected_option && v.rep_freq.rep_freq_pick.selected_option.value) || 'weekly';",
    "  const freq = (v[rfK].rep_freq_pick && v[rfK].rep_freq_pick.selected_option && v[rfK].rep_freq_pick.selected_option.value) || 'weekly';")
p["jsCode"] = js

wf["name"] = "Jessie — Slack Interactions — v58 (ticks + deadlines)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v58.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
