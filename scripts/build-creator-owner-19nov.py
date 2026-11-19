#!/usr/bin/env python3
"""Builds the 19 Nov round (PENDING 155 / 156):

PENDING 155 - a booking made by hand in Google Calendar belongs to whoever made it (Howard, 19 Nov: the Music coordinator books
studios for others by hand and could not see them in My bookings). Google records the creator on every event; Bookers has each
person's Email and Alt email. An event created by one of the person's emails is theirs:
  - Slack Interactions v81 (Render My Bookings) and main v293 (Mine Reply, Change Reply) list it;
  - Slack Interactions v81 (To Cancel, To Move) send the person's emails as `my_emails`;
  - Cancel Booking v35 / Move Booking v44 take `my_emails`: the event's creator may cancel / change it, with or without a `ref:`
    (before: NO_REFERENCE "has to be cancelled by hand"). Move v44 also writes "Booked by: <name> | ref: <id> | Dept: <dept>" on a
    replacement that had no ref: - Jessie creates the replacement, so its creator is no longer the person (the old text is kept
    under Notes:, like the backfill).

PENDING 156 - a booking refused because of an event with no room on it (John's VSI-TRES series, 15 Nov ~18:06: "New Event", 24 Nov
9-10 AM, made by hand with no room, location or description). Book Session refused UNVERIFIABLE; the form said "Couldn't check the
calendar. Press Book again in a moment." - and Book again could never work.
  - Book Session v130 (Check Conflicts): since v125 every room's own free/busy is read, and that is what says whether a room is
    taken - an event with no room on it holds no room. When every room of the booking was read, such events no longer refuse;
    when the read failed, they refuse as before.
  - Slack Interactions v81: UNVERIFIABLE says what it is: 'An event in the calendar then has no room on it ("New Event"), so the
    room can't be confirmed free. Ask whoever made it to add the room, or remove it.'

Built on: slack-interactions-v80 (unimported; includes v79), project-jessie-v292 (== live), cancel-booking-v34, move-booking-v43,
book-session-v129 (each == live).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
W = lambda f: json.load(open(os.path.join(ROOT, "workflows", f)))


def save(wf, f, name):
    wf["name"] = name
    with open(os.path.join(ROOT, "workflows", f), "w") as fh:
        json.dump(wf, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("wrote workflows/" + f, len(wf["nodes"]), "nodes")


def rep(wf, node, old, new, count=1):
    n = [x for x in wf["nodes"] if x["name"] == node][0]
    c = n["parameters"]["jsCode"]
    assert c.count(old) == count, (wf["name"], node, old[:70], c.count(old))
    n["parameters"]["jsCode"] = c.replace(old, new)


def add_input(wf, name):
    t = [n for n in wf["nodes"] if n["type"].endswith("executeWorkflowTrigger")][0]
    vals = t["parameters"]["workflowInputs"]["values"]
    assert not any(v["name"] == name for v in vals)
    vals.append({"name": name})


CREATOR = ("// v35 Cancel / v44 Move (PENDING 155, 19 Nov): a booking made by hand in Google Calendar belongs to whoever made it - the\n"
           "// event's creator is one of the person's emails (Bookers Email / Alt email, sent by Slack Interactions v81 as my_emails)\n"
           "const _myEm = String(REQ.my_emails || '').toLowerCase().split(/[\\s,]+/).filter(x => /@/.test(x));\n"
           "const byCreator = !!(ev.creator && ev.creator.email) && _myEm.indexOf(String(ev.creator.email).toLowerCase()) !== -1;\n")

# ---- Cancel Booking v35
cx = W("cancel-booking-v34.json")
rep(cx, "Check Ownership", "const title = ev.summary || '(no title)';\n\nif (!ref) {",
    "const title = ev.summary || '(no title)';\n" + CREATOR + "\nif (!ref && !byCreator) {")
rep(cx, "Check Ownership", "const owner = ref[1] === me;", "const owner = (!!ref && ref[1] === me) || byCreator;   // v35: or its creator")
rep(cx, "Check Ownership", "const bookerRef = ref[1];", "const bookerRef = ref ? ref[1] : me;   // v35: a hand-made booking's creator")
add_input(cx, "my_emails")
save(cx, "cancel-booking-v35.json", "Jessie — Cancel Booking — v35 (hand-made: creator)")

# ---- Move Booking v44
mv = W("move-booking-v43.json")
rep(mv, "Resolve Booking", "const title = ev.summary || '(no title)';\nif (!ref) return bad('NO_REFERENCE',",
    "const title = ev.summary || '(no title)';\n" + CREATOR + "if (!ref && !byCreator) return bad('NO_REFERENCE',")
rep(mv, "Resolve Booking", "const owner = ref[1] === me;", "const owner = (!!ref && ref[1] === me) || byCreator;   // v44: or its creator")
rep(mv, "Resolve Booking", "const bookerRef = ref[1];", "const bookerRef = ref ? ref[1] : me;   // v44: a hand-made booking's creator")
rep(mv, "Resolve Booking", "  description: __desc, location: outLocation,",
    "  description: (!ref && byCreator) ? (function () {   // v44: Jessie creates the replacement - it carries who it belongs to\n"
    "    const _d0 = String(REQ.department || '').split(',')[0].trim();\n"
    "    const _line = ['Booked by: ' + (String(REQ.requester_name || '').trim() || me), 'ref: ' + me].concat(_d0 ? ['Dept: ' + _d0] : []).join(' | ');\n"
    "    const _old = String(__desc || '').trim(); return _old ? _line + '\\n\\nNotes: ' + _old : _line; })() : __desc, location: outLocation,")
add_input(mv, "my_emails")
save(mv, "move-booking-v44.json", "Jessie — Move Booking — v44 (hand-made: creator)")

# ---- Book Session v130
bs = W("book-session-v129.json")
rep(bs, "Check Conflicts", "if (unverifiable.length) {\n  const names = unverifiable.map(",
    "// v130 (PENDING 156, 19 Nov): an event with no room on it holds no room - every room's own free/busy (Room Free Busy, v125) says\n"
    "// whether a room is taken. Refused only when that read is missing for a room of this booking.\n"
    "const __fbAll = (function () { try { const _c = ((($('Room Free Busy').first() || {}).json) || {}).calendars || {};\n"
    "  return wanted.length > 0 && wanted.every(w => { const x = ROOMS[w.name] && _c[ROOMS[w.name]]; return !!x && !(x.errors && x.errors.length) && Array.isArray(x.busy); });\n"
    "} catch (e) { return false; } })();\n"
    "if (unverifiable.length && !__fbAll) {\n  const names = unverifiable.map(")
save(bs, "book-session-v130.json", "Jessie — Book Session — v130 (roomless events)")

# ---- Slack Interactions v81
si = W("slack-interactions-v80.json")
rep(si, "Render My Bookings", "    const mine = ref === W.user, onTeam = team.indexOf(W.user) !== -1;",
    "    const mine = ref === W.user || (!!(e.creator && e.creator.email) && _myEm.indexOf(String(e.creator.email).toLowerCase()) !== -1), onTeam = team.indexOf(W.user) !== -1;   // v81: or made by hand by them")
rep(si, "Render My Bookings", "const myName = String(meF.Name || '').trim().toLowerCase();",
    "const myName = String(meF.Name || '').trim().toLowerCase();\n"
    "const _myEm = [meF.Email, meF['Alt email']].map(x => String(x || '').trim().toLowerCase()).filter(x => /@/.test(x));   // v81 (PENDING 155)")
BOOKER_OLD = "  return { name: String(f.Name || ''), authority: names(f.Authority), department: names(f.Department) }; }"
BOOKER_NEW = ("  return { name: String(f.Name || ''), authority: names(f.Authority), department: names(f.Department),\n"
              "    emails: [f.Email, f['Alt email']].map(x => String(x || '').trim()).filter(x => /@/.test(x)).join(',') }; }   // v81 (PENDING 155)")
for nd in ["To Cancel", "To Move"]:
    rep(si, nd, BOOKER_OLD, BOOKER_NEW)
rep(si, "To Cancel", "  booking_time: b.s || '' } }];", "  booking_time: b.s || '', my_emails: me.emails || '' } }];")
rep(si, "To Move", "  authority: me.authority, department: me.department, requester_name: me.name, reference_data: '', booking_time: R.b.s || '',",
    "  authority: me.authority, department: me.department, requester_name: me.name, reference_data: '', booking_time: R.b.s || '', my_emails: me.emails || '',   // v81")
UNV_OLD = "  if (reason === 'NO_REFERENCE_DATA' || reason === 'UNVERIFIABLE' || reason === 'LOOKUP_FAILED' || reason === 'CALENDAR_ERROR') return { warn: 'Couldn’t check the calendar. Press *Book* again in a moment.' };   // v15; v25"
UNV_NEW = ("  if (reason === 'UNVERIFIABLE' && /cannot identify a room for \\((.+)\\), so/.test(human)) return { warn: 'An event in the calendar then has no room on it ('\n"
           "    + human.match(/cannot identify a room for \\((.+)\\), so/)[1] + '), so the room can’t be confirmed free. Ask whoever made it to add the room, or remove it.' };   // v81 (PENDING 156)\n" + UNV_OLD)
for nd in ["After Prepare", "After Book", "After Prepare Series"]:
    rep(si, nd, UNV_OLD, UNV_NEW)
save(si, "slack-interactions-v81.json", "Jessie — Slack Interactions — v81 (hand-made bookings)")

# ---- main v293
mn = W("project-jessie-v292.json")
EM = ("const _myEm = (function () { try { const g = $('Get Booker').first().json || {}; const f = g.fields || g;   // v293 (PENDING 155)\n"
      "  return [f.Email, f['Alt email']].map(x => String(x || '').trim().toLowerCase()).filter(x => /@/.test(x)); } catch (e) { return []; } })();\n"
      "const _byMe = e => !!(e && e.creator && e.creator.email) && _myEm.indexOf(String(e.creator.email).toLowerCase()) !== -1;   // made by hand by them\n")
rep(mn, "Mine Reply", "    if (ref !== mc.user && team.indexOf(mc.user) === -1) continue;",
    "    if (ref !== mc.user && team.indexOf(mc.user) === -1 && !_byMe(e)) continue;   // v293: or made by hand by them")
c = [n for n in mn["nodes"] if n["name"] == "Mine Reply"][0]["parameters"]["jsCode"]
i = c.index("const mc = ") if "const mc = " in c else None
assert i is not None
line_end = c.index("\n", i) + 1
[n for n in mn["nodes"] if n["name"] == "Mine Reply"][0]["parameters"]["jsCode"] = c[:line_end] + EM + c[line_end:]
rep(mn, "Change Reply", "  if (ref === co.user || team.indexOf(co.user) !== -1) list.push(evBooking(e));",
    "  if (ref === co.user || team.indexOf(co.user) !== -1 || _byMe(e)) list.push(evBooking(e));   // v293: or made by hand by them")
c = [n for n in mn["nodes"] if n["name"] == "Change Reply"][0]["parameters"]["jsCode"]
i = c.index("const co = ($('Change Offer')")
line_end = c.index("\n", i) + 1
[n for n in mn["nodes"] if n["name"] == "Change Reply"][0]["parameters"]["jsCode"] = c[:line_end] + EM + c[line_end:]
save(mn, "project-jessie-v293.json", "Project Jessie — v293 (hand-made bookings)")
