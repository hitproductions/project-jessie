#!/usr/bin/env python3
"""main v229 (vocals in-room) - QA round 3 (A3, 7 Oct): "Which rooms are vocal booths? Which record vocals in-room?" was
answered with Studios 3, 4, 5, 6, 7, 8, C, D and F for the second list. Airtable's `Records Vocals In-Room` checkbox holds
the answer - Studios 7, 8, C, D and F - but nothing in main read it: Room Table passes only the `Vocal Booth` flag, and the
Rooms and Studios tool has no filter for it, so the model inferred the list (rooms that run VO Recording - Session Types 2
gives 4, 5 and 6 as last-resort VO rooms - and rooms "Paired with Studio A, B, or D", 3-7). Studios 1-6 can record vocals
in the room only as a last resort, so they are not listed.
  - Room Table: a line beside the vocal-booth line, read from the checkbox (tick another room and it appears, no code change):
    "- Record vocals in the room itself (no booth): Studio 7 · Studio 8 · Studio C · Studio D · Studio F. ..."
  - Rooms and Studios tool: records_vocals_in_room ({Records Vocals In-Room}); asked together with vocal_booth, the two are
    OR-ed (AND would return only Studio D, which is both).
  scripts/build-vocals-in-room.py <main-v228> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
RT1_OLD = "const vocalBooths = [];\nconst otherBooths = [];"
RT1_NEW = "const vocalBooths = [];\nconst otherBooths = [];\nconst inRoom = [];   // v229: the `Records Vocals In-Room` checkbox (7, 8, C, D, F)"
RT2_OLD = "    if (f['Vocal Booth'] === true) vocalBooths.push(nm);"
RT2_NEW = "    if (f['Records Vocals In-Room'] === true) inRoom.push(nm);\n    if (f['Vocal Booth'] === true) vocalBooths.push(nm);"
RT3_OLD = "  text += '\\n' + boothLine;\n}"
RT3_NEW = """  text += '\\n' + boothLine;
}
// v229 (QA A3, 7 Oct): which rooms record vocals in the room itself comes from Airtable's checkbox, never from the session
// types a room runs or what it is paired with - asked, the model listed 3-6 too (they can, but only as a last resort).
if (inRoom.length)
  text += '\\n- Record vocals in the room itself (no booth): ' + inRoom.sort().join(' \\u00b7 ') + '. Asked which rooms record vocals '
    + 'in-room, give exactly these - never add a room because it runs VO sessions, is paired with a booth or has a microphone. '
    + 'Other studios can only as a last resort; say so only if they ask about one.';"""
F_OLD = """  var vb   = $fromAI('vocal_booth', 'True only when asked which rooms are vocal booths.', 'boolean', false);"""
F_NEW = """  var vb   = $fromAI('vocal_booth', 'True only when asked which rooms are vocal booths.', 'boolean', false);
  var vr   = $fromAI('records_vocals_in_room', 'True only when asked which rooms record vocals in the room itself, without a booth.', 'boolean', false);"""
F2_OLD = """  if (vb === true || String(vb).toLowerCase() === 'true') parts.push('{Vocal Booth}');"""
F2_NEW = """  var _vb = vb === true || String(vb).toLowerCase() === 'true', _vr = vr === true || String(vr).toLowerCase() === 'true';
  if (_vb && _vr) parts.push('OR({Vocal Booth}, {Records Vocals In-Room})');   // v229: both asked -> either (AND would be only D)
  else if (_vb) parts.push('{Vocal Booth}');
  else if (_vr) parts.push('{Records Vocals In-Room}');"""
F3_OLD = "a room name, a recording format, a kind of room, a session type, or vocal booths. Nothing was looked up."
F3_NEW = "a room name, a recording format, a kind of room, a session type, vocal booths, or rooms that record vocals in-room. Nothing was looked up."
D_OLD = "vocal_booth true returns the rooms flagged as vocal booths, which is not the same as the Recording Booth kind."
D_NEW = ("vocal_booth true returns the rooms flagged as vocal booths, which is not the same as the Recording Booth kind.\n"
         "records_vocals_in_room true returns the rooms that record vocals in the room itself (Records Vocals In-Room) - report exactly those; "
         "never work it out from the session types a room runs or what it is paired with.")
def main(w):
    w["name"] = "Project Jessie — v229 (vocals in-room)"
    rt = node(w, "Room Table")["parameters"]; s = rt["jsCode"]
    s = sub1(s, RT1_OLD, RT1_NEW, "rt1"); s = sub1(s, RT2_OLD, RT2_NEW, "rt2"); s = sub1(s, RT3_OLD, RT3_NEW, "rt3"); rt["jsCode"] = s
    p = node(w, "Rooms and Studios")["parameters"]
    p["filterByFormula"] = sub1(sub1(sub1(p["filterByFormula"], F_OLD, F_NEW, "f1"), F2_OLD, F2_NEW, "f2"), F3_OLD, F3_NEW, "f3")
    k = "toolDescription" if "toolDescription" in p else "description"
    p[k] = sub1(p[k], D_OLD, D_NEW, "desc")
    if p.get("description") and k != "description": p["description"] = p[k]
    return w
if __name__ == "__main__":
    json.dump(main(json.load(open(sys.argv[1]))), open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
