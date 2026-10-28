#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v52.json - Jessie — Slack Interactions — v52 (the one room's day), 28 Oct.

Howard's Slack test of v51, 28 Oct: Atmos Mixing at a taken time showed only "Studio C is taken then - pick another date or
time." Atmos (Studio C) and Van Recording (Studio M) have one room each, so there is nothing else to offer, and the person had
to guess a new time. Now, when that room is taken, the notice is followed by "*Studio C bookings that day:*" and each booking
in the usual card lines (title, then Time), earliest first.

How: To Room Availability asks Room Availability once more for a one-room type - the whole day (00:00-23:59), as a second item
(single date, not all day, not a series). Build Step 2 takes that second answer off before anything else reads the answers, so
the free / busy logic for the asked window is unchanged, and reads that room's bookings from its busy_detail. One extra
calendar read on Atmos / Van Recording only. Built on workflows/imported/slack-interactions-v51-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v51-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:100])
    return js.replace(a, b)


p = by["To Room Availability"]["parameters"]
p["jsCode"] = sub(p["jsCode"], "return days.map(d => ({ json: {\n",
    "const out = days.map(d => ({ json: {\n")
js = p["jsCode"]
end = "  session_type: s.kind === 'booth' ? '' : s.purpose, room: '', scope: '', hours: '', reference_data: ref\n} }));"
js = sub(js, end, end + "\n"
    "// v52 (Howard, 28 Oct): a one-room type (Atmos -> Studio C, Van Recording -> Studio M) - the whole day too, as a second item,\n"
    "// so a taken room can show its bookings that day (Build Step 2 takes it off first)\n"
    "if ((/atmos/i.test(String(s.purpose || '')) || /^van recording$/i.test(String(s.purpose || '').trim())) && days.length === 1 && !s.allDay)\n"
    "  out.push({ json: { start_iso: days[0] + 'T00:00:00+08:00', end_iso: days[0] + 'T23:59:00+08:00', session_type: s.purpose, room: '', scope: '', hours: '', reference_data: ref } });\n"
    "return out;")
p["jsCode"] = js

p = by["Build Step 2"]["parameters"]
js = p["jsCode"]
js = sub(js, "const RAS = $input.all().map(i => i.json || {});\n",
    "const RAS = $input.all().map(i => i.json || {});\n"
    "// v52: the one-room type's whole day (To Room Availability's second item) - taken off before anything reads the answers\n"
    "const RADAY = (onlyRoom(s.purpose) && RAS.length === 2 && !(s.series && (s.series.dates || []).length > 1) && !s.allDay) ? RAS.pop() : null;\n")
js = sub(js, "  blocks.push({ type: 'section', text: md(note || ('Nothing that does ' + label + ' is free then. Go *Back* and try another time.')) });\n",
    "  blocks.push({ type: 'section', text: md(note || ('Nothing that does ' + label + ' is free then. Go *Back* and try another time.')) });\n"
    "  // v52 (Howard, 28 Oct): the one room is taken - its bookings that day, in the card lines, so the next pick is not a guess\n"
    "  if (ONLY && RADAY && RADAY.status === 'OK') {\n"
    "    const _d = (RADAY.busy_detail || []).find(x => String(x.room || '').toLowerCase() === ONLY.toLowerCase());\n"
    "    const _mn = iso => { const t = Date.parse(iso || ''); return Number.isFinite(t) ? new Date(t + 8 * 3600000).toISOString().slice(11, 16) : ''; };\n"
    "    const _12 = hm => { if (!hm) return ''; let [h, m] = hm.split(':').map(Number); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(m).padStart(2, '0') + ' ' + ap; };\n"
    "    const _evs = [].concat((_d && _d.events) || []).slice().sort((a, b) => String(a.start || '').localeCompare(String(b.start || '')));\n"
    "    if (_evs.length) {\n"
    "      blocks.push({ type: 'section', text: md('*' + ONLY + ' bookings that day:*') });\n"
    "      for (const e of _evs.slice(0, 20)) blocks.push({ type: 'section', text: md(('*' + String(e.title || '(no title)') + '*\\n*Time:* '\n"
    "        + (e.allDay ? 'All day' : _12(_mn(e.start)) + ' – ' + _12(_mn(e.end)))).slice(0, 2900)) });\n"
    "    }\n"
    "  }\n")
p["jsCode"] = js

wf["name"] = "Jessie — Slack Interactions — v52 (the one room's day)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v52.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
