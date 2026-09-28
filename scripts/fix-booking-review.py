#!/usr/bin/env python3
"""Booking fixes from the 29 Sep review, applied to fresh pulls.

  scripts/fix-booking-review.py <pull-dir> <out-dir>

pull-dir holds book.json, ra.json, find.json, cancel.json, move.json (fresh `n8n pull`s). Writes
book-session-v56, room-availability-v11, find-booking-v6, cancel-booking-v17, move-booking-v24.

1. Title matching (Cancel Check Ownership, Move Resolve Booking): an untitled event never matches (it used to
   match everything through want.includes('')); only a verified id or ONE exact title is acted on; a partial or
   near title comes back as candidates to confirm.
2. All-day events: a bare date is Manila midnight, not UTC midnight (Book Check Conflicts, Room Availability,
   Move Check New Window). Google's end date stays exclusive; dateTime values are parsed as before.
3. Incomplete calendar reads: a response with nextPageToken (or an error) is refused, never read as free.
   Not paged: the busiest real day had 16 events against a 250 page.
4. Move keeps every room on the original - flagged `resource` or a known / @resource.calendar.google.com email.
"""
import json, os, re, sys

EVMS = ("// Google gives an all-day event as a bare date (\"2026-10-06\", end exclusive). new Date() reads that as UTC\n"
        "// midnight - 08:00 in Manila - so a 6-7 AM booking slipped past an all-day hold (review 29 Sep). A bare date\n"
        "// is Manila midnight; a dateTime keeps its own offset.\n"
        "const evMs = v => { const s = String(v || ''); return /^\\d{4}-\\d{2}-\\d{2}$/.test(s) ? Date.parse(s + 'T00:00:00+08:00') : new Date(s).getTime(); };\n")
EVPARSE = re.compile(r"(?:new Date\(|ms\()\s*\(?\s*((ev|e)\.(start|end)\s*&&\s*\(\2\.\3\.dateTime\s*\|\|\s*\2\.\3\.date\))\s*\)?\s*\)(?:\.getTime\(\))?")

def sub1(code, old, new, label, count=1):
    n = code.count(old)
    if n != count: raise SystemExit(f"{label}: expected {count} match(es), found {n}")
    return code.replace(old, new)

def evms(code, label, expect):
    code, n = EVPARSE.subn(lambda m: "evMs(" + m.group(1) + ")", code)
    if n != expect: raise SystemExit(f"{label}: expected {expect} event-time parses, found {n}")
    return EVMS + code

def node(w, name): return next(n for n in w["nodes"] if n["name"] == name)

def title_block(verb, tool, marker, ret):
    amb = ret("AMBIGUOUS_TITLE",
              "'Nothing was " + verb + " - more than one booking on that date is titled \"' + wantedTitle + '\":\\n'\n"
              "        + hits.map(e => '- ' + e.summary + ' ' + when(e)).join('\\n')\n"
              "        + '\\nAsk the requester which one they mean, then call " + tool + " again with that exact title.'")
    unc = ret("AMBIGUOUS_TITLE",
              "'Nothing was " + verb + " - no booking on that date is titled exactly \"' + wantedTitle + '\". Closest:\\n'\n"
              "        + cands.map(e => '- ' + e.summary + ' ' + when(e)).join('\\n')\n"
              "        + '\\nShow the requester the booking you mean with its exact title and ask them to confirm it (end with \"" + marker + "\"). Only after they reply yes, call " + tool + " again with that exact title.'")
    return ("if (!ev && wantedTitle) {\n"
            "  const want = norm(wantedTitle);\n"
            "  // Only a titled booking can match a title: an untitled event used to match every request, because\n"
            "  // want.includes('') is always true (review 29 Sep). Only ONE exact title is acted on.\n"
            "  const titled = items.filter(e => norm(e.summary));\n"
            "  const hits = titled.filter(e => norm(e.summary) === want);\n"
            "  if (hits.length === 1) { ev = hits[0]; how = 'title'; }\n"
            "  else if (hits.length > 1) " + amb + "\n"
            "  else {\n"
            "    // A partial or near title is shown back, never acted on. The model does corrupt titles it copies back\n"
            "    // (\"REazon1\" for \"REASON1\", 2026-08-30), but a near title can also be a different episode or project\n"
            "    // the same day - and a wrong booking cannot be un-" + verb + ".\n"
            "    const tol = Math.max(1, Math.floor(want.length * 0.15));\n"
            "    const cands = titled.filter(e => { const t = norm(e.summary); return t.includes(want) || want.includes(t) || dist(t, want) <= tol; });\n"
            "    if (cands.length) " + unc + "\n"
            "  }\n"
            "}\n")

def fix_titles(code, verb, tool, marker, ret, label):
    a = code.index("if (!ev && wantedTitle) {")
    b = code.index("\nif (!ev) ", a) + 1
    if code.count("if (!ev && wantedTitle) {") != 1: raise SystemExit(label + ": title block not unique")
    return code[:a] + title_block(verb, tool, marker, ret) + code[b:]

ITEMS_OLD = "const items = Array.isArray(raw.items) ? raw.items"
ITEMS_NEW = ("// A second page (nextPageToken) means this read is incomplete: refuse rather than miss a booking (review 29 Sep).\n"
             "const items = Array.isArray(raw.items) && !raw.nextPageToken ? raw.items")

def main(src, out):
    W = {k: json.load(open(os.path.join(src, k + ".json"))) for k in ("book", "ra", "find", "cancel", "move")}

    # ---- Book Session: Check Conflicts
    n = node(W["book"], "Check Conflicts"); c = n["parameters"]["jsCode"]
    c = evms(c, "book", 6)
    c = sub1(c, "  return out;\n})();\n",
             "  return out;\n})();\n"
             "// A read with a second page (nextPageToken) or an error is incomplete: never treat it as free. Google pages at\n"
             "// 250 (maxResults); the busiest real day had 16 events (21-25 Sep 2026), so this refuses instead of paging.\n"
             "if ($input.all().some(it => { const j = (it && it.json) || {}; return !!(j.nextPageToken || j.error); })) {\n"
             "  return [{ json: { verdict:'REJECTED', reason:'UNVERIFIABLE', unverifiable: [],\n"
             "    human:'The calendar could not be read completely for that window, so I could not confirm the room is free. '\n"
             "        + 'Nothing was booked - tell the requester and offer to try again in a moment.' } }];\n"
             "}\n", "book EVENTS")
    n["parameters"]["jsCode"] = c

    # ---- Room Availability: Compute Availability
    n = node(W["ra"], "Compute Availability"); c = n["parameters"]["jsCode"]
    c = evms(c, "ra", 2)
    c = sub1(c, "if (!_read || _in.some(j => j.error)) {", "if (!_read || _in.some(j => j.error || j.nextPageToken)) {", "ra read")
    n["parameters"]["jsCode"] = c

    # ---- Find Booking: Shape Results
    n = node(W["find"], "Shape Results"); c = n["parameters"]["jsCode"]
    c = sub1(c, "const items = Array.isArray(raw.items) ? raw.items : null;",
             "// A second page (nextPageToken) means this read is incomplete: say it failed rather than list half a day.\n"
             "const items = Array.isArray(raw.items) && !raw.nextPageToken ? raw.items : null;", "find items")
    n["parameters"]["jsCode"] = c

    # ---- Cancel Booking: Check Ownership
    n = node(W["cancel"], "Check Ownership"); c = n["parameters"]["jsCode"]
    c = sub1(c, ITEMS_OLD, ITEMS_NEW, "cancel items")
    ret_c = lambda reason, msg: ("{\n    return [{ json: { verdict:'REJECTED', reason:'" + reason + "',\n      human: " + msg + " } }];\n  }")
    c = fix_titles(c, "cancelled", "Cancel Booking", "Confirm to cancel. (yes/no)", ret_c, "cancel")
    n["parameters"]["jsCode"] = c

    # ---- Move Booking: Resolve Booking + Check New Window
    n = node(W["move"], "Resolve Booking"); c = n["parameters"]["jsCode"]
    c = sub1(c, ITEMS_OLD, ITEMS_NEW, "move items")
    ret_m = lambda reason, msg: ("return bad('" + reason + "',\n      " + msg + ");")
    c = fix_titles(c, "moved", "Move Booking", "Confirm to move. (yes/no)", ret_m, "move")
    c = sub1(c, "let outAttendees = (ev.attendees || []).filter(a => a.resource).map(a => ({ email: a.email }));",
             "let outAttendees = [];", "move attendees")
    i = c.index("const ROOMS = {"); j = c.index("};", i) + 2
    c = (c[:j] + "\n// Every room on the original is kept, flagged or not: only `resource: true` attendees used to be copied, so a room\n"
         "// without the flag was dropped from the replacement (review 29 Sep). A room is a known room email or any\n"
         "// @resource.calendar.google.com address. A booking that never had a room attendee (M booth holds, some\n"
         "// Localization bookings) still moves as it is - nothing is dropped from it.\n"
         "const ROOM_EMAILS = new Set(Object.values(ROOMS).map(e => String(e).toLowerCase()));\n"
         "const isRoom = a => !!a && (a.resource === true || ROOM_EMAILS.has(String(a.email || '').toLowerCase())\n"
         "  || /@resource\\.calendar\\.google\\.com$/i.test(String(a.email || '')));\n"
         "outAttendees = (ev.attendees || []).filter(isRoom).map(a => ({ email: a.email }));" + c[j:])
    n["parameters"]["jsCode"] = c

    n = node(W["move"], "Check New Window"); c = n["parameters"]["jsCode"]
    c = evms(c, "move cnw", 2)
    c = sub1(c, "if (!Array.isArray(raw.items)) {", "if (!Array.isArray(raw.items) || raw.nextPageToken) {", "move cnw read")
    n["parameters"]["jsCode"] = c

    names = {"book": ("Jessie — Book Session — v56 (v55 fixed)", "book-session-v56.json"),
             "ra": ("Jessie — Room Availability — v11 (v10 fixed)", "room-availability-v11.json"),
             "find": ("Jessie — Find Booking — v6 (v5 fixed)", "find-booking-v6.json"),
             "cancel": ("Jessie — Cancel Booking — v17 (v16 fixed)", "cancel-booking-v17.json"),
             "move": ("Jessie — Move Booking — v24 (v23 fixed)", "move-booking-v24.json")}
    for k, (title, fn) in names.items():
        W[k]["name"] = title
        json.dump(W[k], open(os.path.join(out, fn), "w"), indent=2, ensure_ascii=False)
        print("wrote", fn)

if __name__ == "__main__":
    main(*sys.argv[1:3])
