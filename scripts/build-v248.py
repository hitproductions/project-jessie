#!/usr/bin/env python3
"""main v248 + Room Availability v21 (leaks + room reply) - from the 8 Oct 22:04-22:06 Slack round on v247 (Haiku 5.5):
  - details given -> "VO Recording is a Post session, and QATEST8 has no Localization record, which is expected for Post
    work. I still need the engineer's name to prepare the booking." - internal reasoning in the reply (Anthropic's Haiku 5.5
    guide: more likely with thinking off), and an engineer requester asked for the engineer as a statement, which v207's
    question rewrite does not catch.
  - "book studio 3 ... vo recording" -> "VO Recording isn't normally run in Studio 3. The usual rooms are ..." - Room
    Availability's NOT_RUN_HERE answer, still worded by the model (Book Session v99 covers the last-resort case only).

main v248 (on v247), Guard Probe:
  1. A sentence stating internal bookkeeping is dropped - a department as a session class ("is a Post session"), a lookup
     result ("has no Localization record", "no record for"), table names, "Airtable", "reference data". Questions are kept.
  2. When Booked For knows the engineer (named and resolved, or the requester is an engineer), a statement asking for one
     ("I still need the engineer's name ...") is dropped; if nothing is left, v207's fallback question is used.
Room Availability v21 (on v20): a room asked about that is not a usual room for the session type (NOT_RUN_HERE, or
  FREE_BUT_LAST_RESORT) gets its reply in code, in Book Session v99's words: "Studio 3 isn't a usual VO Recording room -
  Studio 7, Studio 8 and Studio F are free then. One of those, or still Studio 3?"
  scripts/build-v248.py <main-v247> <main-out> <ra-v20> <ra-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

LEAKS = r"""// --- v248 (8 Oct 22:05): internal reasoning and a needless engineer ask never reach the requester -----------------------
// "VO Recording is a Post session, and QATEST8 has no Localization record, which is expected for Post work. I still need the
// engineer's name to prepare the booking." - the first sentence is the model's own bookkeeping; the second asked an engineer
// requester for an engineer, as a statement v207 does not catch. Never on a card or a code-written reply.
try {
  if (!_prepared && !_codeCard && !/\*Date:\*|\*Dates|\*Moving to:\*|Book it\?|Cancel it\?|Move it\?|Confirm to|🗓️/.test(text)) {
    const _LEAK = /\bis an? (?:Post|Localization|Advertising|Entertainment|Music|Internal|Marketing|Personal|External)(?: department)? (?:session|booking|job|work)\b|\b(?:has|have|had|found|with) no (?:\w+ ){0,2}records?\b|\bno (?:\w+ ){0,2}records? (?:for|of|in|on)\b|\b(?:Localization|Bookers|Clients|Session Types|Rooms and Studios|Localization Projects) (?:table|record|records|list|lookup)\b|\bAirtable\b|\breference data\b|\bwhich is expected for\b/i;
    const _bfL = (($('Booked For').first() || {}).json) || {};
    const _ENG = /^(?:I(?:'ll| will)? (?:still )?(?:need|have to (?:know|have)|require)|(?:I )?still need|Just need)\b[^?]*\bengineer\b[^?]*[.!]?$/i;
    const _was = text;
    text = text.split('\n').map(l => /^\s*(?:[*_•-]|❌|✅|⚠️|Heads up)/.test(l) ? l
      : l.split(/(?<=[.!?])\s+/).filter(x => /\?\s*$/.test(x) || !(_LEAK.test(x) || (_bfL.engineerResolved && _ENG.test(x.trim())))).join(' ')).join('\n').replace(/\n{3,}/g, '\n\n').trim();
    if (!text && _was) {
      const _hasClient = !!String(_bfL.client || _bfL.forClient || '').trim();
      text = _hasClient ? 'Anything else before I show you the booking?' : 'Who’s the client? (or "none")';
    }
  }
} catch (e) {}

"""

ROOMQ = r"""    // v21 (8 Oct 22:06): a room that is not a usual room for the session type - one short question, in code, in Book
    // Session v99's words (the model wrote "VO Recording isn't normally run in Studio 3. The usual rooms are ...").
    if (_hits.every(Boolean) && _hits.length === 1 && st && (priority.length || lastResort.length)
        && (_each[0].status === 'NOT_RUN_HERE' || _each[0].status === 'FREE_BUT_LAST_RESORT')) {
      const _and2 = a => a.length <= 1 ? a.join('') : a.slice(0, -1).join(', ') + ' and ' + a[a.length - 1];
      const _u = priority.filter(free), _ty = String(REQ.session_type || '').trim(), _then = reqEnd - reqStart >= 8 * 3600000 ? 'that day' : 'then';
      out.reply_text = _u.length
        ? _hits[0] + ' isn\'t a usual ' + _ty + ' room - ' + _and2(_u) + (_u.length > 1 ? ' are' : ' is') + ' free ' + _then + '. One of those, or still ' + _hits[0] + '?'
        : _hits[0] + ' isn\'t a usual ' + _ty + ' room, and none of the usual ones is free ' + _then + '. Still ' + _hits[0] + '?';
    }
"""

def main(w):
    w["name"] = "Project Jessie — v248 (leaks + room reply)"
    gp = node(w, "Guard Probe")["parameters"]
    gp["jsCode"] = once(gp["jsCode"], "// --- v247 (brevity, 8 Oct)", LEAKS + "// --- v247 (brevity, 8 Oct)", "leaks")
    return w

def ra(w):
    w["name"] = "Jessie — Room Availability — v21 (usual-room question in code)"
    n = node(w, "Compute Availability")["parameters"]
    n["jsCode"] = once(n["jsCode"], "  if (_hits.every(Boolean) && _each.every(a => a.status === 'FREE' || a.status === 'BUSY')) {",
                       ROOMQ + "  if (_hits.every(Boolean) && _each.every(a => a.status === 'FREE' || a.status === 'BUSY')) {", "room question")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 4: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(ra(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
