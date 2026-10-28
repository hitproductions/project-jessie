#!/usr/bin/env python3
"""Builds workflows/slack-interactions-v56.json - Jessie — Slack Interactions — v56 (all day repeats), 29 Oct.

Howard's Slack test, 29 Oct: an M booth, All day booking ticked, Repeats ticked (weekly, Mon) - step 1 refused it with "All day
books one date - untick Repeats, or untick All day and pick the times." M booths are usually held all day, and on several dates.

The refusal was a v21 simplification (round 4, "one date only"), not a limit of the booking side: Book Series has carried all_day
since v4 (Expand Dates gives each date 12:00 AM to 12:00 AM the next day, the same event a single all-day booking makes, and
Aggregate stores all_day with the series). The form never passed it on: To Prepare Series sent all_day: false with 00:00 / 23:59,
which would have booked timed 12:00 AM - 11:59 PM events.

v56: step 1 lets All day and Repeats go together (M booth and Event, the two that have All day); To Prepare Series passes all_day
(and no times); the series' confirm meta says all day, so the Booking… message and the result say "All day" instead of a time.
Everything else in the series path already reads all-day bookings (Room Availability per date over the whole day, the card's Time
line from Book Session, the notices, My bookings, Reminders). Built on workflows/imported/slack-interactions-v55-imported.json
(the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "slack-interactions-v55-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:140])
    return js.replace(a, b)


p = by["Read Step 1"]["parameters"]
p["jsCode"] = sub(p["jsCode"],
    "if (allDay && repOn) errors.purpose = 'All day books one date - untick Repeats, or untick All day and pick the times.';   // v21\n",
    "// v56 (Howard, 29 Oct): All day and Repeats go together - M booths are held all day on several dates (v21 refused it)\n")

p = by["To Prepare Series"]["parameters"]
p["jsCode"] = sub(p["jsCode"],
    "time_start: R.s.t0, time_end: R.s.t1, all_day: false,",
    "time_start: R.s.allDay ? '' : R.s.t0, time_end: R.s.allDay ? '' : R.s.t1, all_day: !!R.s.allDay,   // v56: all day too")

p = by["After Prepare Series"]["parameters"]
p["jsCode"] = sub(p["jsCode"],
    "  time: R.s.t0 + '-' + R.s.t1, rooms: R.rooms || '' };",
    "  time: R.s.allDay ? '' : R.s.t0 + '-' + R.s.t1, ad: R.s.allDay ? 1 : 0, rooms: R.rooms || '' };   // v56: ad - all day, no time")

p = by["After Book Series"]["parameters"]
p["jsCode"] = sub(p["jsCode"],
    "(tm[0] ? '\\n*Time:* ' + t12(tm[0]) + ' – ' + t12(tm[1]) : '')",
    "(R.meta.ad ? '\\n*Time:* All day' : tm[0] ? '\\n*Time:* ' + t12(tm[0]) + ' – ' + t12(tm[1]) : '')")   # v56

p = by["Mark Source Series"]["parameters"]
p["jsCode"] = sub(p["jsCode"],
    "tm.length === 2 ? srcT(tm[0]) + ' – ' + srcT(tm[1]) : ''",
    "M.ad ? 'All day' : tm.length === 2 ? srcT(tm[0]) + ' – ' + srcT(tm[1]) : ''")   # v56

wf["name"] = "Jessie — Slack Interactions — v56 (all day repeats)"
out = os.path.join(ROOT, "workflows", "slack-interactions-v56.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
