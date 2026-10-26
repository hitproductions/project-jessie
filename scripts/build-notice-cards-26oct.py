#!/usr/bin/env python3
"""Builds the notice cards, 26 Oct: Cancel Booking v30, Move Booking v36, Jessie — Request Messages v4.

Howard (26 Oct): "let's make the notification messages clearer and simpler" - a summary like the other cards.
  1. Cancel / Move notices ("Heads up - "QA-GIVE UP / WD" on 2027-10-28, a session you are on, was cancelled by Camy
     Caridad."): "A session you are on was cancelled by Camy Caridad:" (or "Your booking was cancelled by …:"), then the card -
     *title*, Date, Time, Room - and buttons (cancelled: Book a room / My bookings; moved: My bookings, the card showing the new
     date / time / room). Sent with blocks (chat.postMessage) instead of plain text. While testing, the "[DEV] would notify X
     (id):" prefix becomes the small "Test: this is for X." line the other messages use.
  2. A request, ended, to the person asked: "Howard Luistro asks for the following booking:" + Date / Time / Room, then how it
     ended (as before), and My bookings.
  3. A priority request, open: "Howard Luistro is requesting a new booking to take over your existing one. Their Celebrity
     Recording session takes priority over your VO Recording session in that room." + "Their requested booking:" (card) +
     "Your existing booking:" (card) + Move my booking / Give it up / Keep my booking; the answer-by time under the buttons.
     A shared M booth request and the requester's own message get the same card layout.
Built on the live downloads (workflows/imported/*-imported.json).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load(f):
    return json.load(open(os.path.join(ROOT, "workflows", "imported", f)))


def save(wf, out, name):
    wf["name"] = name
    with open(os.path.join(ROOT, "workflows", out), "w") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote workflows/" + out)


def sub(wf, node, a, b, n=1):
    nd = [x for x in wf["nodes"] if x["name"] == node][0]
    js = nd["parameters"]["jsCode"]
    assert js.count(a) == n, (node, js.count(a), a[:80])
    nd["parameters"]["jsCode"] = js.replace(a, b)


# ---------------- Cancel / Move: the notice as a card
CARD_JS = r"""
// v30 Cancel / v36 Move (26 Oct, Howard: "clearer and simpler"): who did it, then the booking as a card - *title*, Date, Time,
// Room - and buttons, like the other cards. While testing a redirected notice says who it is for on a small line at the end.
const _DL = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'], _ML = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const _mnl = iso => new Date((/^\d{4}-\d{2}-\d{2}$/.test(String(iso || '')) ? Date.parse(iso + 'T00:00:00+08:00') : Date.parse(iso)) + 8 * 3600000);
const _t12 = iso => { const x = _mnl(iso); if (isNaN(x)) return ''; let h = x.getUTCHours(); const m = x.getUTCMinutes(), ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(m).padStart(2, '0') + ' ' + ap; };
const _allDay = (s, e) => /^\d{4}-\d{2}-\d{2}$/.test(String(s || '')) || (_t12(s) === '12:00 AM' && _t12(e) === '12:00 AM');
const _day = iso => { const x = _mnl(iso); return isNaN(x) ? String(dateStr || '') : _DL[x.getUTCDay()] + ', ' + _ML[x.getUTCMonth()] + ' ' + x.getUTCDate() + ', ' + x.getUTCFullYear(); };
const _room = r => String(r || '').split(',').map(x => x.replace(/^KDC Plaza-Top Level-/i, '').replace(/\s*\(\d+\)\s*$/, '').trim()).filter(Boolean).join(' + ');
const card = lead => lead + '\n\n*' + title + '*\n*Date:* ' + _day(S || dateStr) + (S && E ? '\n*Time:* ' + (_allDay(S, E) ? 'All day' : _t12(S) + ' – ' + _t12(E)) : '') + (ROOM ? '\n*Room:* ' + ROOM : '');
const _btn = (aid, text) => ({ type: 'button', action_id: aid, value: 'menu', text: { type: 'plain_text', text } });
const BUTTONS = { type: 'actions', elements: VERB === 'cancelled' ? [_btn('open_book', 'Book a room'), _btn('my_bookings', 'My bookings')] : [_btn('my_bookings', 'My bookings')] };
"""
PUSH_OLD = """  const to = route(id, true); const redirected = to !== id;
  out.push({ to, text: (redirected ? ('[DEV] would notify ' + name + ' (' + id + '):\\n') : '') + body });
};"""
PUSH_NEW = """  const to = route(id, true); const redirected = to !== id;
  const blocks = [{ type: 'section', text: { type: 'mrkdwn', text: card(body).slice(0, 2900) } }, BUTTONS]
    .concat(redirected ? [{ type: 'context', elements: [{ type: 'mrkdwn', text: '_Test: this is for ' + name + ' (' + id + ')._' }] }] : []);   // v30 / v36: was "[DEV] would notify …"
  out.push({ to, text: body + ' ' + title, blocks });
};"""
BOOKER_OLD = "push(bookerId, co.bookerName || 'the booker', 'Heads up - your booking \"' + title + '\" on ' + dateStr + ' was ' + VERB + roomNote + ' by ' + actor + '.');"
BOOKER_NEW = "push(bookerId, co.bookerName || 'the booker', 'Your booking was ' + VERB + ' by ' + actor + ':');"
TEAM_OLD = "for (const id of team) push(id, names[id] || 'a team member', 'Heads up - \"' + title + '\" on ' + dateStr + ', a session you are on, was ' + VERB + roomNote + ' by ' + actor + '.');"
TEAM_NEW = "for (const id of team) push(id, names[id] || 'a team member', 'A session you are on was ' + VERB + ' by ' + actor + ':');"


def notice(src, out, name, data_line):
    wf = load(src)
    sub(wf, "Build Recipients", "const out = [], told = new Set();", data_line + CARD_JS + "const out = [], told = new Set();")
    sub(wf, "Build Recipients", PUSH_OLD, PUSH_NEW)
    sub(wf, "Build Recipients", BOOKER_OLD, BOOKER_NEW)
    sub(wf, "Build Recipients", TEAM_OLD, TEAM_NEW)
    # send with blocks: the Slack node sent text only
    sd = [x for x in wf["nodes"] if x["name"] == "Send DMs"][0]
    sd["type"] = "n8n-nodes-base.httpRequest"
    sd["typeVersion"] = 4.2
    sd["parameters"] = {"method": "POST", "url": "https://slack.com/api/chat.postMessage", "authentication": "predefinedCredentialType",
                        "nodeCredentialType": "slackApi", "sendBody": True, "specifyBody": "json",
                        "jsonBody": "={{ JSON.stringify({ channel: $json.to, text: $json.text, blocks: $json.blocks }) }}", "options": {}}
    assert sd.get("credentials", {}).get("slackApi"), sd.get("credentials")
    return wf


# Cancel: the booking's time and room from the event it found
cw = notice("cancel-booking-v29-imported.json", None, None,
            "const S = String(co.start || ''), E = String(co.end || ''), ROOM = _roomOf(co.room);   // v30: the cancelled booking\n")
sub(cw, "Check Ownership", "  start: (ev.start && (ev.start.dateTime || ev.start.date)) || '',\n  notify,",
    "  start: (ev.start && (ev.start.dateTime || ev.start.date)) || '',\n  end: (ev.end && (ev.end.dateTime || ev.end.date)) || '', room: cxRoom(ev) || '',   // v30: for the notice card\n  notify,")
sub(cw, "Build Recipients", "const S = String(co.start || ''), E = String(co.end || ''), ROOM = _roomOf(co.room);", "const S = String(co.start || ''), E = String(co.end || '');")
sub(cw, "Build Recipients", "const out = [], told = new Set();", "const ROOM = _room(co.room);\nconst out = [], told = new Set();")
save(cw, "cancel-booking-v30.json", "Jessie — Cancel Booking — v30 (notice cards)")

# Move: the new date / time / room
mw = notice("move-booking-v35-imported.json", None, None,
            "const S = String(co.new_start || ''), E = String(co.new_end || '');   // v36: where it is now\n")
sub(mw, "Build Recipients", "const out = [], told = new Set();", "const ROOM = _room(co.location || trig.new_rooms);\nconst out = [], told = new Set();")
save(mw, "move-booking-v36.json", "Jessie — Move Booking — v36 (notice cards)")

# ---------------- Request Messages: the cards
rw = load("request-messages-v3-imported.json")
CARD = ("// v4 (26 Oct, Howard: \"clearer and simpler\"): a booking as a card - *title*, Date, Time, Room - like the other cards\n"
        "const bookCard = (t, dLong, times, rm) => (t ? '*' + t + '*\\n' : '') + '*Date:* ' + dLong + '\\n*Time:* ' + times + '\\n*Room:* ' + rm;\n"
        "const reqCard = bookCard(title, _dayLong(day), _times(rs, re), room);\n"
        "const incCard = bookCard(incTitle, _dayLong(inc.d || day), inc.d ? (inc.s && !(inc.s === '00:00' && inc.e === '00:00') ? _t12(inc.s) + ' – ' + _t12(inc.e) : 'All day') : _times(rs, re), inc.r || room);\n")
sub(rw, "Render", "const reqHead = '*' + title + '*\\n' + when + ' · ' + room;",
    "const reqHead = '*' + title + '*\\n' + when + ' · ' + room;\n" + CARD)
# the requester's own message: the card
sub(rw, "Render", "  const lines = ['⏳ *Requested – ' + room + '*', reqHead,",
    "  const lines = ['⏳ *Requested – ' + room + '*', '', reqCard, '',   // v4: the card")
# a shared booth, open
sub(rw, "Render", "  if (isMB) return [sec('🙋 *' + R.name + ' asks to use ' + room + '* · ' + whenShort + ' – during your standing hold.\\n'\n      + 'If you don’t need it that day, let them use it. *No answer by ' + dl + ': it’s booked for them.*'),",
    "  if (isMB) return [sec('🙋 ' + R.name + ' asks to use ' + room + ' during your standing hold:\\n\\n' + bookCard(title, _dayLong(day), _times(rs, re), room)\n"
    "      + '\\n\\nIf you don’t need it that day, let them use it. *No answer by ' + dl + ': it’s booked for them.*'),   // v4: the card")
# a priority request, open (Howard's wording)
sub(rw, "Render", """  const lines = ['🙋 *' + R.name + ' asks for ' + room + '* · ' + whenShort,
    'For *' + (type || 'a session') + '*' + (title ? ' (' + title + ')' : '') + ', which takes priority' + (inc.st ? ' over ' + inc.st : '') + '.',
    '', 'Your booking: *' + incTitle + '*' + (incWhen ? ' · ' + incWhen : ''),
    'Move it to a time or room that doesn’t clash, give it up, or keep it. Please answer by *' + dl + '* – no answer keeps your booking.'];""",
    """  // v4 (Howard, 26 Oct): what they want, then both bookings as cards; the answer-by time under the buttons
  const lines = ['🙋 ' + R.name + ' is requesting a new booking to take over your existing one. Their ' + (type || 'session') + (type ? ' session' : '') + ' takes priority over your '
      + (inc.st ? inc.st + ' session' : 'booking') + ' in that room.',
    '', '*Their requested booking:*', reqCard, '', '*Your existing booking:*', incCard];""")
sub(rw, "Render", """    btn('cr_keep', 'Keep my booking', { id: rid, w: p.r }, { confirm: confirm('Keep your booking?', R.name + ' is told you need ' + room + ' then.', 'Keep it', 'Not yet') })] }];
}""", """    btn('cr_keep', 'Keep my booking', { id: rid, w: p.r }, { confirm: confirm('Keep your booking?', R.name + ' is told you need ' + room + ' then.', 'Keep it', 'Not yet') })] },
    ctx('Move it to a time or room that doesn’t clash, give it up, or keep it. Please answer by *' + dl + '* – no answer keeps your booking.')];   // v4
}""")
# a request, ended, to the person asked (Howard's wording)
sub(rw, "Render", "  const head = (isMB ? '*' + R.name + ' asked to use ' + room + '*' : '*' + R.name + ' asked for ' + room + '*') + ' · ' + whenShort;",
    "  const head = (isMB ? R.name + ' asks to use ' + room + ' during your standing hold:' : R.name + ' asks for the following booking:')   // v4 (Howard, 26 Oct)\n"
    "    + '\\n\\n' + bookCard('', _dayLong(day), _times(rs, re), room);")
sub(rw, "Render", "  return [sec(head), ctx(line)];",
    "  return [sec(head), ctx(line), { type: 'actions', elements: [btn('my_bookings', 'My bookings', 'menu')] }];   // v4: My bookings")
# the requester's ended message (not DONE): the card too
sub(rw, "Render", "  return [sec(lead + '\\n' + reqHead), { type: 'actions', elements: [btn('cr_pick', 'Pick another room', pick), btn('my_bookings', 'My bookings', 'menu')] }];",
    "  return [sec(lead + '\\n\\n' + reqCard), { type: 'actions', elements: [btn('cr_pick', 'Pick another room', pick), btn('my_bookings', 'My bookings', 'menu')] }];   // v4: the card")
save(rw, "request-messages-v4.json", "Jessie — Request Messages — v4 (cards)")
