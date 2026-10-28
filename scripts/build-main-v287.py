#!/usr/bin/env python3
"""Builds workflows/project-jessie-v287.json - Project Jessie — v287 (several rooms asked), 28 Oct.

Howard's Slack test of v286, 28 Oct 1:40 PM: "is studio f and c free tomorrow?" was answered for Studio C only ("✅ Studio C
is free all day.", Studio F only inside the "Free all day" list). Room Availability writes the answer in code and answers
several rooms at once (each one's line, then the rest of the day without them), but which room it is asked about is the
AI's choice: its room input takes one room, and when the AI checks two rooms one call at a time Guard Probe relays the last
answer. A second room booked the whole day would have been left out of the answer altogether.

v287 (two changes, nothing else):
1. **Booked For** also hands on `askedRooms`: the rooms named in THIS message, when there are two or more - "studio f and c",
   "studios 7, 8 and c", "m3 or m4", "booth b and d", "likha and katha" - as "Studio F, Studio C" (Airtable's names, in the
   order typed). One room or none -> '' (as before). Its own try block after everything else, so it can never change the
   other fields.
2. **Room Availability** (the AI's tool): the room input is `askedRooms` when it is set, else the AI's room exactly as
   before. The AI's own input ($fromAI 'window_room') is unchanged, so the tool's schema is the same.
Room Availability itself is unchanged - it already answers "Studio F, Studio C" room by room.
Built on workflows/imported/project-jessie-v286-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "project-jessie-v286-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b):
    assert js.count(a) == 1, (js.count(a), a[:120])
    return js.replace(a, b)


# 1. Booked For: askedRooms
p = by["Booked For"]["parameters"]
js = p["jsCode"]
END = "return [{ json: out }];"
assert js.rstrip().endswith(END) and js.count(END) == 1
js = js.rstrip()[: -len(END)] + r"""// v287 (Howard, 28 Oct 1:40 PM): "is studio f and c free tomorrow?" was answered for Studio C only - the AI passed one room.
// The rooms named in THIS message, when two or more, for Room Availability's room input ('' = the AI's room, as before).
// A list goes on after "studio(s)" / "booth(s)" / an M booth: "studio f and c", "studios 7, 8 and c", "m3 or 4", "booth b and d".
// A lone lowercase "a" in a list is a word ("studio 7 and a booth"), and a number before am / pm / ":" is a time.
out.askedRooms = '';
try {
  const NAMES = $('All Rooms').all().map(i => String((((i.json || {}).fields || {})['Room Name']) || '').trim()).filter(Boolean);
  const x = String((($('Slack Trigger').first() || {}).json || {}).text || '').replace(/\*sent using\*[\s\S]*$/i, '').replace(/<[^>]*>/g, ' ').slice(0, 500);
  const hit = [], put = n => { const k = NAMES.find(r => r.toLowerCase() === n.toLowerCase()); if (k && hit.indexOf(k) === -1) hit.push(k); };
  const SEP = '\\s*(?:,\\s*(?:and|or)\\s+|,|&|\\/|\\band\\b|\\bor\\b)\\s*';
  const NOTTIME = '(?!\\s*(?:am|pm|a\\.m|p\\.m|nn|noon|:|\\.\\d|h\\b|hrs?\\b|hours?\\b|mins?\\b))';
  const all = [];
  let m;
  const rs = new RegExp('\\bstudios?\\s*([1-8a-fm])\\b' + NOTTIME + '((?:' + SEP + '(?:studio\\s*)?(?:[1-8b-fm]|A)\\b' + NOTTIME + ')*)', 'gi');
  while ((m = rs.exec(x))) {
    all.push([m.index, 'Studio ' + m[1].toUpperCase()]);
    const tail = m[2] || '', rt = new RegExp(SEP + '(?:studio\\s*)?([1-8b-fm]|A)\\b', 'gi'); let t;
    while ((t = rt.exec(tail))) if (t[1] !== 'a') all.push([m.index + 1 + t.index, 'Studio ' + t[1].toUpperCase()]);
  }
  const rm = new RegExp('(?<![\\w\'’])m(?:-?|[\\s-]?booth\\s*)([1-8])\\b' + NOTTIME + '((?:' + SEP + '(?:m(?:-?|[\\s-]?booth\\s*))?[1-8]\\b' + NOTTIME + ')*)', 'gi');
  while ((m = rm.exec(x))) {
    all.push([m.index, 'M' + m[1]]);
    const tail = m[2] || '', rt = new RegExp(SEP + '(?:m(?:-?|[\\s-]?booth\\s*))?([1-8])\\b', 'gi'); let t;
    while ((t = rt.exec(tail))) all.push([m.index + 1 + t.index, 'M' + t[1]]);
  }
  const rb = new RegExp('\\b(?:vocal\\s+)?booths?\\s+([abd])\\b((?:' + SEP + '(?:booth\\s+)?(?:[bd]|A)\\b)*)', 'gi');
  while ((m = rb.exec(x))) {
    all.push([m.index, 'Studio ' + m[1].toUpperCase()]);
    const tail = m[2] || '', rt = new RegExp(SEP + '(?:booth\\s+)?([bd]|A)\\b', 'gi'); let t;
    while ((t = rt.exec(tail))) if (t[1] !== 'a') all.push([m.index + 1 + t.index, 'Studio ' + t[1].toUpperCase()]);
  }
  const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  for (const n of NAMES) if (!/^Studio\s|^M[1-8]$/i.test(n)) { const r = new RegExp('\\b' + esc(n) + '\\b', 'i'); const k = r.exec(x); if (k) all.push([k.index, n]); }
  all.sort((p, q) => p[0] - q[0]).forEach(a => put(a[1]));
  if (hit.length >= 2) out.askedRooms = hit.slice(0, 8).join(', ');
} catch (e) { out.askedRooms = ''; }
return [{ json: out }];
"""
p["jsCode"] = js

# 2. Room Availability tool: the rooms typed, else the AI's room
v = by["Room Availability"]["parameters"]["workflowInputs"]["value"]
OLD = "={{ $fromAI('window_room', 'The room the requester named, when they named one - e.g. \"Studio 3\". Empty when they are asking what is free generally.', 'string', '') }}"
assert v["room"] == OLD, v["room"]
v["room"] = ("={{ (($('Booked For').first().json || {}).askedRooms) || $fromAI('window_room', 'The room the requester named, when they named one - "
             "e.g. \"Studio 3\". Empty when they are asking what is free generally.', 'string', '') }}")

wf["name"] = "Project Jessie — v287 (several rooms asked)"
out = os.path.join(ROOT, "workflows", "project-jessie-v287.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
