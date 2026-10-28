#!/usr/bin/env python3
"""Builds the 28 Oct round (PENDING 135, 124, 136), each from its live download in workflows/imported/:

- workflows/book-session-v124.json - Jessie — Book Session — v124 (new client = client work)
- workflows/move-booking-v41.json - Jessie — Move Booking — v41 (new client on Change)
- workflows/room-availability-v24.json - Jessie — Room Availability — v24 (who booked it)
- workflows/slack-interactions-v51.json - Jessie — Slack Interactions — v51 (Atmos department)
- workflows/project-jessie-v285.json - Project Jessie — v285 (session type list)

PENDING 135 (decided 28 Oct, Howard: "if it's a new client, it's client work"): a client named on a booking with no Client Type
in Airtable (a new client) is client work - Entertainment for a Localization booking, else the booker's department's client
type (Advertising when that department has none). The booker's department decides only when no client is named. Kristine
(Business Development) booked Band Recording for Sony Music (not in Airtable) and got Type: Internal. Book Session's
__decideType; and on Change, a new client kept on an Internal booking makes it client work (Slack Interactions To Move sends
ClientWork, Move Booking's Resolve Booking rewrites Type: in place).

PENDING 124: a booking with no `ref:` (made or edited by hand in Google Calendar) could not be asked for. `ref:` stays the
first source; when it is missing, the "Booked by:" name is looked up in Bookers (the exact Name, or one "Goes by" alias - one
person only, else nobody). Book Session's Decide Preempt (the person in the way, an M booth's holder) and the form's "Booked –
ask to use" list (Room Availability now hands on each booking's Booked by name; Slack Interactions resolves it).

PENDING 136 (Howard, 28 Oct: Localization Atmos Mixing renamed Atmos Mixing in Airtable, for every department): the form's
step 1 never marked a booking as Atmos - Read Step 1 had no Atmos rule, so "Localization Atmos Mixing" got the Localization
form (a project code) and "Atmos Mixing" would get the studio form (client, arranger). Read Step 1 now says Atmos, and the
Atmos form asks the Department (Localization, Audio Post or Music - read from the type's Engineer Role Required), set to the
booker's own when it is one of them. Book Session's type order and main's Session Types list use the new name (main's list
also lacked Post Processing and Van Recording).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMP = os.path.join(ROOT, "workflows", "imported")


def load(name):
    return json.load(open(os.path.join(IMP, name)))


def sub(js, a, b, n=1):
    assert js.count(a) == n, (n, js.count(a), a[:120])
    return js.replace(a, b)


def save(wf, fname):
    out = os.path.join(ROOT, "workflows", fname)
    with open(out, "w") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")


def code(wf, name):
    return next(n for n in wf["nodes"] if n["name"] == name)["parameters"]


# ---------------------------------------------------------------- Book Session v124
bs = load("book-session-v123-imported.json")
p = code(bs, "Check Conflicts")
js = p["jsCode"]
js = sub(js, "  if (!client && ask && /arranger/i.test(__reqRole) && __reqDepts.indexOf('music') !== -1) return { ask: ['Client work', 'your own project'], arranger: true };",
         "  // v124 (PENDING 135, decided 28 Oct): a client named with no Client Type in Airtable (a new client) is client work -\n"
         "  // the booker's department decides only when there is no client (Business Development + Sony Music was Internal)\n"
         "  if (client && !rt.length) return { type: String(REQ.department || '').trim().toLowerCase() === 'localization' ? 'Entertainment' : _cw() };\n"
         "  if (!client && ask && /arranger/i.test(__reqRole) && __reqDepts.indexOf('music') !== -1) return { ask: ['Client work', 'your own project'], arranger: true };")
js = sub(js, "'audio post': ['VO Recording', 'Post Mixing', 'Post Processing', 'Celebrity Recording'],",
         "'audio post': ['VO Recording', 'Post Mixing', 'Post Processing', 'Celebrity Recording', 'Atmos Mixing'],")
js = sub(js, "'Band Recording', 'Music Mixing', 'Music Arranging', 'Music Presentation'],   // v118",
         "'Band Recording', 'Music Mixing', 'Music Arranging', 'Music Presentation', 'Atmos Mixing'],   // v124: Atmos Mixing (28 Oct, every department); v118")
js = sub(js, "'Localization Mixing', 'Localization Atmos Mixing', 'QC'] };", "'Localization Mixing', 'Atmos Mixing', 'QC'] };")
p["jsCode"] = js

p = code(bs, "Decide Preempt")
js = p["jsCode"]
PB = "function parseBookedBy(x){ const m=String(x||'').match(/Booked by:\\s*([^|\\n]+)/i); return m?m[1].trim():''; }"
js = sub(js, PB, PB + "\n"
         "  // v124 (PENDING 124): ref: first; a booking made by hand with no ref: - its \"Booked by\" name in Bookers (the exact Name or one\n"
         "  // \"Goes by\" alias, one person only), else nobody\n"
         "  function refByName(name){ const n=String(name||'').replace(/\\(.*$/,'').trim().toLowerCase(); if(!n) return null; let rows=[]; try{ rows=$('All Bookers').all().map(function(i){ return (i&&i.json&&i.json.fields)||{}; }); }catch(_){ return null; }\n"
         "    let hit=rows.filter(function(f){ return String(f.Name||'').trim().toLowerCase()===n; });\n"
         "    if(hit.length!==1) hit=rows.filter(function(f){ const m=String(f.Info||'').match(/goes by\\s+([^\\n]*)/i); return !!m && m[1].split(/,|\\bor\\b|\\band\\b/i).map(function(x){ return x.replace(/[.\\s]+$/,'').trim().toLowerCase(); }).indexOf(n)!==-1; });\n"
         "    if(hit.length!==1) return null; return String(hit[0]['Slack User ID']||'').split(/[\\s,]+/).filter(Boolean)[0]||null; }\n"
         "  function refOf(x){ return parseRef(x)||refByName(parseBookedBy(x)); }")
js = sub(js, "const r=parseRef(h.description);", "const r=refOf(h.description);")
js = sub(js, "const approver = parseRef(inc.description);", "const approver = refOf(inc.description);   // v124: or the Booked by name")
p["jsCode"] = js
bs["name"] = "Jessie — Book Session — v124 (new client = client work)"
save(bs, "book-session-v124.json")

# ---------------------------------------------------------------- Move Booking v41
mv = load("move-booking-v40-imported.json")
p = code(mv, "Resolve Booking")
js = p["jsCode"]
js = sub(js, "    __desc = segs.join(' | ');\n",
         "    // v41 (PENDING 135, decided 28 Oct): a new client kept on the Change form makes an Internal booking client work\n"
         "    if (nd.ClientWork) { const _ti = segs.findIndex(s => /^Type:/i.test(s)), _cur = _ti === -1 ? '' : segs[_ti].replace(/^Type:\\s*/i, '').trim();\n"
         "      if (!_cur || /^internal$/i.test(_cur)) { const _ty = 'Type: ' + (bookingDept === 'localization' ? 'Entertainment' : 'Advertising');\n"
         "        if (_ti !== -1) segs[_ti] = _ty; else { const _di = segs.findIndex(s => /^Dept:/i.test(s)); if (_di === -1) segs.push(_ty); else segs.splice(_di, 0, _ty); } } }\n"
         "    __desc = segs.join(' | ');\n")
p["jsCode"] = js
mv["name"] = "Jessie — Move Booking — v41 (new client on Change)"
save(mv, "move-booking-v41.json")

# ---------------------------------------------------------------- Room Availability v24
ra = load("room-availability-v23-imported.json")
p = code(ra, "Compute Availability")
js = p["jsCode"]
js = sub(js, "    team: ((d.match(/team:\\s*([^|\\n]+)/) || [])[1] || '').split(/[\\s,]+/).filter(Boolean) }; }) }));",
         "    team: ((d.match(/team:\\s*([^|\\n]+)/) || [])[1] || '').split(/[\\s,]+/).filter(Boolean),\n"
         "    bookedBy: ((d.split(/\\n|<br\\s*\\/?>/i)[0].match(/Booked by:\\s*([^|\\n(]+)/i) || [])[1] || '').trim() }; }) }));   // v24 (PENDING 124): for a booking with no ref:")
p["jsCode"] = js
ra["name"] = "Jessie — Room Availability — v24 (who booked it)"
save(ra, "room-availability-v24.json")

# ---------------------------------------------------------------- Slack Interactions v51
si = load("slack-interactions-v50-imported.json")
# Atmos is its own kind from step 1 (PENDING 136)
p = code(si, "Read Step 1")
js = p["jsCode"]
js = sub(js, ": /^(?:localization|qc)\\b/i.test(purpose) ? 'loc' : /^post processing$/i.test(purpose) ? 'post' : 'studio';",
         ": /atmos/i.test(purpose) ? 'atmos' : /^(?:localization|qc)\\b/i.test(purpose) ? 'loc' : /^post processing$/i.test(purpose) ? 'post' : 'studio';", n=2)
js = sub(js, "const kind = purpose === '__booth' ? 'booth' : (purpose === 'Meeting' || purpose === 'Event') ? 'meeting'\n  :",
         "// v51 (PENDING 136): Atmos Mixing is its own form (it was never set here - \"Localization Atmos Mixing\" got the Localization form)\n"
         "const kind = purpose === '__booth' ? 'booth' : (purpose === 'Meeting' || purpose === 'Event') ? 'meeting'\n  :")
p["jsCode"] = js
# the Atmos form asks the department
p = code(si, "Build Step 2")
js = p["jsCode"]
js = sub(js, "  const deptAsk = false;   // v29: no Department field - Read Step 2 takes it from the engineer / arranger picked",
         "  // v29: no Department field - Read Step 2 takes it from the engineer / arranger picked; v51 (Howard, 28 Oct): except Atmos Mixing,\n"
         "  // which any of its departments books (Localization, Audio Post, Music - the type's Engineer Role Required), set to the booker's own\n"
         "  const deptAsk = s.kind === 'atmos' && typeDepts.length > 1;")
p["jsCode"] = js
# a booking with no ref: can still be asked for - its Booked by name in Bookers (PENDING 124)
RBN = ("      // v51 (PENDING 124): a booking with no ref: (made by hand) - its Booked by name in Bookers (the Name or one alias), else nobody\n"
       "      d.events = [].concat(d.events || []).map(e => e.ref || !e.bookedBy ? e : Object.assign({}, e, { ref: (() => { const n = String(e.bookedBy).replace(/\\(.*$/, '').trim().toLowerCase();\n"
       "        const rows = ((data && data.bookers) || []).map(b => b.fields || {}); let hit = rows.filter(f => String(f.Name || '').trim().toLowerCase() === n);\n"
       "        if (hit.length !== 1) hit = rows.filter(f => { const m = String(f.Info || '').match(/goes by\\s+([^\\n]*)/i); return !!m && m[1].split(/,|\\bor\\b|\\band\\b/i).map(x => x.replace(/[.\\s]+$/, '').trim().toLowerCase()).indexOf(n) !== -1; });\n"
       "        return hit.length === 1 ? (String(hit[0]['Slack User ID'] || '').split(/[\\s,]+/).filter(Boolean)[0] || '') : ''; })() }));\n")
for nm in ("Build Step 2", "Note Toggle"):
    p = code(si, nm)
    p["jsCode"] = sub(p["jsCode"], "    for (const d of ra.busy_detail) {\n", "    for (const d of ra.busy_detail) {\n" + RBN)
# a new client kept on Change makes an Internal booking client work (PENDING 135)
p = code(si, "To Move")
js = p["jsCode"]
js = sub(js, "if (R.clientTyped) {\n", "let __newClient = false;   // v51 (PENDING 135): a new client kept -> Move makes an Internal booking client work\nif (R.clientTyped) {\n")
js = sub(js, "  const exact = names.find(x => x.toLowerCase() === tl);\n", "  const exact = names.find(x => x.toLowerCase() === tl);\n  __newClient = !exact;\n")
js = sub(js, "  new_details: (R.newDetails || R.roomChanged) ? JSON.stringify(Object.assign({}, R.newDetails || {},\n",
         "  new_details: (R.newDetails || R.roomChanged || __newClient) ? JSON.stringify(Object.assign({}, R.newDetails || {}, __newClient ? { ClientWork: true } : {},\n")
p["jsCode"] = js
si["name"] = "Jessie — Slack Interactions — v51 (Atmos department)"
save(si, "slack-interactions-v51.json")

# ---------------------------------------------------------------- main v285
mn = load("project-jessie-v284-imported.json")
OLD = ("one of: Band Recording, Celebrity Recording, Event, Localization Atmos Mixing, Localization Dubbing, Localization Editing, "
       "Localization Mixing, Meeting, Music Arranging, Music Mixing, Music Presentation, Music Recording, Post Mixing, QC, VO Recording.")
NEW = ("one of: Atmos Mixing, Band Recording, Celebrity Recording, Event, Localization Dubbing, Localization Editing, "
       "Localization Mixing, Meeting, Music Arranging, Music Mixing, Music Presentation, Music Recording, Post Mixing, Post Processing, QC, "
       "Van Recording, VO Recording.")
hits = 0
for n in mn["nodes"]:
    s = json.dumps(n["parameters"], ensure_ascii=False)
    if OLD in s:
        n["parameters"] = json.loads(s.replace(OLD, NEW)); hits += 1
assert hits == 1, hits
mn["name"] = "Project Jessie — v285 (session type list)"
save(mn, "project-jessie-v285.json")
