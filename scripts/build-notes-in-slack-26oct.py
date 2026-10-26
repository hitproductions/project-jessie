#!/usr/bin/env python3
"""Builds the booking note in Slack, 26 Oct: Slack Interactions v44, main v283, Reminders v6, Move Booking v38, Cancel v32.

Howard (26 Oct): "maybe we should also find a way to include the notes into the slack messages?" - picked: Booked / Changed
cards, engineer / arranger notices, reminders, My bookings list.
  - A card (Booked, Changed, Cancelled, reminders, the engineer / arranger notices that carry the card): "*Notes:*" and the note
    at the end (line breaks kept; at most 600 characters).
  - A list row (My bookings, typed "what do I have"): "📝" and the note's first line (at most 80 characters).
  - The note comes from the event (Book Session v122's "Notes:" block, or an older booking's inline "| Notes: …"), from the
    form for a new booking / series, and from the replacement for a change (Move v38 returns its description).
  - Cancel v32 / Move v38: the cancel / move notice cards show it too.
Built on the live downloads (workflows/imported/*-imported.json).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HELPERS = r"""// v44 / v283 / Reminders v6 (26 Oct, Howard): the booking's note in Slack - "*Notes:*" at the end of a card, "📝" and its first
// line in a list. From the event's "Notes:" block (Book Session v122) or an older booking's inline "| Notes: …".
function evNote(e) { const d = String((e && e.description) || ''); const m = d.match(/\n\s*\n\s*Notes?:\s*([\s\S]*)$/i) || d.match(/(?:^|\|)\s*Notes?:\s*([^|]*)$/i) || d.match(/(?:^|\|)\s*Notes?:\s*([^|\n]*)/i); return m ? m[1].trim() : ''; }
function noteLine(nt) { nt = String(nt || '').trim(); if (!nt) return ''; if (nt.length > 600) nt = nt.slice(0, 600).trim() + '…'; return '\n*Notes:*' + (/\n/.test(nt) ? '\n' : ' ') + nt; }
function noteRow(nt) { const f = String(nt || '').split('\n').map(x => x.trim()).find(Boolean) || ''; return f ? '\n📝 ' + (f.length > 80 ? f.slice(0, 80).trim() + '…' : f) : ''; }
"""


def load(f):
    return json.load(open(os.path.join(ROOT, "workflows", "imported", f)))


def save(wf, out, title):
    wf["name"] = title
    with open(os.path.join(ROOT, "workflows", out), "w") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote workflows/" + out)


def node(wf, name):
    return [x for x in wf["nodes"] if x["name"] == name][0]


def sub(wf, name, a, b, n=1):
    nd = node(wf, name)
    js = nd["parameters"]["jsCode"]
    assert js.count(a) == n, (name, js.count(a), a[:80])
    nd["parameters"]["jsCode"] = js.replace(a, b)


EVB1 = "return { id: e.id, d: a.d, s: a.hm, e: b.hm, r: evRoom(e), t: e.summary || '(no title)', st: evType(e) }; }"
EVB2 = "return { id: e.id, d: String((e.start && e.start.date) || ''), s: '', e: '', r: evRoom(e), t: e.summary || '(no title)', st: evType(e) };"
CARD_END = "(roomHold(b.r) ? '\\n*Holding room:* ' + roomHold(b.r) : ''); }"


def helpers(wf, want_card=True):
    """the helpers before evBooking; evBooking carries the note; bkCard ends with it"""
    hits = [0, 0, 0, 0]
    for n in wf["nodes"]:
        js = n.get("parameters", {}).get("jsCode") or ""
        if "function evBooking(e) {" not in js:
            continue
        js = js.replace("function evBooking(e) {", HELPERS + "function evBooking(e) {", 1); hits[0] += 1
        c1, c2 = js.count(EVB1), js.count(EVB2)
        js = js.replace(EVB1, EVB1.replace("st: evType(e) }; }", "st: evType(e), nt: evNote(e) }; }")).replace(EVB2, EVB2.replace("st: evType(e) };", "st: evType(e), nt: evNote(e) };"))
        hits[1] += c1; hits[2] += c2
        if "function bkCard(b, head)" in js:
            i = js.index("function bkCard(b, head)"); j = js.index("\n", i)
            line = js[i:j]
            assert line.endswith(CARD_END), (n["name"], line[-80:])
            js = js[:i] + line[:-len("; }")] + " + noteLine(b.nt); }" + js[j:]; hits[3] += 1
        n["parameters"]["jsCode"] = js
    return hits


# ---------------- Slack Interactions v44
si = load("slack-interactions-v43-imported.json")
print("SI helpers / evBooking / evBooking all-day / bkCard:", helpers(si))
# the Booked card: the form's note (its "Notes: …" segment in the booking's description)
sub(si, "After Book", "(roomHold(F['Room'] || R.rooms || R.room) ? '\\n*Holding room:* ' + roomHold(F['Room'] || R.rooms || R.room) : '');   // v21",
    "(roomHold(F['Room'] || R.rooms || R.room) ? '\\n*Holding room:* ' + roomHold(F['Room'] || R.rooms || R.room) : '')   // v21\n"
    "  + noteLine(evNote({ description: (A.book || {}).description }));   // v44: the note")
# a series' card
sub(si, "After Book Series", "  + booked.map(d => '- ' + sh(d)).join('\\n') + (tm[0] ? '\\n*Time:* ' + t12(tm[0]) + ' – ' + t12(tm[1]) : '') + (T.rooms ? '\\n*Room:* ' + roomMain(T.rooms) + (roomHold(T.rooms) ? '\\n*Holding room:* ' + roomHold(T.rooms) : '') : '')",
    "  + booked.map(d => '- ' + sh(d)).join('\\n') + (tm[0] ? '\\n*Time:* ' + t12(tm[0]) + ' – ' + t12(tm[1]) : '') + (T.rooms ? '\\n*Room:* ' + roomMain(T.rooms) + (roomHold(T.rooms) ? '\\n*Holding room:* ' + roomHold(T.rooms) : '') : '')\n"
    "  + noteLine(evNote({ description: T.description }))   // v44: the note")
nd = node(si, "After Book Series"); nd["parameters"]["jsCode"] = HELPERS + nd["parameters"]["jsCode"]
# a change: the replacement's note (Move v38 returns its description)
sub(si, "After Move", "  const nb = { id: String(r.event_id || b.id), d: n.d, s: n.s, e: n.e, r: n.r || b.r, t: ($('To Move').first().json.new_summary) || b.t };",
    "  const nb = { id: String(r.event_id || b.id), d: n.d, s: n.s, e: n.e, r: n.r || b.r, t: ($('To Move').first().json.new_summary) || b.t, nt: evNote({ description: r.description }) };   // v44: the note")
# My bookings rows
sub(si, "Render My Bookings", "md('*' + x.b.t + '*\\n' + whenLine(x.b) + (x.note ? '\\n_' + x.note + '_' : ''))",
    "md('*' + x.b.t + '*\\n' + whenLine(x.b) + noteRow(x.b.nt) + (x.note ? '\\n_' + x.note + '_' : ''))")
save(si, "slack-interactions-v44.json", "Jessie — Slack Interactions — v44 (the note in Slack)")

# ---------------- main v283
mn = load("project-jessie-v282-imported.json")
print("main helpers:", helpers(mn))
sub(mn, "Mine Reply", "md('*' + b.t + '*\\n' + whenLine(b))", "md('*' + b.t + '*\\n' + whenLine(b) + noteRow(b.nt))")
save(mn, "project-jessie-v283.json", "Project Jessie — v283 (the note in my bookings)")

# ---------------- Reminders v6
rm = load("reminders-v5-imported.json")
print("Reminders helpers:", helpers(rm))
save(rm, "reminders-v6.json", "Jessie — Reminders — v6 (the note on the card)")

# ---------------- Cancel v32 / Move v38: the notice card
NOTICE_OLD = "(ROOM ? '\\n*Room:* ' + ROOM : '');"
NOTICE_NEW = ("(ROOM ? '\\n*Room:* ' + ROOM : '') + (() => {   // v32 Cancel / v38 Move: the note\n"
              "  const d = String(co.description || co.notes_desc || ''), m = d.match(/\\n\\s*\\n\\s*Notes?:\\s*([\\s\\S]*)$/i) || d.match(/(?:^|\\|)\\s*Notes?:\\s*([^|\\n]*)/i);\n"
              "  let nt = (m ? m[1] : '').trim(); if (!nt) return ''; if (nt.length > 600) nt = nt.slice(0, 600).trim() + '…'; return '\\n*Notes:*' + (/\\n/.test(nt) ? '\\n' : ' ') + nt; })();")
cx = load("cancel-booking-v31-imported.json")
sub(cx, "Check Ownership", "room: cxRoom(ev) || '',   // v30: for the notice card",
    "room: cxRoom(ev) || '', notes_desc: String(ev.description || ''),   // v30: for the notice card; v32: its note")
sub(cx, "Build Recipients", NOTICE_OLD, NOTICE_NEW)
save(cx, "cancel-booking-v32.json", "Jessie — Cancel Booking — v32 (the note on the notice)")
mv = load("move-booking-v37-imported.json")
sub(mv, "Build Recipients", NOTICE_OLD, NOTICE_NEW)
for nm in ["Return Moved", "Return Delete Failed"]:
    sub(mv, nm, "event_id: created.id || '',", "event_id: created.id || '', description: created.description || R.description || '',   /* v38: the Changed card's note */")
save(mv, "move-booking-v38.json", "Jessie — Move Booking — v38 (the note on the notice and the Changed card)")
