#!/usr/bin/env python3
"""main v202 (move direct + me fix) - PENDING 68 and 71.
  scripts/build-move-direct.py <main-live> <main-out>

68 - 30 Sep 17:18 PHT (QASER, main v201): at the yes to the 9 Nov card the model called Move Booking twice in parallel
- two replacements (one with the room declined), then "could not remove the original" for an original the first call
had already removed. Bookings (Book Direct) and cancels (Cancel Direct) skip the model at the yes; moves did not.
Now a yes to a move card goes: Cancel Direct? (no) -> Move Direct? -> Move Direct (Move Booking, once, with the card's
title / date / new times / room - Booked For's approvedMove, v200) -> Move Direct Reply (code: 'Moved "TITLE" to ...',
plus the next series card) -> Send Reply. No card, or not confirmed -> Already Done? and the model, as before.

71 - 1 Oct 09:26 (DASHING): "me" as the engineer. Booked For now reads "engineer me", "I'm the engineer", "I'll
engineer", "me as engineer", "ako ang engineer", and a bare "me" / "myself" / "ako" answer to "Who is the engineer...?"
as the requester (by their Bookers name).
"""
import json, sys, copy, uuid

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# --- Booked For: the card's Moving-to line for the reply; "me" as the engineer --------------------------------
BF1_OLD = "              date_label: String(_nl).trim().split(/,\\s*\\d{1,2}:\\d{2}/)[0],"
BF1_NEW = "              to_line: String(_ml).trim(), date_label: String(_nl).trim().split(/,\\s*\\d{1,2}:\\d{2}/)[0],"
BF2_ANCHOR = "  out.saidWords = String(out.requesterText"
BF2_BLOCK = r"""  // v202 (PENDING 71, 1 Oct DASHING): the requester naming THEMSELVES as the engineer - "me" was answered "No engineer
  // was named". "engineer me", "I'm the engineer", "I'll engineer", "me as engineer", "ako ang engineer", or a bare
  // "me" / "myself" / "ako" answer to Jessie's engineer question = the requester, by their Bookers name.
  try {
    const _meName = String(((($('Get Booker').first() || {}).json || {}).fields || {}).Name || '').trim();
    const _SELF = /\bengineer(?:ed)?\s*(?:is|:|=|will be|by)?\s*(?:me|myself)\b|\bi\s*(?:'m|’m| am| will be|'ll be|’ll be)\s+(?:the\s+)?engineer(?:ing)?\b|\bi\s*(?:'ll|’ll| will)\s+engineer\b|\bme\s+as\s+(?:the\s+)?engineer\b|\bako\s+(?:ang\s+|yung\s+)?(?:mag-?)?engineer\b/i;
    if (_meName) {
      const _lastQ = String(theirs[0] || ''), _ans1 = String(mine[0] || '').trim().replace(/[.!?]+$/, '');
      const _bare = /\bwho(?:'s|\s+is|\s+will\s+be)?\s+(?:the\s+)?engineer|\bwho'?s\s+engineering\b/i.test(_lastQ) && /^(me|myself|ako|i am|i'm|i will|i'll)$/i.test(_ans1);
      if (_bare || (!out.engineerResolved && mine.some(t => _SELF.test(t)))) { out.engineer = _meName; out.engineerResolved = true; out.engineerPhrase = _bare ? _ans1 : 'me'; out.engineerIsMe = true; }
    }
  } catch (e) {}
"""

IF_COND = "={{ ($('Gate Context').first().json.confirmedMove === true && (($('Booked For').first().json || {}).approvedMove || {}).title) ? 'yes' : 'no' }}"
AM = "(($('Booked For').first().json || {}).approvedMove || {})"
MOVE_INPUTS = {
    "title": "={{ " + AM + ".title }}",
    "booking_date": "={{ " + AM + ".booking_date }}",
    "new_start_iso": "={{ " + AM + ".new_start_iso }}",
    "new_end_iso": "={{ " + AM + ".new_end_iso }}",
    "new_rooms": "={{ " + AM + ".new_rooms || '' }}",
    "event_id": "",
    "confirmed": "={{ $('Gate Context').first().json.confirmedMove }}",
    "requester": "={{ $('Slack Trigger').first().json.user }}",
    "requester_name": "={{ $('Get Booker').first().json.fields.Name }}",
    "authority": "={{ ($('Get Booker').first().json.fields.Authority || []).map(a => (a && a.name) || a).join(', ') }}",
    "department": "={{ ($('Get Booker').first().json.fields.Department || []).map(a => (a && a.name) || a).join(', ') }}",
    "reference_data": "={{ $('Room Table').first().json.referenceData }}",
}
REPLY = r"""// Move Direct Reply (main v202, PENDING 68): the answer to a yes on a move card, from Move Booking's result - written here,
// never by the model (30 Sep: it moved two dates on one yes, then called Move Booking twice at once).
let r = {}; try { r = $input.first().json || {}; if (Array.isArray(r)) r = r[0] || {}; } catch (e) {}
const am = ((($('Booked For').first() || {}).json || {}).approvedMove) || {};
let next = ''; try { next = String((($('Booked For').first() || {}).json || {}).seriesNextCard || ''); } catch (e) {}
const st = String(r.status || '').toUpperCase(), why = String(r.reason || '').toUpperCase();
const T = {
  ROOM_OCCUPIED: "That time is taken now, so nothing was moved. Want a different time or room?",
  NOT_YOURS: "That booking was made by someone else, and you can't move it. Nothing was changed.",
  NOT_ON_CALENDAR: "I can't find that booking any more, so nothing was moved.",
  AMBIGUOUS_TITLE: "There's more than one booking with that name that day, so nothing was moved. Which one?",
  LOOKUP_FAILED: "I couldn't read the calendar just now, so nothing was moved. Please try again in a moment.",
  DURATION_INVALID: "That new time doesn't work (it ends before it starts), so nothing was moved.",
  MISSING_TIMES: "I need the new start and end, so nothing was moved.",
};
let text;
if (st === 'MOVED') text = 'Moved "' + am.title + '" to ' + (am.to_line || 'the new time') + '.' + (next ? '\n\n' + next : '');
else if (st === 'PARTIAL') text = 'The new time is booked, but the old one ("' + am.title + '") could not be removed, so it is on the calendar twice. Please delete the old one.';
else if (st === 'PREEMPT_PENDING') text = String(r.human || "That time is held by someone else - I've asked them, and I'll confirm once they reply.");
else if (T[why]) text = T[why];
else text = "I couldn't confirm that move went through. Please check the calendar before trying again.";
return [{ json: { output: text, directMove: { status: r.status || r.verdict || '', reason: r.reason || '', event_id: r.event_id || '' } } }];
"""

TL_OLD = "  let gp = null, bd = null, cd = null, ad = null;"
TL_NEW = "  let gp = null, bd = null, cd = null, ad = null, md = null;\n  try { md = $('Move Direct').first().json || null; } catch (e) {}"
TL2_OLD = "  row.Path = inp._dup ? 'duplicate dropped' : bd ? 'book direct' : cd ? 'cancel direct' : ad ? 'already done' : 'agent';"
TL2_NEW = "  row.Path = inp._dup ? 'duplicate dropped' : bd ? 'book direct' : cd ? 'cancel direct' : md ? 'move direct' : ad ? 'already done' : 'agent';"
TL3_OLD = "  row.Tools = bd ? 'Book Direct -> ' + res(bd) : cd ? 'Cancel Direct -> ' + res(cd) : clip((gp && gp.toolsLog) || '', 6000);"
TL3_NEW = "  row.Tools = bd ? 'Book Direct -> ' + res(bd) : cd ? 'Cancel Direct -> ' + res(cd) : md ? 'Move Direct -> ' + res(Array.isArray(md) ? md[0] : md) : clip((gp && gp.toolsLog) || '', 6000);"

def fix(w):
    w["name"] = "Project Jessie — v202 (move direct + me fix)"
    b = node(w, "Booked For")["parameters"]
    s = sub1(b["jsCode"], BF1_OLD, BF1_NEW, "bf1")
    b["jsCode"] = sub1(s, BF2_ANCHOR, BF2_BLOCK + BF2_ANCHOR, "bf2")
    t = node(w, "Turn Log Row")["parameters"]
    t["jsCode"] = sub1(sub1(sub1(t["jsCode"], TL_OLD, TL_NEW, "tl"), TL2_OLD, TL2_NEW, "tl2"), TL3_OLD, TL3_NEW, "tl3")
    # nodes
    cdq = node(w, "Cancel Direct?"); cdn = node(w, "Cancel Direct"); bdr = node(w, "Book Direct Reply")
    x, y = cdq["position"]
    q = copy.deepcopy(cdq); q["id"] = str(uuid.uuid4()); q["name"] = "Move Direct?"; q["position"] = [x, y + 208]
    q["parameters"]["conditions"]["conditions"][0]["id"] = str(uuid.uuid4())
    q["parameters"]["conditions"]["conditions"][0]["leftValue"] = IF_COND
    mvd = copy.deepcopy(cdn); mvd["id"] = str(uuid.uuid4()); mvd["name"] = "Move Direct"; mvd["position"] = [x + 176, y + 208]
    mvd["parameters"]["workflowId"] = {"__rl": True, "value": "t7lwR2km4tfN8DbM", "mode": "list", "cachedResultName": "Jessie — Move Booking", "cachedResultUrl": "/workflow/t7lwR2km4tfN8DbM"}
    mvd["parameters"]["workflowInputs"]["value"] = MOVE_INPUTS
    rp = copy.deepcopy(bdr); rp["id"] = str(uuid.uuid4()); rp["name"] = "Move Direct Reply"; rp["position"] = [x + 352, y + 208]
    rp["parameters"]["jsCode"] = REPLY
    w["nodes"] += [q, mvd, rp]
    # wiring: Cancel Direct? false -> Move Direct? ; Move Direct? true -> Move Direct -> Reply -> Send Reply ; false -> Already Done?
    c = w["connections"]
    br = c["Cancel Direct?"]["main"]
    if [t["node"] for t in br[1]] != ["Already Done?"]: raise SystemExit("Cancel Direct? false branch changed")
    br[1] = [{"node": "Move Direct?", "type": "main", "index": 0}]
    c["Move Direct?"] = {"main": [[{"node": "Move Direct", "type": "main", "index": 0}], [{"node": "Already Done?", "type": "main", "index": 0}]]}
    c["Move Direct"] = {"main": [[{"node": "Move Direct Reply", "type": "main", "index": 0}]]}
    c["Move Direct Reply"] = {"main": [[{"node": "Send Reply", "type": "main", "index": 0}]]}
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
