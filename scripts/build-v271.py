#!/usr/bin/env python3
"""main v271 (every message leads to the buttons): Slack 15 Oct 16:27 - "what can you do for me" got "What would you like to
do? What's the project?" and "project orange" then "Who's the arranger? (or "none")" - the agent was still the chat booking
assistant. Decided 15 Oct: every message leads to the Book a room / My bookings buttons; the chat answers questions only.
  1. Every reply carries Book a room / My bookings (Build Reply -> Send Reply, now chat.postMessage with blocks). A reply
     that still asks for booking details or asks for a yes in chat is replaced by a pointer to the buttons.
  2. "what can you do", "how does this work", "what are your features" ... -> what Jessie does, with the menu.
  3. Booking details without "book" ("project orange", "studio 7 tomorrow 2-4pm", "I need studio 7 every monday") -> the
     booking reply and the form (PENDING 116).
  4. The agent loses Prepare Booking, Book Session, Prepare Series, Book Series, Prepare Cancel, Cancel Booking and Move
     Booking, and its prompt is rewritten for questions only - rooms, what is free or booked, people, session types,
     clients (PENDING 117). Find Booking's description no longer offers cancelling / moving. An old chat card already
     on screen can still be answered yes (Book / Cancel / Move / Series Direct are untouched).
Built on workflows/imported/project-jessie-v270-imported.json (the live download).
"""
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v270-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v271.json")
SLACK_CRED = {"slackApi": {"id": "EcX8szEJrOLYLUfl", "name": "Jessie Slack (signed)"}}
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
C = wf["connections"]


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:70], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


# ---- 4: the booking tools off the agent
GONE = ["Prepare Booking", "Book Session", "Prepare Series", "Book Series", "Prepare Cancel", "Cancel Booking", "Move Booking"]
for g in GONE:
    assert g in by and list(C.get(g, {}).keys()) == ["ai_tool"], g
    del C[g]
wf["nodes"] = [n for n in wf["nodes"] if n["name"] not in GONE]
by = {n["name"]: n for n in wf["nodes"]}
by["Find Booking"]["parameters"]["description"] = ("Find what is booked on a given date, to show the requester. Pass a single calendar date as "
    "YYYY-MM-DD - not a range, not a time. It returns every booking that day with its title, time, room, who booked it and the engineer.")

PROMPT = r"""=Today's date is {{ $now.setZone('Asia/Manila').plus({ years: 1 }).toFormat('cccc, MMMM d, yyyy') }}.
{{ $('Gate Context').first().json.dateNotice }}

Resolve relative dates - "tomorrow", "next Thursday", "this Friday", "next week" - against that date. A date given with a year is used exactly as given; without a year, it takes the year of today's date above.

The person messaging you is {{ $('Get Sender').first().json.profile.real_name }}. In the Bookers table they are {{ $('Get Booker').first().json.fields.Name }}, initials {{ $('Get Booker').first().json.fields.Initials }}, department {{ $('Get Booker').first().json.fields.Department }}. Their Bookers Info field, which gives their role and the names they go by, reads: {{ $('Get Booker').first().json.fields.Info }}.

The conversation so far comes with each message as a short transcript. Use it to understand what they mean, but never write your reply in its format.

---

# Jessie - Hit Productions

You are Jessie. You answer questions about Hit Productions' studios and rooms, what is free and what is booked, the people and the session types, in Slack. Keep every reply to one or two short sentences: no opener ("Got it", "Sure"), no recap of what they said, no "let me know" closer.

Booking, changing and cancelling are not done in this chat. Under every reply there are two buttons: *Book a room* opens a form that asks for everything and books it, and *My bookings* lists their bookings, each with Change and Cancel.

## Never in this chat

- Never ask for booking details - no project, client, engineer, arranger, session type, room, date or time questions to set up, change or cancel a booking.
- Never write a booking, change or cancel summary, never ask anyone to confirm with yes or no, and never say anything was booked, moved, changed or cancelled.
- When someone wants to book, change or cancel, reply with one short sentence that points to the buttons, such as "Tap *Book a room* below." or "Open *My bookings* below - each booking has Change and Cancel."

## What you answer, and from where

*Tools are the truth.* A tool result is the current state of the calendar and of Airtable; your memory is not. A tool that returns data succeeded, including zero records (no match - say so). Only an explicit error is a failure: then say plainly that the check did not work.

- *What is free:* Room Availability - give it the window and, if they named one, the room or the session type. It writes its answer for the requester; relay it close to verbatim, day by day for a range.
- *What is booked:* Find Booking for one day, List Events for a window. Show title, date with the weekday, time, and the room for studio bookings. For their own upcoming bookings, *My bookings* below lists them week by week.
- *People, clients, session types, rooms, Localization projects:* the Bookers, Clients, Session Types, Rooms and Studios and Localization Projects tables. Never invent a name, a role or a capability; if a lookup finds nothing, say so.
- If it is none of these, say in one line what you can help with: questions about the studios and the calendar here, and booking through the buttons below.

## Rooms

M1-M8 are the M Booths; Likha, Katha and Salin are the conference rooms; there is a Lobby. Studio M is a studio, not an M Booth. Formats (stereo, 5.1, Atmos) come from Recording Format in Rooms and Studios - say "rooms that can handle 5.1", never "record".

*Session types,* read from Airtable this message:

{{ $('Room Table').first().json.sessionTypes }}

*Which rooms each session type uses* (normally, and also possible):

{{ $('Room Table').first().json.roomTable }}

*Rooms:*

{{ $('Room Table').first().json.roomNames }}

## Style

Philippine time (UTC+8). You write Slack mrkdwn - single asterisks for *bold*. Casual, friendly and direct - busy studio staff, not documentation. Match their language (English or Taglish) but never their tone: warm, even and professional."""
by["Jessie AI Agent"]["parameters"]["options"]["systemMessage"] = PROMPT

# ---- 1: every reply carries the buttons
BUILD_REPLY = r"""// Build Reply (main v271): every reply in the chat carries Book a room / My bookings (decided 15 Oct: every message leads to
// the buttons). An agent reply that still asks for booking details or asks for a yes is replaced by a pointer to the buttons.
const j = $input.first().json || {};
let text = String(j.output || '').trim();
let agent = false; try { agent = !!$('Guard Probe').first().json; } catch (e) { agent = false; }
const BOOKING_ASK = /(?:who(?:’|')?s the (?:client|engineer|arranger)|what(?:’|')?s the (?:project|client)|which (?:session type|room|studio)|what (?:kind|type) of (?:session|booking)|what time (?:should|works|do you)|confirm to (?:book|cancel|move)|reply yes or no|book it\?|\(yes\/no\))/i;
if (agent && BOOKING_ASK.test(text)) text = 'Tap *Book a room* below - the form asks for everything it needs. To change or cancel, open *My bookings*.';
if (!text) text = 'What would you like to do?';
const chunks = []; for (let i = 0; i < text.length && chunks.length < 40; i += 2900) chunks.push(text.slice(i, i + 2900));
const blocks = chunks.map(c => ({ type: 'section', text: { type: 'mrkdwn', text: c } })).concat([{ type: 'actions', elements: [
  { type: 'button', style: 'primary', action_id: 'open_book', value: 'menu', text: { type: 'plain_text', text: 'Book a room' } },
  { type: 'button', action_id: 'my_bookings', value: 'menu', text: { type: 'plain_text', text: 'My bookings' } } ] }]);
return [{ json: Object.assign({}, j, { output: text, reply: { text: text.slice(0, 3900), blocks } }) }];"""
x, y = by["Send Reply"]["position"]
old_send = by["Send Reply"]
wf["nodes"].remove(old_send)
wf["nodes"].extend([
    {"parameters": {"jsCode": BUILD_REPLY}, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [x - 200, y + 160], "id": str(uuid.uuid4()), "name": "Build Reply"},
    {"parameters": {"method": "POST", "url": "https://slack.com/api/chat.postMessage", "authentication": "predefinedCredentialType",
                    "nodeCredentialType": "slackApi", "sendBody": True, "specifyBody": "json",
                    "jsonBody": "={{ JSON.stringify({ channel: $('Slack Trigger').first().json.channel, text: $json.reply.text, blocks: $json.reply.blocks }) }}", "options": {}},
     "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [x, y], "id": str(uuid.uuid4()), "name": "Send Reply",
     "credentials": SLACK_CRED, "onError": "continueRegularOutput"},
])
for src, v in C.items():
    for outs in v.get("main", []):
        for c in outs:
            if c["node"] == "Send Reply" and src != "Build Reply":
                c["node"] = "Build Reply"
C["Build Reply"] = {"main": [[{"node": "Send Reply", "type": "main", "index": 0}]]}
by = {n["name"]: n for n in wf["nodes"]}

# ---- 2: "what can you do" -> what Jessie does, with the menu
patch("Menu Check", [
    ("const THANKS = /^", """// v271: asking what Jessie can do gets the menu with one line on what she does
const ABOUT = /^(?:what (?:can|do) you do(?: for me)?|what are you|who are you|what is this|what(?:’|')?s this|how (?:does this|do you|do i use this) work|how can you help(?: me)?|what are your (?:features|functions)|what can i do(?: here)?|help me|what do you offer|how do i (?:use|start)(?: this)?)\\??$/;
const THANKS = /^"""),
    ("let menu = raw.trim() !== '' && (phrase === '' || GREET.indexOf(phrase) !== -1 || /^(h+i+|he+y+|hel+o+)$/.test(phrase));\nlet why = menu ? 'greeting' : '';",
     "let menu = raw.trim() !== '' && (phrase === '' || GREET.indexOf(phrase) !== -1 || /^(h+i+|he+y+|hel+o+)$/.test(phrase));\nlet why = menu ? 'greeting' : '';\nif (!menu && ABOUT.test(phrase)) { menu = true; why = 'about'; }   // v271"),
    ("const head = why === 'thanks' ? 'Anytime! Anything else?' :",
     "const head = why === 'about' ? 'I book studios and rooms at Hit Productions - tap *Book a room*, or *My bookings* to see, change or cancel yours. You can also ask me what’s free or booked, and about the rooms.' : why === 'thanks' ? 'Anytime! Anything else?' :"),
])

# ---- 3: booking details without "book" lead to the form
patch("Form Offer", [
    ("  if (g.confirmed || g.confirmedCancel || g.confirmedMove) skip('a yes to a chat card');",
     """  // v271 (PENDING 116): booking details without "book" ("project orange", "studio 7 tomorrow 2-4pm", "i need studio 7 every
  // monday") are a booking request too - not a question, not a change or cancel, and naming a room, a date or time, a
  // session type, a project or a client
  if (!intent && !prev) {
    const q = /\\?/.test(t) || /^\\s*(?:what|when|where|who|whos|whose|which|why|how|is|are|am|can|could|do|does|did|will|would|should|may|any|have|has)\\b/i.test(t);
    const chg = /\\b(?:cancel|delete|remove|move|moving|resched\\w*|change|push|pull|extend|shorten|switch|instead|earlier|later)\\b|\\bmake it\\b/i.test(t);
    const roomish = /\\bstudio\\s*[1-8a-fm]\\b|\\bm[\\s-]?booth\\s*[1-8]\\b|\\bm[1-8]\\b|\\b(?:likha|salin|katha|lobby)\\b/i.test(t);
    const dateish = !!String(g.datesInMessage || '').trim() || /\\b\\d{1,2}(?::\\d{2})?\\s*(?:am|pm|nn)\\b|\\bnoon\\b/i.test(t);
    const detail = /\\b(?:project|client|session|recording|mixing|dubbing|editing|meeting|mastering|vo)\\b/i.test(t);
    if (!q && !chg && (roomish || dateish || detail)) intent = true;
  }
  if (g.confirmed || g.confirmedCancel || g.confirmedMove) skip('a yes to a chat card');"""),
    ("  const intent = /\\b(book|rebook|reserve)\\b/i.test(t)", "  let intent = /\\b(book|rebook|reserve)\\b/i.test(t)"),
])
wf["name"] = "Project Jessie — v271 (every message leads to the buttons)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
