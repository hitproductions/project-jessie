#!/usr/bin/env python3
"""Builds the second 20 Nov round (Howard):

A. An event blocks a room only when that room is booked on it (PENDING 159). Its room resource must be a guest that has not
   declined. A room named only in the location text or at the start of the title, a resource that declined, or no room at all
   no longer blocks anything. Each room's own calendar (free/busy, since Book Session v125 / Room Availability v25) still shows
   every room that really is held, including rooms booked from someone's own calendar or through Envoy.
   Found on 20 Nov: "New Event" (24 Nov, no room), "Studio F session" (20 Nov, Studio F declined), "test booking" (21 Nov, M2
   declined), "Hit Productions Christmas Party 2026" (17 Dec, location "Hit Productions, KDC Plaza").
   - Book Session v132 (Check Conflicts): roomsOf, and the free/busy cover check, read only accepted / pending room resources; an
     event with no room is skipped (no UNVERIFIABLE refusal any more).
   - Room Availability v27 (Compute Availability): the same, in all three places it reads rooms; no "no identifiable room ... treat
     this as incomplete" note.
   - Move Booking v46 (Check New Window): clashes and the free times it offers read only room resources that have not declined;
     an event with no room no longer blocks the times offered.
B. Coordinators find their department's bookings by typing (PENDING 115) - main v296 (Change Reply): a typed change that names
   something (a title word, a date or a room) also looks through other people's bookings in the requester's department when they
   are a Dept Head or Client Booking coordinator (HAIST Dev: every department). My bookings is unchanged.
C. Room Check v4 (PENDING 147): when Slack refuses the "the room turned this booking down" DM, an alert goes to the ops channel
   (the same one Slack Interactions' Ops Alert uses) with the booking, whose it was and Slack's error.
Built on the live builds: book-session-v131, room-availability-v26, move-booking-v45, project-jessie-v295, room-check-v3.
"""
import json
import os
import re
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load(f):
    return json.load(open(os.path.join(ROOT, "workflows", f)))


def save(wf, f, name):
    wf["name"] = name
    with open(os.path.join(ROOT, "workflows", f), "w") as fh:
        json.dump(wf, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("wrote workflows/" + f, len(wf["nodes"]), "nodes")


def node(wf, n):
    return [x for x in wf["nodes"] if x["name"] == n][0]


def rep(wf, n, old, new, count=1):
    p = node(wf, n)["parameters"]
    k = p["jsCode"].count(old)
    assert k == count, (wf["name"], n, old[:80], k)
    p["jsCode"] = p["jsCode"].replace(old, new)


HELD = "(a => a && String(a.responseStatus || '') !== 'declined')"   # a guest that has not declined

# ---- A1. Book Session v132
bs = load("book-session-v131.json")
rep(bs, "Check Conflicts",
    "  const emails = (ev.attendees || []).map(a => String(a.email || '').toLowerCase());\n"
    "  const loc = String(ev.location || '').toLowerCase();\n"
    "  const firstSeg = String(ev.summary || '').split(' - ')[0].trim().toLowerCase();\n"
    "  for (const k of keys) {\n"
    "    const lk = k.toLowerCase();\n"
    "    if (emails.indexOf(ROOMS[k].toLowerCase()) !== -1) { found.push(k); continue; }\n"
    "    if (loc && loc.indexOf(lk) !== -1) { found.push(k); continue; }\n"
    "    if (firstSeg && firstSeg === lk) { found.push(k); }\n"
    "  }\n",
    "  // v132 (PENDING 159, 20 Nov): a room is held only by its resource on the event, not declined - never by the location text or\n"
    "  // the title alone (each room's own calendar, read below as free/busy, shows every room really held)\n"
    "  const emails = (ev.attendees || []).filter" + HELD + ".map(a => String(a.email || '').toLowerCase());\n"
    "  for (const k of keys) {\n"
    "    if (emails.indexOf(ROOMS[k].toLowerCase()) !== -1) found.push(k);\n"
    "  }\n")
rep(bs, "Check Conflicts",
    "(ev.attendees || []).some(a => String(a.email || '').toLowerCase() === _em) || String(ev.location || '').toLowerCase().indexOf(_lk) !== -1\n"
    "      || String(ev.summary || '').split(' - ')[0].trim().toLowerCase() === _lk)",
    "(ev.attendees || []).some(a => String(a.responseStatus || '') !== 'declined' && String(a.email || '').toLowerCase() === _em) /* v132: its resource only */)")
rep(bs, "Check Conflicts",
    "  if (!evRooms.length) {\n    unverifiable.push(",
    "  if (!evRooms.length) continue;   // v132 (PENDING 159): an event with no room booked on it holds no room\n  if (false) {\n    unverifiable.push(")
save(bs, "book-session-v132.json", "Jessie — Book Session — v132 (rooms booked only)")

# ---- A2. Room Availability v27
ra = load("room-availability-v26.json")
c = node(ra, "Compute Availability")["parameters"]["jsCode"]
n0 = c.count("(ev.attendees || []).map(a => String(a.email || '').toLowerCase())")
assert n0 == 3, n0
c = c.replace("(ev.attendees || []).map(a => String(a.email || '').toLowerCase())",
              "(ev.attendees || []).filter" + HELD + ".map(a => String(a.email || '').toLowerCase())")
OLDM = "    if (emails.indexOf(ROOMS[k].toLowerCase()) !== -1 || (loc && loc.indexOf(lk) !== -1) || firstSeg === lk) {"
assert c.count(OLDM) == 1
c = c.replace(OLDM, "    if (emails.indexOf(ROOMS[k].toLowerCase()) !== -1) {   // v27 (PENDING 159): its resource only - not the location or title")
OLDG = "      if (emails.indexOf(ROOMS[k].toLowerCase()) !== -1 || (loc && loc.indexOf(lk) !== -1) || seg === lk) (iv[k] = iv[k] || []).push([s0, e0]); }"
assert c.count(OLDG) == 1
c = c.replace(OLDG, "      if (emails.indexOf(ROOMS[k].toLowerCase()) !== -1) (iv[k] = iv[k] || []).push([s0, e0]); }   // v27: its resource only")
OLDU = "  if (!matched) unidentified.push(ev.summary || '(no title)');"
assert c.count(OLDU) == 1
c = c.replace(OLDU, "  // v27: an event with no room booked on it holds no room - not counted, no \"incomplete\" note")
OLDR = "      return keys.filter(k => emails.indexOf(ROOMS[k].toLowerCase()) !== -1 || (loc && loc.indexOf(k.toLowerCase()) !== -1) || seg === k.toLowerCase());"
assert c.count(OLDR) == 1
c = c.replace(OLDR, "      return keys.filter(k => emails.indexOf(ROOMS[k].toLowerCase()) !== -1);   // v27: its resource only")
OLDE = ("  return (ev.attendees || []).some(a => String(a.email || '').toLowerCase() === em) || String(ev.location || '').toLowerCase().indexOf(lk) !== -1\n"
        "    || String(ev.summary || '').split(' - ')[0].trim().toLowerCase() === lk; };")
assert c.count(OLDE) == 1, c.count(OLDE)
c = c.replace(OLDE, "  return (ev.attendees || []).some(a => String(a.responseStatus || '') !== 'declined' && String(a.email || '').toLowerCase() === em); };   // v27: its resource only")
node(ra, "Compute Availability")["parameters"]["jsCode"] = c
save(ra, "room-availability-v27.json", "Jessie — Room Availability — v27 (rooms booked only)")

# ---- A3. Move Booking v46
mv = load("move-booking-v45.json")
c = node(mv, "Check New Window")["parameters"]["jsCode"]
OLD1 = ("  const emails = (e.attendees || []).map(a => String(a.email || '').toLowerCase());\n"
        "  const sameRoom = mine.some(m => emails.indexOf(m) !== -1)\n"
        "    || (loc && String(e.location || '').toLowerCase() === loc);")
assert c.count(OLD1) == 1
c = c.replace(OLD1, "  const emails = (e.attendees || []).filter" + HELD + ".map(a => String(a.email || '').toLowerCase());\n"
              "  const sameRoom = mine.some(m => /resource\\.calendar\\.google\\.com$/.test(m) && emails.indexOf(m) !== -1);   // v46 (PENDING 159): its room resource only")
OLD2 = ("      const emails = (e.attendees || []).map(a => String(a.email || '').toLowerCase());\n"
        "      const same = mine.some(m => emails.indexOf(m) !== -1) || (loc && String(e.location || '').toLowerCase() === loc);\n"
        "      const noRoom = !emails.some(x => /resource\\.calendar\\.google\\.com$/.test(x)) && !String(e.location || '').trim();\n")
assert c.count(OLD2) == 1, c.count(OLD2)
c = c.replace(OLD2, "      const emails = (e.attendees || []).filter" + HELD + ".map(a => String(a.email || '').toLowerCase());\n"
              "      const same = mine.some(m => /resource\\.calendar\\.google\\.com$/.test(m) && emails.indexOf(m) !== -1);   // v46: its room resource only\n"
              "      const noRoom = false;   // v46: an event with no room booked on it no longer blocks the times offered\n")
node(mv, "Check New Window")["parameters"]["jsCode"] = c
save(mv, "move-booking-v46.json", "Jessie — Move Booking — v46 (rooms booked only)")

# ---- A4. every other copy in Book Session / Room Availability (alternative rooms, the room-request check, the free/busy cover)
def room_rule_everywhere(wf, n):
    p = node(wf, n)["parameters"]; c = p["jsCode"]
    c = c.replace("(ev.attendees || []).map(a => String(a.email || '').toLowerCase())", "(ev.attendees || []).filter" + HELD + ".map(a => String(a.email || '').toLowerCase())")
    c = re.sub(r"\s*\|\|\s*\(loc && loc\.indexOf\(lk\) !== -1\)\s*\|\|\s*firstSeg === lk", "", c)
    c = re.sub(r"\s*\|\|\s*\(_loc && _loc\.indexOf\(k\.toLowerCase\(\)\) !== -1\)\s*\|\|\s*_fs === k\.toLowerCase\(\)", "", c)
    c = c.replace("(ev.attendees || []).some(a => String(a.email || '').toLowerCase() === _em) || String(ev.location || '').toLowerCase().indexOf(_lk) !== -1\n"
                  "      || String(ev.summary || '').split(' - ')[0].trim().toLowerCase() === _lk)",
                  "(ev.attendees || []).some(a => String(a.responseStatus || '') !== 'declined' && String(a.email || '').toLowerCase() === _em) /* v27 / v132: its resource only */)")
    left = re.findall(r"(?:loc|_loc)\s*&&\s*(?:loc|_loc)\.indexOf\(|location \|\| ''\)\.toLowerCase\(\)\.indexOf\(|(?:firstSeg|seg|_fs) === (?:lk|_lk|k\.toLowerCase\(\))|split\(' - '\)\[0\]\.trim\(\)\.toLowerCase\(\) === _?lk", c)
    assert not left, (wf["name"], n, left)
    p["jsCode"] = c

for f, n, name in [("book-session-v132.json", "Check Conflicts", "Jessie — Book Session — v132 (rooms booked only)"),
                   ("room-availability-v27.json", "Compute Availability", "Jessie — Room Availability — v27 (rooms booked only)")]:
    wf = load(f); room_rule_everywhere(wf, n); save(wf, f, name)

# ---- B. main v296 (PENDING 115)
mn = load("project-jessie-v295.json")
rep(mn, "Change Reply",
    "  if (ref === co.user || team.indexOf(co.user) !== -1 || _byMe(e)) list.push(evBooking(e));   // v293: or made by hand by them\n",
    "  if (ref === co.user || team.indexOf(co.user) !== -1 || _byMe(e)) list.push(evBooking(e));   // v293: or made by hand by them\n"
    "  // v296 (PENDING 115): a coordinator's typed change that names something also finds their department's bookings\n"
    "  else if (co.kind === 'change' && _specific && (_auth.haist || (_auth.coord && _auth.depts.indexOf(((desc.match(/Dept:\\s*([^|\\n]+)/) || [])[1] || '').trim().toLowerCase()) !== -1))) list.push(evBooking(e));\n")
rep(mn, "Change Reply",
    "const res = $input.first().json || {};\nconst md = t => ({ type: 'mrkdwn', text: t });\nlet list = [];\n",
    "const res = $input.first().json || {};\nconst md = t => ({ type: 'mrkdwn', text: t });\nlet list = [];\n"
    "// v296 (PENDING 115): who may change other people's bookings - a Dept Head / Client Booking coordinator in their own department, a\n"
    "// HAIST Dev in any (the same rule Move Booking applies); only when the typed change names a title word, a date or a room\n"
    "const _auth = (function () { try { const g = $('Get Booker').first().json || {}; const f = g.fields || g;\n"
    "  const a = [].concat(f.Authority || []).map(x => String((x && x.name) || x).trim().toLowerCase());\n"
    "  return { haist: a.indexOf('haist dev') !== -1, coord: a.indexOf('dept head') !== -1 || a.indexOf('client booking') !== -1,\n"
    "    depts: [].concat(f.Department || []).map(x => String((x && x.name) || x).trim().toLowerCase()) }; } catch (e) { return { haist: false, coord: false, depts: [] }; } })();\n"
    "const _specific = !!(co.words.length || co.fDates.length || co.fRooms.length);\n")
save(mn, "project-jessie-v296.json", "Project Jessie — v296 (coordinators find by typing)")

# ---- C. Room Check v4 (PENDING 147)
rc = load("room-check-v3.json")
si = load("slack-interactions-v82.json")
ops = re.search(r"return \[\{ json: \{ channel: '([A-Z0-9]+)'", node(si, "Ops Alert")["parameters"]["jsCode"]).group(1)
sd = node(rc, "Send DM")
pos = sd["position"]
rc["nodes"].append({"parameters": {"jsCode":
    "// DM Failed? (v4, PENDING 147): Slack refused the \"the room turned this booking down\" DM (29 Oct: the booker never heard, and\n"
    "// Send DM's \"continue on error\" hid it) -> an alert to the ops channel, as Slack Interactions' Ops Alert does. Sent -> no item.\n"
    "const r = ($input.first() || {}).json || {};\n"
    "if (r.ok === true) return [];\n"
    "let d = {}; try { d = $('Build DM').first().json || {}; } catch (e) {}\n"
    "let t = {}; try { t = $('When Executed by Another Workflow').first().json || {}; } catch (e) {}\n"
    "const err = r.error ? (typeof r.error === 'string' ? r.error : JSON.stringify(r.error)) : JSON.stringify(r).slice(0, 300);\n"
    "const at = new Date(Date.now() + 8 * 3600000).toISOString().slice(0, 16).replace('T', ' ');\n"
    "const text = '⚠️ Jessie - Room Check: the room turned down a booking, but the DM to ' + (d.channel ? '<@' + d.channel + '>' : '(no booker id)')\n"
    "  + ' could not be sent (' + at + ' PHT): ' + String(err).slice(0, 600) + '\\n' + String(d.text || t.title || t.summary || '').slice(0, 600)\n"
    "  + (d.removed ? '\\nThe booking was removed from the calendar.' : '');\n"
    "return [{ json: { channel: '" + ops + "', text, blocks: [{ type: 'section', text: { type: 'mrkdwn', text: text.slice(0, 2900) } }] } }];"},
    "id": str(uuid.uuid4()), "name": "DM Failed?", "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [pos[0] + 220, pos[1] + 200]})
rc["nodes"].append({"parameters": {"method": "POST", "url": "https://slack.com/api/chat.postMessage", "authentication": "predefinedCredentialType",
    "nodeCredentialType": "slackApi", "sendBody": True, "specifyBody": "json",
    "jsonBody": "={{ JSON.stringify({ channel: $json.channel, text: $json.text, blocks: $json.blocks }) }}", "options": {}},
    "id": str(uuid.uuid4()), "name": "Send Alert", "type": sd["type"], "typeVersion": sd["typeVersion"], "position": [pos[0] + 440, pos[1] + 200],
    "credentials": sd.get("credentials"), "onError": "continueRegularOutput"})
conn = rc["connections"]["Send DM"]["main"][0]
assert [x["node"] for x in conn] == ["Declined Row"], conn
conn.append({"node": "DM Failed?", "type": "main", "index": 0})
rc["connections"]["DM Failed?"] = {"main": [[{"node": "Send Alert", "type": "main", "index": 0}]]}
save(rc, "room-check-v4.json", "Jessie — Room Check — v4 (DM failure alert)")
