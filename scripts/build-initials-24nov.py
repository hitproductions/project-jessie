#!/usr/bin/env python3
"""PENDING 161 (Howard, 24 Nov): a booking made by hand in Google Calendar is also the person's whose initials end its title.
A coordinator made "ATE / Client / HL" by hand for Howard; it showed only in the coordinator's My bookings (the creator, PENDING 155).

The rule, everywhere: an event Jessie did not make - no `ref:` and no `team:` on its first line - whose title ends, after " / " or
" | ", in initials only ("HL", "HL x MV", "HL AEG") belongs also to each person those initials are in Bookers. Initials two people
share go to the one with Client Booking authority (the one who books studios); still shared, nobody. Jessie's own bookings
(ref: / team:) are read exactly as before - the initials never add anyone to them.

  Slack Interactions v88: My bookings lists them ("You're on the team"); To Cancel / To Move send `people` (each Bookers email ->
    [Slack id, name], each initials -> its one owner); byIni (the Change form's people from a title) uses the same shared rule.
  Cancel v37 / Move v49: the initials' owner may cancel / change it (option b); the creator is told (bookerRef from `people`);
    the engineer(s) by initials are told when someone else acts. Move's replacement of a hand-made booking carries
    "Booked by | ref | (Dept) | team:" - the creator as booker, the initials' owners as team - so neither loses it.
  Reminders v12: the initials' owners get the reminder, when the booking names nobody (no ref:, no team:, no Engineer: / Arranger:).
  main v301: typed "my bookings" (Mine Reply) and typed changes (Change Reply) list them too.
Built on slack-interactions-v87, cancel-booking-v36, move-booking-v48, reminders-v11, project-jessie-v300 (each == live)."""
import json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
W = lambda f: json.load(open(os.path.join(ROOT, "workflows", f)))
def save(wf, f, name):
    wf["name"] = name
    with open(os.path.join(ROOT, "workflows", f), "w") as fh:
        json.dump(wf, fh, indent=2, ensure_ascii=False); fh.write("\n")
    print("wrote workflows/" + f, len(wf["nodes"]), "nodes")
def node(wf, nd): return [x for x in wf["nodes"] if x["name"] == nd][0]
def rep(wf, nd, old, new, count=1):
    n = node(wf, nd); c = n["parameters"]["jsCode"]
    assert c.count(old) == count, (nd, old[:80], c.count(old)); n["parameters"]["jsCode"] = c.replace(old, new)
def pre(wf, nd, code): n = node(wf, nd); n["parameters"]["jsCode"] = code + n["parameters"]["jsCode"]
def add_input(wf, name):
    t = node(wf, "When Executed by Another Workflow"); vals = t["parameters"]["workflowInputs"]["values"]
    assert not any(v["name"] == name for v in vals); vals.append({"name": name})

# The shared helpers (the same text in every node that uses them)
H = (
"// PENDING 161 (24 Nov): a booking made by hand (no ref:, no team:) is also the person's whose initials end its title, after\n"
"// \" / \" or \" | \" (\"ATE / Client / HL\", \"VSI-TRES | MT\", \"X / HL x MV\"). Only a last part that is all initials counts.\n"
"function _p161Inits(t) { const s = String(t || '').split(/\\s*[\\/|]\\s*/); if (s.length < 2) return [];\n"
"  const w = s[s.length - 1].trim().split(/\\s+x\\s+|\\s*[,+&]\\s*|\\s+/i).filter(Boolean);\n"
"  return w.length && w.every(x => /^[A-Z]{2,4}$/.test(x)) ? w : []; }\n"
"// Initials two people share (in Bookers) go to the one with Client Booking authority - the one who books studios; still shared, nobody\n"
"function _p161Owner(fs, ini) { const q = String(ini || '').trim().toUpperCase(); if (!q) return null;\n"
"  let h = (fs || []).filter(f => f && String(f.Initials || '').trim().toUpperCase() === q);\n"
"  if (h.length > 1) h = h.filter(f => [].concat(f.Authority || []).some(a => /^client booking$/i.test(String((a && a.name) || a).trim())));\n"
"  return h.length === 1 ? h[0] : null; }\n")
SID = "const _p161Id = f => String((f && f['Slack User ID']) || '').split(/[\\s,]+/).filter(Boolean)[0] || '';\n"
# My initials, when they are mine alone (by the rule above)
MYINI = ("function _p161Mine(fs, me) { const o = me && me.Initials ? _p161Owner(fs, me.Initials) : null;\n"
         "  return o && _p161Id(o) && _p161Id(o) === _p161Id(me) ? String(me.Initials).trim().toUpperCase() : ''; }\n")

# ---------------------------------------------------------------- Slack Interactions v88
si = W("slack-interactions-v87.json")
# My bookings
pre(si, "Render My Bookings", H + SID + MYINI)
rep(si, "Render My Bookings",
    "const _myEm = [meF.Email, meF['Alt email']]",
    "const _myIni = _p161Mine((data.bookers || []).map(b => b.fields || {}), meF);   // v88 (PENDING 161)\n"
    "const _myEm = [meF.Email, meF['Alt email']]")
rep(si, "Render My Bookings",
    "    if (!mine && !onTeam) continue;",
    "    const byIni = !mine && !onTeam && !ref && !team.length && !!_myIni && _p161Inits(e.summary).indexOf(_myIni) !== -1;   // v88 (PENDING 161): made by hand, their initials on it\n"
    "    if (!mine && !onTeam && !byIni) continue;")
# people for Cancel / Move
PEOPLE = ("// v88 (PENDING 161): each Bookers email -> [Slack id, name], and each initials -> its one owner (shared: Client Booking), for\n"
          "// Cancel / Move to tell a hand-made booking's creator and to let the person whose initials end its title cancel / change it\n"
          "function peopleMap(data) { const fs = ((data && data.bookers) || []).map(b => b.fields || {}), e = {}, i = {};\n"
          "  for (const f of fs) { const u = _p161Id(f); if (!u) continue;\n"
          "    for (const m of [f.Email, f['Alt email']]) { const k = String(m || '').trim().toLowerCase(); if (/@/.test(k)) e[k] = [u, String(f.Name || '').trim()]; }\n"
          "    const q = String(f.Initials || '').trim().toUpperCase(); if (q && !(q in i)) { const o = _p161Owner(fs, q); i[q] = o ? _p161Id(o) : ''; } }\n"
          "  return JSON.stringify({ e, i }); }\n")
pre(si, "To Cancel", H + SID + PEOPLE)
rep(si, "To Cancel",
    "const me = booker(readCache($('Read Cache 5').all().map(i => i.json || {})) || { bookers: [] }, c.user);",
    "const _data = readCache($('Read Cache 5').all().map(i => i.json || {})) || { bookers: [] };   // v88\n"
    "const me = booker(_data, c.user);")
rep(si, "To Cancel", "booking_time: b.s || '', my_emails: me.emails || '' } }];",
    "booking_time: b.s || '', my_emails: me.emails || '', people: peopleMap(_data) } }];   // v88: people")
pre(si, "To Move", H + SID + PEOPLE)
rep(si, "To Move", "booking_time: R.b.s || '', my_emails: me.emails || '',   // v81",
    "booking_time: R.b.s || '', my_emails: me.emails || '', people: peopleMap(data),   // v81; v88: people")
# byIni: the Change form's people from a title - the same shared rule
STAFF_OLD = "  return { name: String(f.Name || '').trim(), info: String(f.Info || ''), ini: String(f.Initials || '').trim(), dept: [].concat(f.Department || []),"
STAFF_NEW = ("  return { name: String(f.Name || '').trim(), info: String(f.Info || ''), ini: String(f.Initials || '').trim(), dept: [].concat(f.Department || []),\n"
             "           auth: [].concat(f.Authority || []).map(a => String((a && a.name) || a).trim().toLowerCase()),   // v88 (PENDING 161)")
BYINI_OLD = "function byIni(st, ini) { const h = st.filter(x => ini && x.ini.toLowerCase() === String(ini).toLowerCase()); return h.length === 1 ? h[0] : null; }"
BYINI_NEW = ("function byIni(st, ini) { let h = st.filter(x => ini && x.ini.toLowerCase() === String(ini).toLowerCase());\n"
             "  if (h.length > 1) h = h.filter(x => (x.auth || []).indexOf('client booking') !== -1);   // v88 (PENDING 161): shared initials - the one who books studios\n"
             "  return h.length === 1 ? h[0] : null; }")
for nd in ["Build Change", "Read Change", "To Move", "After Move", "Note Toggle", "Build Change C"]:
    rep(si, nd, STAFF_OLD, STAFF_NEW); rep(si, nd, BYINI_OLD, BYINI_NEW)
save(si, "slack-interactions-v88.json", "Jessie — Slack Interactions — v88 (initials on hand-made)")

# ---------------------------------------------------------------- Cancel v37
OWN = (
"// v37 Cancel / v49 Move (PENDING 161, 24 Nov): a booking made by hand (no ref:, no team:) is also the person's whose initials end\n"
"// its title - `people` (Slack Interactions v88) maps each initials to its one owner, and each Bookers email to [Slack id, name]\n"
"let _P = { e: {}, i: {} }; try { _P = JSON.parse(String(REQ.people || '') || '{}') || _P; } catch (e) {}\n"
"const _Pe = (_P && _P.e) || {}, _Pi = (_P && _P.i) || {};\n"
"const _team0 = ((__H.match(/team:\\s*([^|\\n]+)/) || [])[1] || '').split(/[\\s,]+/).filter(Boolean);\n"
"const _iniIds = !ref && !_team0.length ? _p161Inits(title).map(x => _Pi[x] || '').filter((x, i, a) => x && a.indexOf(x) === i) : [];\n"
"const byInitials = !!me && _iniIds.indexOf(me) !== -1;\n"
"const _crP = (ev.creator && ev.creator.email && _Pe[String(ev.creator.email).toLowerCase()]) || null;   // [Slack id, name] of whoever made it\n")
cx = W("cancel-booking-v36.json")
add_input(cx, "people")
pre(cx, "Check Ownership", H)
rep(cx, "Check Ownership",
    "if (!ref && !byCreator) {\n  return [{ json: { verdict:'REJECTED', reason:'NO_REFERENCE', title,",
    OWN.replace("__H", "desc") +
    "if (!ref && !byCreator && !byInitials) {\n  return [{ json: { verdict:'REJECTED', reason:'NO_REFERENCE', title,")
rep(cx, "Check Ownership", "if (!(owner || onTeam || isHaistDev || coordInDept)) {",
    "if (!(owner || onTeam || byInitials || isHaistDev || coordInDept)) {   // v37: or their initials on a hand-made booking")
rep(cx, "Check Ownership", "concat(owner ? [] : ['*Booked by:* ' + (who || 'unknown')])",
    "concat(owner ? [] : ['*Booked by:* ' + (who || (_crP && _crP[1]) || 'unknown')])")
rep(cx, "Check Ownership", "const notify = !owner || team.some(id => id !== me) || (!team.length && !!(engInitials0 || engName0));",
    "const _nTeam = team.length ? team : _iniIds;   // v37: a hand-made booking's people by initials\n"
    "const notify = !owner || _nTeam.some(id => id !== me) || (!team.length && !!(engInitials0 || engName0));")
rep(cx, "Check Ownership", "const bookerRef = ref ? ref[1] : me;   // v35: a hand-made booking's creator",
    "const bookerRef = ref ? ref[1] : byCreator ? me : ((_crP && _crP[0]) || me);   // v35: a hand-made booking's creator; v37: told when someone else cancels it")
rep(cx, "Check Ownership", "const bookerName = who || 'the booker';", "const bookerName = who || (_crP && _crP[1]) || 'the booker';")
rep(cx, "Check Ownership", "return [{ json: { verdict:'CLEAR', event_id: ev.id, title, matched_on: how, team,   // v28: the team, for the notices",
    "return [{ json: { verdict:'CLEAR', event_id: ev.id, title, matched_on: how, team: _nTeam,   // v28: the team, for the notices (v37: or by initials)")
save(cx, "cancel-booking-v37.json", "Jessie — Cancel Booking — v37 (initials on hand-made)")

# ---------------------------------------------------------------- Move v49
mv = W("move-booking-v48.json")
add_input(mv, "people")
pre(mv, "Resolve Booking", H)
rep(mv, "Resolve Booking",
    "if (!ref && !byCreator) return bad('NO_REFERENCE',",
    OWN.replace("__H", "descH") + "if (!ref && !byCreator && !byInitials) return bad('NO_REFERENCE',")
rep(mv, "Resolve Booking", "if (!(owner || onTeam || isHaistDev || coordInDept)) return bad('NOT_YOURS',",
    "if (!(owner || onTeam || byInitials || isHaistDev || coordInDept)) return bad('NOT_YOURS',   // v49: or their initials on a hand-made booking")
rep(mv, "Resolve Booking", "const notify = !owner || team.some(id => id !== me) || (!team.length && !!(engInitials0 || engName0));",
    "const _nTeam = team.length ? team : _iniIds;   // v49: a hand-made booking's people by initials\n"
    "const notify = !owner || _nTeam.some(id => id !== me) || (!team.length && !!(engInitials0 || engName0));")
rep(mv, "Resolve Booking", "const bookerRef = ref ? ref[1] : me;   // v44: a hand-made booking's creator",
    "const bookerRef = ref ? ref[1] : byCreator ? me : ((_crP && _crP[0]) || me);   // v44: a hand-made booking's creator; v49: told when someone else changes it")
rep(mv, "Resolve Booking", "const bookerName = (by && by[1] && by[1].trim()) || 'the booker';",
    "const bookerName = (by && by[1] && by[1].trim()) || (_crP && _crP[1]) || 'the booker';")
OLD_DESC = (
"  description: (!ref && byCreator) ? (function () {   // v44: Jessie creates the replacement - it carries who it belongs to\n"
"    const _d0 = String(REQ.department || '').split(',')[0].trim();\n"
"    const _line = ['Booked by: ' + (String(REQ.requester_name || '').trim() || me), 'ref: ' + me].concat(_d0 ? ['Dept: ' + _d0] : []).join(' | ');\n"
"    const _old = String(__desc || '').trim(); return _old ? _line + '\\n\\nNotes: ' + _old : _line; })() : __desc, location: outLocation, attendees: outAttendees,\n")
NEW_DESC = "  description: __outDesc, location: outLocation, attendees: outAttendees,\n"
rep(mv, "Resolve Booking", OLD_DESC, NEW_DESC)
rep(mv, "Resolve Booking",
    "  new_team: ((_hd(__desc).match(/team:\\s*([^|\\n]+)/) || [])[1] || '').split(/[\\s,]+/).filter(Boolean), team_changed: __teamChanged,   // v39: taken off",
    "  new_team: ((_hd(__outDesc).match(/team:\\s*([^|\\n]+)/) || [])[1] || '').split(/[\\s,]+/).filter(Boolean), team_changed: __teamChanged,   // v39: taken off")
rep(mv, "Resolve Booking",
    "return [{ json: { verdict:'CLEAR', matched_on: how, original_id: ev.id, title: __title, team, color_id: __colour,   // v31: team for the notices",
    "// v44: Jessie creates the replacement of a hand-made booking - it carries who it belongs to (\"Booked by | ref | Dept\").\n"
    "// v49 (PENDING 161): the creator stays the booker when the person whose initials end the title changes it, and those people go\n"
    "// on team: (the replacement has a ref:, so its title's initials no longer count) - neither loses it. The team the Change form\n"
    "// picked wins; it moves to the first line, never left under Notes.\n"
    "const __outDesc = !ref ? (function () {\n"
    "  const _own = byCreator ? [String(REQ.requester_name || '').trim() || me, me] : (_crP ? [_crP[1] || _crP[0], _crP[0]] : null);\n"
    "  const _d0 = byCreator ? String(REQ.department || '').split(',')[0].trim() : '';\n"
    "  const _tf = ((_hd(__desc).match(/team:\\s*([^|\\n]+)/) || [])[1] || '').split(/[\\s,]+/).filter(Boolean);\n"
    "  const _tm = /team:/.test(_hd(__desc)) ? _tf : _iniIds;\n"
    "  const _parts = (_own ? ['Booked by: ' + _own[0], 'ref: ' + _own[1]] : []).concat(_d0 ? ['Dept: ' + _d0] : []).concat(_tm.length ? ['team: ' + _tm.join(' ')] : []);\n"
    "  if (!_own && !_tm.length) return __desc;\n"
    "  const _old = String(__desc || '').replace(/(^|\\s*\\|\\s*)team:\\s*[^|\\n]*/, '').replace(/^\\s*\\|\\s*/, '').trim();\n"
    "  return _old ? _parts.join(' | ') + '\\n\\nNotes: ' + _old : _parts.join(' | '); })() : __desc;\n"
    "return [{ json: { verdict:'CLEAR', matched_on: how, original_id: ev.id, title: __title, team: _nTeam, color_id: __colour,   // v31: team for the notices (v49: or by initials)")
save(mv, "move-booking-v49.json", "Jessie — Move Booking — v49 (initials on hand-made)")

# ---------------------------------------------------------------- Reminders v12
rm = W("reminders-v11.json")
pre(rm, "Build Reminders", H)
rep(rm, "Build Reminders",
    "  if (!ref && !byCreator) continue;   // made through Jessie, or by hand by a booker\n",
    "  // v12 (PENDING 161): a booking made by hand that names nobody (no team:, no Engineer: / Arranger:) - the people whose initials end\n"
    "  // its title get the reminder too (shared initials: the one with Client Booking authority)\n"
    "  const _named0 = !ref && !/team:/.test(desc) && !/(?:Engineer|Arranger):/.test(desc);\n"
    "  const iniIds = _named0 ? _p161Inits(e.summary).map(x => _p161Owner(staff, x)).filter(Boolean).map(idOf).filter(Boolean) : [];\n"
    "  if (!ref && !byCreator && !iniIds.length) continue;   // made through Jessie, or by hand by a booker (v12: or for someone by their initials)\n")
rep(rm, "Build Reminders",
    "  for (const id of [...new Set([ref, byCreator].filter(Boolean).concat(team, named))]) {",
    "  for (const id of [...new Set([ref, byCreator].filter(Boolean).concat(team, named, iniIds))]) {")
save(rm, "reminders-v12.json", "Jessie — Reminders — v12 (initials on hand-made)")

# ---------------------------------------------------------------- main v301
mn = W("project-jessie-v300.json")
MAINI = ("// v301 (PENDING 161): my initials, when they are mine alone - a booking made by hand with them at the end of its title is mine too\n"
         "const _myIni = (function () { try { const g = $('Get Booker').first().json || {}; const f = g.fields || g;\n"
         "  return _p161Mine($('All Bookers').all().map(i => (i.json && i.json.fields) || {}), f); } catch (e) { return ''; } })();\n"
         "const _byIni = (e, ref, team) => !ref && !team.length && !!_myIni && _p161Inits(e && e.summary).indexOf(_myIni) !== -1;\n")
for nd in ["Mine Reply", "Change Reply"]:
    pre(mn, nd, H + SID + MYINI)
rep(mn, "Mine Reply", "const res = $input.first().json || {};", MAINI + "const res = $input.first().json || {};")
rep(mn, "Mine Reply", "    if (ref !== mc.user && team.indexOf(mc.user) === -1 && !_byMe(e)) continue;   // v293: or made by hand by them",
    "    if (ref !== mc.user && team.indexOf(mc.user) === -1 && !_byMe(e) && !_byIni(e, ref, team)) continue;   // v293: or made by hand by them; v301: or their initials on it")
rep(mn, "Change Reply", "const res = $input.first().json || {};", MAINI + "const res = $input.first().json || {};")
rep(mn, "Change Reply", "  if (ref === co.user || team.indexOf(co.user) !== -1 || _byMe(e)) list.push(evBooking(e));   // v293: or made by hand by them",
    "  if (ref === co.user || team.indexOf(co.user) !== -1 || _byMe(e) || _byIni(e, ref, team)) list.push(evBooking(e));   // v293: or made by hand by them; v301: or their initials on it")
save(mn, "project-jessie-v301.json", "Project Jessie — v301 (initials on hand-made)")
