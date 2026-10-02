#!/usr/bin/env python3
"""main v213 (availability date pinned) - live 2 Oct 12:44: "can you check what studios are free tomorrow?" - Gate
Context resolved "tomorrow" = Sunday, 3 October 2027 and told the model so, and the model still asked Room Availability
for 2027-10-04 (Turn Log exec 21683). The answer was a correct reading of the wrong day. Now: Gate Context also returns
datesInMessage (the dates named in this message only, never a carried one); when exactly one is named and the model's
window is a single day on another date, Room Availability's start / end are moved to that date, times kept.
  scripts/build-window-date.py <main-live> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
G_OLD = "  datesUnderDiscussion: datesUnderDiscussion,"
G_NEW = "  datesUnderDiscussion: datesUnderDiscussion,\n  datesInMessage: Array.from(new Set(msgDates)).join(','),   // v213: named in this message only (Room Availability pins its window to it)"
FIX = "((v, s, e, g, which) => { try { const d = String(g.datesInMessage || '').split(',').map(x => x.trim()).filter(x => /^\\d{4}-\\d{2}-\\d{2}$/.test(x)); const S = String(s || '').trim(), E = String(e || '').trim(); const sd = S.slice(0, 10), ed = E.slice(0, 10); const oneDay = /^\\d{4}-\\d{2}-\\d{2}T/.test(S) && /^\\d{4}-\\d{2}-\\d{2}T/.test(E) && (sd === ed || (Date.parse(E) - Date.parse(S) <= 86400000 && /T00:00/.test(E))); if (d.length === 1 && oneDay && sd !== d[0]) { if (which === 'start') return d[0] + S.slice(10); return (ed === sd ? d[0] : new Date(Date.parse(d[0] + 'T00:00:00+08:00') + 86400000 + 8 * 3600000).toISOString().slice(0, 10)) + E.slice(10); } } catch (x) {} return v; })"
S_OLD = "={{ $fromAI('window_start', 'ISO 8601 start of the window to check, with +08:00.', 'string', '') }}"
E_OLD = "={{ $fromAI('window_end', 'ISO 8601 end of the window to check, with +08:00.', 'string', '') }}"
S_NEW = "={{ " + FIX + "($fromAI('window_start', 'ISO 8601 start of the window to check, with +08:00.', 'string', ''), $fromAI('window_start', 'ISO 8601 start of the window to check, with +08:00.', 'string', ''), $fromAI('window_end', 'ISO 8601 end of the window to check, with +08:00.', 'string', ''), ($('Gate Context').first().json || {}), 'start') }}"
E_NEW = "={{ " + FIX + "($fromAI('window_end', 'ISO 8601 end of the window to check, with +08:00.', 'string', ''), $fromAI('window_start', 'ISO 8601 start of the window to check, with +08:00.', 'string', ''), $fromAI('window_end', 'ISO 8601 end of the window to check, with +08:00.', 'string', ''), ($('Gate Context').first().json || {}), 'end') }}"
w = json.load(open(sys.argv[1])); w["name"] = "Project Jessie — v213 (availability date pinned)"
g = node(w, "Gate Context")["parameters"]; g["jsCode"] = sub1(g["jsCode"], G_OLD, G_NEW, "gate")
v = node(w, "Room Availability")["parameters"]["workflowInputs"]["value"]
v["start_iso"] = sub1(v["start_iso"], S_OLD, S_NEW, "start"); v["end_iso"] = sub1(v["end_iso"], E_OLD, E_NEW, "end")
json.dump(w, open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
