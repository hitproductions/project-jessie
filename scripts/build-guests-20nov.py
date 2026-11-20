#!/usr/bin/env python3
"""Guests on meetings and events (PENDING 160 (c), decided 20 Nov):
  - guests only on meetings and events for now;
  - outside emails allowed;
  - a guest in Bookers gets a Slack message and the Google invite; anyone else the Google invite only.

Slack Interactions v83
  Build Step 2   meetings / events: "Guests" (Bookers, multi-select) and "Other guests (emails)" (typed), both optional
  Read Step 2    picks -> Bookers Email (else Alt email); typed text -> every email in it (names around them ignored, a broken
                 address refused); prep.guests = the emails; guestIds (Bookers among them) / guestNames for the card
  To Prepare Series  passes guests on
  After Book     the Booked card: "*Guests:* <names / emails>"
  After Book Series  the same on the series card
  Booked Notices / Series Notices   a guest in Bookers: "<booker> invited you to a meeting / an event" with the card (no
                 Change / Cancel - it is not theirs); never twice (engineer / arranger / who it is for already told)
Book Session v133  input guests; Create Event's attendees = the rooms + the guests; sendUpdates all when there are guests
Book Series v13    input guests; stored with the series (Aggregate) and passed to each date's Book Session (Expand Dates)
Move Booking v47   the replacement keeps every non-room attendee (guests stay on a changed booking); Create Replacement and
                   Delete Original send updates (the guests get the change and the old one's cancellation)
Cancel Booking v36 Delete Event sends updates (the guests get the cancellation)
Room Check v5      Delete Declined sends updates (a guest invited seconds before gets the cancellation)

Built on: slack-interactions-v82, book-session-v132, book-series-v12, move-booking-v46, cancel-booking-v35, room-check-v4
(each == live).
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


def node(wf, name):
    return [x for x in wf["nodes"] if x["name"] == name][0]


def rep(wf, nd, old, new, count=1):
    n = node(wf, nd)
    c = n["parameters"]["jsCode"]
    assert c.count(old) == count, (wf["name"], nd, old[:80], c.count(old))
    n["parameters"]["jsCode"] = c.replace(old, new)


def add_input(wf, name):
    t = [n for n in wf["nodes"] if n["type"].endswith("executeWorkflowTrigger")][0]
    vals = t["parameters"]["workflowInputs"]["values"]
    assert not any(v["name"] == name for v in vals)
    vals.append({"name": name})


# ---------------------------------------------------------------- Slack Interactions v83
si = W("slack-interactions-v82.json")

rep(si, "Build Step 2",
    "      placeholder: { type: 'plain_text', text: 'Select a department' }, options: dOpts }, dIni ? { initial_option: dIni } : {})));\n"
    "    blocks.push(notes);\n  } else if (s.kind === 'booth') {",
    "      placeholder: { type: 'plain_text', text: 'Select a department' }, options: dOpts }, dIni ? { initial_option: dIni } : {})));\n"
    "    // v83 (Howard, 20 Nov): guests on meetings and events - people in Bookers picked (the Google invite and a message from\n"
    "    // Jessie), anyone else by email (the Google invite only). Grouped by department when there are more than 100.\n"
    "    const _gp = people.slice().sort((a, b) => a.name.localeCompare(b.name));\n"
    "    const _gSel = { type: 'multi_static_select', action_id: 'guests_pick', placeholder: { type: 'plain_text', text: 'Select people' } };\n"
    "    if (_gp.length <= 100) _gSel.options = _gp.map(popt);\n"
    "    else { const _gd = {}; for (const p of _gp) { const d = p.dept[0] || 'Other'; (_gd[d] = _gd[d] || []).push(popt(p)); }\n"
    "      _gSel.option_groups = Object.keys(_gd).sort().slice(0, 100).map(d => ({ label: { type: 'plain_text', text: d.slice(0, 75) }, options: _gd[d].slice(0, 100) })); }\n"
    "    const _gIni = _preL('gu'), _gOn = [].concat(_gSel.options || [], ...(_gSel.option_groups || []).map(g => g.options)).filter(o => _gIni.indexOf(o.value) !== -1);\n"
    "    if (_gOn.length) _gSel.initial_options = _gOn;\n"
    "    const _geEl = txtIn('guest_emails_in', ''), _ge = String(pre.ge || '').trim().slice(0, 500); if (_ge) _geEl.initial_value = _ge;\n"
    "    blocks.push(input('guests', 'Guests', _gSel, { optional: true, hint: { type: 'plain_text', text: 'They get the Google Calendar invite and a message from Jessie.' } }),\n"
    "      input('guest_emails', 'Other guests (emails)', _geEl, { optional: true, hint: { type: 'plain_text', text: 'Anyone else, inside or outside Hit. Separate emails with commas. They get the Google Calendar invite.' } }));\n"
    "    blocks.push(notes);\n  } else if (s.kind === 'booth') {")

READ_GUESTS = r"""
// v83 (Howard, 20 Nov): a meeting's / an event's guests - people picked from Bookers (their Email, else Alt email; a message from
// Jessie too) and every email typed under Other guests (the Google invite only; names around them are ignored, a broken one refused)
const __bk = (data.bookers || []).map(b => b.fields || {});
const __okEm = x => /^[^\s@,;<>()"']+@[^\s@,;<>()"']+\.[A-Za-z]{2,}$/.test(x) && !/@resource\.calendar\.google\.com$/i.test(x);
const __emOf = f => [f.Email, f['Alt email']].map(x => String(x || '').trim()).filter(__okEm);
const __byEm = e => __bk.find(f => __emOf(f).some(y => y.toLowerCase() === e)) || null;
const __sid = f => String((f && f['Slack User ID']) || '').split(/[\s,]+/).filter(Boolean)[0] || '';
const guestPick = s.kind === 'meeting' ? ((v.guests && v.guests.guests_pick && v.guests.guests_pick.selected_options) || []).map(o => o.value).filter(Boolean) : [];
const guestTyped = s.kind === 'meeting' ? String(val('guest_emails', 'guest_emails_in') || '').trim() : '';
const guestEmails = [], guestIds = [], guestNames = [], __noEm = [];
const __addG = (e, f) => { e = e.toLowerCase(); if (guestEmails.indexOf(e) !== -1) return; guestEmails.push(e);
  const id = __sid(f); if (id && guestIds.indexOf(id) === -1) guestIds.push(id); guestNames.push(f && f.Name ? String(f.Name).trim() : e); };
for (const id of guestPick) { const f = __bk.find(f => String(f['Slack User ID'] || '').split(/[\s,]+/).indexOf(id) !== -1) || null;
  const e = f ? __emOf(f)[0] : ''; if (!e) { __noEm.push((f && f.Name) || id); continue; } __addG(e, f); }
const __typed = guestTyped.match(/[^\s@,;<>()"':]+@[^\s@,;<>()"']+\.[A-Za-z]{2,}/g) || [];
const __left = __typed.reduce((t, e) => t.split(e).join(' '), guestTyped).split(/[\s,;]+/).filter(x => /@/.test(x));
for (const e of __typed) if (__okEm(e)) __addG(e, __byEm(e.toLowerCase()));
if (__noEm.length) errors.guests = 'No email on file for ' + __noEm.join(', ') + ' – type it under Other guests.';
if (__left.length) errors.guest_emails = 'Check ' + (__left.length > 1 ? 'these emails: ' : 'this email: ') + __left.slice(0, 3).join(', ');
"""
DATA_LINE = "const data = readCache($('Read Cache 3').all().map(i => i.json || {})) || { bookers: [], rooms: [], sessionTypes: [] };\n"
rep(si, "Read Step 2", DATA_LINE, DATA_LINE + READ_GUESTS.lstrip("\n"))
rep(si, "Read Step 2", "  request_ok: !!askK   // v37",
    "  request_ok: !!askK, guests: guestEmails.join(',')   // v83: the guests' emails; v37")
rep(si, "Read Step 2", "  nt: notes.slice(0, 600) };",
    "  nt: notes.slice(0, 600), gu: guestPick.join(','), ge: guestTyped.slice(0, 500) };   // v83: the guests")
rep(si, "Read Step 2", "return [{ json: { ask: askK, valid, calTitle,",
    "return [{ json: { guests: guestEmails.join(','), guestIds: guestIds.join(','), guestNames: guestNames.join(', '), ask: askK, valid, calTitle,")

rep(si, "To Prepare Series", "description: T.description,",
    "description: T.description, guests: T.guests || '',   // v83")

rep(si, "After Book", "  + noteLine(evNote({ description: (A.book || {}).description }));   // v44: the note",
    "  + (R.guestNames ? '\\n*Guests:* ' + R.guestNames : '')   // v83\n"
    "  + noteLine(evNote({ description: (A.book || {}).description }));   // v44: the note")

GLINE = (
    "const __gLine = (function () { try { const g = String(T.guests || '').split(/[\\s,;]+/).filter(x => /@/.test(x)); if (!g.length) return '';   // v83: the guests\n"
    "  let B = []; try { const rows = $('Read Cache 8').all().map(i => i.json || {}).filter(r => r.cache_key === 'jessie-reference')\n"
    "    .sort((a, b) => (Date.parse(b.refreshed_at || '') || 0) - (Date.parse(a.refreshed_at || '') || 0)); B = ((JSON.parse(rows[0].payload) || {}).bookers || []).map(b => b.fields || {}); } catch (e) { B = []; }\n"
    "  return '\\n*Guests:* ' + g.map(e => { const f = B.find(f => [f.Email, f['Alt email']].some(y => String(y || '').trim().toLowerCase() === e.toLowerCase()));\n"
    "    return f && f.Name ? String(f.Name).trim() : e; }).join(', '); } catch (e) { return ''; } })();\n")
rep(si, "After Book Series", "const T = $('To Book Series').first().json;\n", "const T = $('To Book Series').first().json;\n" + GLINE)
rep(si, "After Book Series",
    "(T.rooms ? '\\n*Room:* ' + roomMain(T.rooms) + (roomHold(T.rooms) ? '\\n*Holding room:* ' + roomHold(T.rooms) : '') : '')",
    "(T.rooms ? '\\n*Room:* ' + roomMain(T.rooms) + (roomHold(T.rooms) ? '\\n*Holding room:* ' + roomHold(T.rooms) : '') : '') + __gLine")

rep(si, "Booked Notices", "return notices([].concat(_ids(R.engineerId)", "const __n1 = notices([].concat(_ids(R.engineerId)")
rep(si, "Booked Notices", "me, whoIs(data, me) || 'Someone', body, bk);",
    "me, whoIs(data, me) || 'Someone', body, bk);\n"
    "// v83 (Howard, 20 Nov): a meeting's / an event's guests in Bookers are told too (anyone else gets the Google invite only) - without\n"
    "// Change / Cancel, the booking is not theirs; never twice (the engineer, arranger or who it is for was told above)\n"
    "const __told = new Set([me].concat(_ids(R.engineerId), _ids(R.arrangerId), [R.forId]).filter(Boolean));\n"
    "const __what = /^event$/i.test(String((R.s || {}).purpose || '')) ? 'an event' : 'a meeting';\n"
    "return __n1.concat(notices(_ids(R.guestIds).filter(id => !__told.has(id)).map(id => ({ id, line: 'invited you to ' + __what, name: whoIs(data, id) })),\n"
    "  me, whoIs(data, me) || 'Someone', body, null));")

rep(si, "Series Notices", "return notices(team.map(id =>", "const __n1 = notices(team.map(id =>")
rep(si, "Series Notices", "R.user, whoIs(data, R.user) || 'Someone', body);",
    "R.user, whoIs(data, R.user) || 'Someone', body);\n"
    "// v83 (Howard, 20 Nov): the series' guests in Bookers are told once, with the dates (anyone else: the Google invites only)\n"
    "const __B = (data.bookers || []).map(b => b.fields || {});\n"
    "const __gid = String(T.guests || '').split(/[\\s,;]+/).filter(x => /@/.test(x)).map(e => { const f = __B.find(f => [f.Email, f['Alt email']].some(y => String(y || '').trim().toLowerCase() === e.toLowerCase()));\n"
    "  return f ? String(f['Slack User ID'] || '').split(/[\\s,]+/).filter(Boolean)[0] || '' : ''; }).filter((x, i, a) => x && a.indexOf(x) === i);\n"
    "const __told = new Set([R.user].concat(team));\n"
    "const __what = /^event$/i.test(String(T.session_type || '')) ? 'an event' : 'a meeting';\n"
    "return __n1.concat(notices(__gid.filter(id => !__told.has(id)).map(id => ({ id, line: 'invited you to ' + __what + (n ? ' on ' + n + ' dates' : ''), name: whoIs(data, id) })),\n"
    "  R.user, whoIs(data, R.user) || 'Someone', body));")
save(si, "slack-interactions-v83.json", "Jessie — Slack Interactions — v83 (guests)")

# ---------------------------------------------------------------- Book Session v133
bs = W("book-session-v132.json")
add_input(bs, "guests")
ce = node(bs, "Create Event")
af = ce["parameters"]["additionalFields"]
OLD = "return ids.join(','); })() }}"
assert af["attendees"][0].count(OLD) == 1
af["attendees"][0] = af["attendees"][0].replace(OLD,
    "const _g = String($('When Executed by Another Workflow').first().json.guests || '').split(/[\\s,;]+/).map(function(x){ return x.trim().toLowerCase(); })"
    ".filter(function(x, i, a){ return /^[^\\s@,;<>()\"']+@[^\\s@,;<>()\"']+\\.[a-z]{2,}$/.test(x) && !/@resource\\.calendar\\.google\\.com$/.test(x) && a.indexOf(x) === i; }); "
    "return ids.concat(_g).join(','); })() }}")
assert "sendUpdates" not in af
af["sendUpdates"] = "={{ /@/.test(String($('When Executed by Another Workflow').first().json.guests || '')) ? 'all' : 'none' }}"
save(bs, "book-session-v133.json", "Jessie — Book Session — v133 (guests)")

# ---------------------------------------------------------------- Book Series v13
bser = W("book-series-v12.json")
add_input(bser, "guests")
rep(bser, "Expand Dates", "    client: REQ.client || '', engineer: REQ.engineer || '',\n",
    "    client: REQ.client || '', engineer: REQ.engineer || '', guests: REQ.guests || '',   // v13: meeting / event guests\n")
rep(bser, "Aggregate", "    requester_text: String(REQ0.requester_text || ''), per_date: JSON.stringify(perDate),",
    "    requester_text: String(REQ0.requester_text || ''), per_date: JSON.stringify(perDate), guests: String(REQ0.guests || ''),   // v13: guests")
save(bser, "book-series-v13.json", "Jessie — Book Series — v13 (guests)")

# ---------------------------------------------------------------- Move Booking v47
mv = W("move-booking-v46.json")
rep(mv, "Resolve Booking", "// Notify the booker (and assigned engineer",
    "// v47 (20 Nov): the guests stay on the changed booking (a meeting's / an event's, or a hand-made event's) - only the rooms change;\n"
    "// Create Replacement / Delete Original send updates, so Google tells them\n"
    "outAttendees = outAttendees.concat((ev.attendees || []).filter(a => a && a.email && !isRoom(a) && !a.self)\n"
    "  .map(a => Object.assign({ email: a.email }, a.optional ? { optional: true } : {})));\n"
    "// Notify the booker (and assigned engineer")
for nd in ["Create Replacement", "Delete Original"]:
    p = node(mv, nd)["parameters"]
    assert "sendUpdates" not in p["url"]
    if nd == "Create Replacement":
        assert p["url"].endswith("/events"), p["url"]
        p["url"] += "?sendUpdates=all"
    else:
        assert p["url"].endswith("original_id) }}"), p["url"]
        p["url"] += "?sendUpdates=all"
save(mv, "move-booking-v47.json", "Jessie — Move Booking — v47 (guests kept)")

# ---------------------------------------------------------------- Cancel Booking v36
cx = W("cancel-booking-v35.json")
de = node(cx, "Delete Event")["parameters"]
assert de.get("options") == {}, de.get("options")
de["options"] = {"sendUpdates": "all"}
save(cx, "cancel-booking-v36.json", "Jessie — Cancel Booking — v36 (guests told)")

# ---------------------------------------------------------------- Room Check v5
rc = W("room-check-v4.json")
p = node(rc, "Delete Declined")["parameters"]
assert p["url"].endswith("event_id || '')) }}"), p["url"]
p["url"] += "?sendUpdates=all"
save(rc, "room-check-v5.json", "Jessie — Room Check — v5 (guests told)")
