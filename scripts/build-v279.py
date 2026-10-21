#!/usr/bin/env python3
"""Builds workflows/project-jessie-v279.json - main "Project Jessie", v279 (my bookings in a room; no leaked reasoning), 22 Oct.

QA (22 Oct 00:47, Howard): "do i have studio 8 bookings" went to the AI - Mine Check only knew "do I have bookings" with nothing
in between - and the reply carried an early room-check card ("Heads up: You already have Studio 8 booked …", as if booking) and
the model's own reasoning: "Howard is asking about Studio 8 bookings with no date given. Per the rules, I need a timeframe before
calling List Events. I'll ask for it."
  1. Mine Check: "do I have … bookings / sessions" and "my … bookings" with words in between (a room, "any"); a room named
     ("studio 8", "m4", "likha") narrows the list to it. Also (Howard: the wordings the AI still got) "did I book …", "what
     (did) I book(ed)", "anything / any sessions … for me", "do I have anything …" - never with free / available / open in it,
     and "did I book" / "what I book" alone are not a booking. Form Offer no longer takes a message that starts "did I book" /
     "what did I book" for a booking request (it offered the form for "did i book m4 for monday" without a "?").
  2. Mine Reply: "*Your bookings in Studio 8* · …", only that room's; "Nothing booked for you in Studio 8 then."
  3. Guard Probe's leak filter (v248) also drops a sentence that names a tool ("List Events", "Room Availability", "Prepare
     Booking", …), "per the rules", "before calling", "I'll ask for it", or talks about the person in the third person ("… is
     asking about", "the requester").
Built on workflows/imported/project-jessie-v278-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v278-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v279.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def sub(node, a, b):
    js = by[node]["parameters"]["jsCode"]
    assert js.count(a) == 1, (node, js.count(a), a[:80])
    by[node]["parameters"]["jsCode"] = js.replace(a, b)


sub("Mine Check", r"|\bdo i have (?:any )?(?:bookings?|sessions?)\b|\bwhere am i\b/.test(t);",
    r"|\bdo i have (?:any )?(?:bookings?|sessions?)\b|\bwhere am i\b/.test(t)" + "\n"
    r"    || /\bdo i have\b[^?.!]{0,40}?\b(?:bookings?|sessions?)\b|\bmy\b[^?.!]{0,25}?\b(?:bookings?|sessions?)\b/.test(t)   // v279 (QA 22 Oct): \"do i have studio 8 bookings\"" + "\n"
    r"    || (/\bdid i (?:book|reserve)\b|\bwhat (?:did )?i (?:booked|book|reserved)\b|\bany(?:thing| bookings?| sessions?)\b(?: \w+){0,2}? for me\b|\bdo i have anything\b/.test(t)" + "\n"
    r"        && !/\b(?:free|available|availability|open|vacant)\b/.test(t));   // v279: \"did i book studio 8\", \"what i booked\", \"anything for me\", \"do i have anything tomorrow\" - never \"anything free\"")
sub("Mine Check", r"else if (/\b(?:cancel|delete|remove|move|resched\w*|change|push|extend|shorten|book)\b/.test(t)) mc.why",
    r"else if (/\b(?:cancel|delete|remove|move|resched\w*|change|push|extend|shorten|book)\b/.test(t.replace(/\b(?:did|what(?: did)?) i book\b/g, ''))) mc.why")
sub("Mine Check", "    Object.assign(mc, { go: !!mc.channel && !!mc.user, why: 'my bookings', start, end, week,",
    "    // v279: a room named narrows the list (\"do i have studio 8 bookings\")\n"
    "    const _rm = t.match(/\\bstudio\\s+([0-9]{1,2}|[a-z])\\b|\\b(m[1-8])\\b|\\b(likha|katha|salin|lobby)\\b/);\n"
    "    mc.room = !_rm ? '' : _rm[1] ? 'Studio ' + _rm[1].toUpperCase() : _rm[2] ? _rm[2].toUpperCase() : _rm[3].charAt(0).toUpperCase() + _rm[3].slice(1);\n"
    "    Object.assign(mc, { go: !!mc.channel && !!mc.user, why: 'my bookings', start, end, week,")
sub("Form Offer", r"    && !/\b(?:what|which|when|where|who|how|do i|did i|have i)\b[^?]*\b(?:book|booked)\b[^?]*\?/i.test(t);",
    r"    && !/\b(?:what|which|when|where|who|how|do i|did i|have i)\b[^?]*\b(?:book|booked)\b[^?]*\?/i.test(t)" + "\n"
    r"    && !/^\s*(?:(?:hi|hey|hello|jessie)\b[\s,!]*)?(?:(?:show me |tell me |check )?what (?:did )?i (?:book|booked|reserved?)|did i (?:book|reserve))\b/i.test(t);   // v279: \"did i book m4 for monday\" is a my-bookings question, not a booking")
sub("Form Offer", r"    const q = /\?/.test(t) || /^\s*(?:what|when",
    r"    const q = /\?/.test(t) || /^\s*(?:(?:hi|hey|hello|jessie)\b[\s,!]*)?(?:what|when")   # v279: "hey did i book studio 8 tomorrow" is a question too
sub("Mine Reply", "const blocks = [{ type: 'section', text: md('*Your bookings* · ' + head) }];",
    "const blocks = [{ type: 'section', text: md('*Your bookings' + (mc.room ? ' in ' + mc.room : '') + '* · ' + head) }];   // v279: a room asked about")
sub("Mine Reply", "    rows.push(evBooking(e));",
    "    const _b = evBooking(e);\n"
    "    if (mc.room && !String(_b.r || '').split(',').some(x => x.trim().toLowerCase() === mc.room.toLowerCase())) continue;   // v279\n"
    "    rows.push(_b);")
sub("Mine Reply", "if (!rows.length) blocks.push({ type: 'section', text: md('Nothing booked for you then.') });",
    "if (!rows.length) blocks.push({ type: 'section', text: md('Nothing booked for you' + (mc.room ? ' in ' + mc.room : '') + ' then.') });   // v279")
sub("Guard Probe", r"|\bso I need to ask\b|\bonce I have the (?:owner|details|date|time)\b/i;   // v254: + 12:26",
    r"|\bso I need to ask\b|\bonce I have the (?:owner|details|date|time)\b"
    r"|\bper the rules\b|\bbefore calling\b|\b(?:List Events|Room Availability|Find Booking|Prepare Booking|Prepare Series|Book Session|Book Series|Move Booking|Cancel Booking|Expand Series)\b"
    r"|\bI(?:'|’)?ll ask (?:for it|them|the requester)\b|\bis asking (?:about|for|to)\b|\bthe requester\b/i;   // v254: + 12:26; v279 (QA 22 Oct): tool names, rules, third person")
wf["name"] = "Project Jessie — v279 (my bookings in a room; no leaked reasoning)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT))
