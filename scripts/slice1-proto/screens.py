"""Slice 1 screens (docs/design/slack-app-v1-scope.md), as real Block Kit, for the click-through prototype.

Sample data: real dates (no QA year shift), real clients and staff (internal). build.py writes each screen to
docs/design/blockkit/slice1/<id>.json for the Block Kit Builder and wires them into flows in the prototype.
"""

pt = lambda t: {"type": "plain_text", "text": t}
md = lambda t: {"type": "mrkdwn", "text": t}
ctx = lambda *t: {"type": "context", "elements": [md(x) for x in t]}
sec = lambda t: {"type": "section", "text": md(t)}
dv = {"type": "divider"}


def opt(t, v=None, d=None):
    o = {"text": pt(t), "value": v or t}
    if d:
        o["description"] = pt(d)
    return o


def btn(t, a, style=None, confirm=None, v="x"):
    b = {"type": "button", "text": pt(t), "action_id": a, "value": v}
    if style:
        b["style"] = style
    if confirm:
        b["confirm"] = confirm
    return b


acts = lambda *e: {"type": "actions", "elements": list(e)}


def inp(bid, label, el, optional=False, hint=None):
    b = {"type": "input", "block_id": bid, "label": pt(label), "element": el}
    if optional:
        b["optional"] = True
    if hint:
        b["hint"] = pt(hint)
    return b


def radio(a, options, i=0):
    return {"type": "radio_buttons", "action_id": a, "options": options, "initial_option": options[i]}


def text_in(a, value=None, multiline=False, ph=None):
    e = {"type": "plain_text_input", "action_id": a}
    if value:
        e["initial_value"] = value
    if multiline:
        e["multiline"] = True
    if ph:
        e["placeholder"] = pt(ph)
    return e


users = lambda a, ph: {"type": "users_select", "action_id": a, "placeholder": pt(ph)}
date = lambda a, d: {"type": "datepicker", "action_id": a, "initial_date": d}
time = lambda a, t: {"type": "timepicker", "action_id": a, "initial_time": t, "timezone": "Asia/Manila"}


def modal(title, blocks, submit=None, close="Cancel", cb="view"):
    m = {"type": "modal", "callback_id": cb, "title": pt(title), "close": pt(close), "blocks": blocks}
    if submit:
        m["submit"] = pt(submit)
    return m


msg = lambda blocks: {"blocks": blocks}

SESSION_GROUPS = [
    {"label": pt("Sessions"), "options": [opt(t) for t in [
        "VO Recording", "Post Mixing", "Music Mixing", "Music Vocal Recording", "Band Recording", "Celebrity Recording",
        "QC", "Post Processing", "Localization Dubbing", "Localization Editing", "Localization Mixing",
        "Localization Atmos Mixing"]]},
    {"label": pt("Not a session"), "options": [opt("Meeting"), opt("Event"), opt("Booth time (M booth)", "booth")]},
]


def what_for(initial):
    return inp("purpose", "What's it for?", {"type": "static_select", "action_id": "purpose_pick", "initial_option": opt(initial),
                                             "option_groups": SESSION_GROUPS},
               hint="Jessie offers the rooms that can do this, the usual ones first.")


def step1(d, t0, t1, purpose):
    return modal("Book a room", [
        ctx("*Step 1 of 2* · when, and what for"),
        inp("date", "Date", date("date_pick", d)),
        inp("start", "Start", time("start_pick", t0)),
        inp("end", "End", time("end_pick", t1)),
        what_for(purpose),
    ], submit="Find rooms", cb="book_step1")


def studio_details(project=None, client=None, title_hint="*QAW1 / <client> / HL*"):
    return [
        dv,
        inp("project", "Project", text_in("project_in", project)),
        inp("client", "Client", text_in("client_in", client), optional=True, hint="Leave empty if there's no client. A new name is fine."),
        inp("engineer", "Engineer", users("engineer_pick", "You"), hint="Set to you. Change it if someone else is engineering."),
        inp("notes", "Notes", text_in("notes_in", multiline=True), optional=True),
        ctx("Calendar title: " + title_hint),
    ]


VO_ROOMS = [opt("Studio 8", d="Recommended · usual for VO Recording"), opt("Studio F", d="Usual for VO Recording"),
            opt("Studio C", d="Usual for VO Recording")]


def step2(when, rooms, note=None, project=None, client=None, title="*QAW1 / <client> / HL*", lead="*Step 2 of 2* · room and details",
          warn=None):
    b = []
    if warn:
        b += [sec(warn), dv]
    b += [ctx(lead), sec("🗓️ *" + when + "*"), inp("room", "Room", radio("room_radio", rooms))]
    if note:
        b.append(ctx(note))
    return modal("Book a room", b + studio_details(project, client, title), submit="Book", close="Back", cb="book_step2")


def booking(room, when):
    return modal("Book a room", [sec("⏳ *Booking " + room + "…*\n" + when),
                                 ctx("Checking the room, writing it to the calendar and waiting for the room to accept. A few seconds.")], close="Close")


def booked(title, line, room):
    return modal("Book a room", [sec("✅ *Booked.*\n*" + title + "*\n" + line),
                                 ctx(room + " accepted. The details and the Move / Cancel buttons are in your DM.")], close="Done")


def result(title, line, meta):
    return msg([sec("✅ *Booked.*\n*" + title + "*\n" + line), ctx(meta), acts(btn("Move", "move"), btn("Cancel", "cancel", "danger"))])


T1 = "QAW1 / Sasa Abella / HL"
W1 = "Thursday, Oct 15 · 2:00–4:00 PM"
S = {}

# ---- starting -------------------------------------------------------------------------------------------------------
S["01-menu"] = ("message", msg([
    sec("Hi! What would you like to do?"),
    acts(btn("Book a room", "open_book", "primary"), btn("My bookings", "my_bookings")),
    ctx("Or just type it, like _book studio 7 tomorrow 2-4pm_ or _is studio 8 free friday?_"),
]))
S["02-typed-request"] = ("message", msg([
    sec("🗓️ *Studio 7 · Thursday, Oct 15 · 2:00–4:00 PM*\nVO Recording · QAW1 · Sasa Abella"),
    acts(btn("Book a room", "open_book_prefilled", "primary")),
    ctx("Opens the form with these filled in."),
]))
S["03-not-understood"] = ("message", msg([
    sec("I can only help with studio bookings. Here's what I can do:"),
    acts(btn("Book a room", "open_book", "primary"), btn("My bookings", "my_bookings")),
]))

# ---- booking a studio ------------------------------------------------------------------------------------------------
S["10-step1"] = ("modal", step1("2026-10-15", "14:00", "16:00", "VO Recording"))
S["11-step2"] = ("modal", step2(W1 + " · VO Recording", VO_ROOMS, "Not free then: Studio 7 (free from 4:00 PM)", "QAW1"))
S["12-booking-s8"] = ("modal", booking("Studio 8", W1))
S["13-booked-s8"] = ("modal", booked(T1, "Studio 8 · " + W1, "Studio 8"))
S["14-result-s8"] = ("message", result(T1, "Studio 8 · " + W1, "VO Recording · Engineer: you · Advertising"))

S["15-step2-prefilled"] = ("modal", step2(W1 + " · VO Recording",
    [opt("Studio 7", d="You asked for this · usual for VO Recording")] + VO_ROOMS[:2], None, "QAW1", "Sasa Abella",
    "*QAW1 / Sasa Abella / HL*", "*Step 2 of 2* · _date, time and session type came from your message - Back to change them_"))
S["16-booking-s7"] = ("modal", booking("Studio 7", W1))
S["17-booked-s7"] = ("modal", booked(T1, "Studio 7 · " + W1, "Studio 7"))
S["18-result-s7"] = ("message", result(T1, "Studio 7 · " + W1, "VO Recording · Engineer: you · Advertising"))

S["19-problem"] = ("modal", modal("Book a room", [
    sec("⚠️ *Studio 8 was just booked by someone else* for 2:00–3:00 PM. Pick another room, or go Back to change the time."),
    dv,
    sec("🗓️ *" + W1 + " · VO Recording*"),
    inp("room", "Room", radio("room_radio", [opt("Studio F", d="Recommended · usual for VO Recording"), opt("Studio C", d="Usual for VO Recording")])),
    dv,
    inp("project", "Project", text_in("project_in", "QAW1")),
    inp("client", "Client", text_in("client_in", "Sasa Abela"), optional=True, hint="Did you mean Sasa Abella? Change it, or keep it as typed."),
    ctx("Everything else you entered is kept."),
], submit="Book", close="Back"))
S["21-booking-sf"] = ("modal", booking("Studio F", W1))
S["22-booked-sf"] = ("modal", booked(T1, "Studio F · " + W1, "Studio F"))
S["23-result-sf"] = ("message", result(T1, "Studio F · " + W1, "VO Recording · Engineer: you · Advertising"))

# ---- meeting and localization ----------------------------------------------------------------------------------------
WM = "Thursday, Oct 15 · 3:00–4:00 PM"
S["30-step1-meeting"] = ("modal", step1("2026-10-15", "15:00", "16:00", "Meeting"))
S["31-step2-meeting"] = ("modal", modal("Book a room", [
    ctx("*Step 2 of 2* · room and details"),
    sec("🗓️ *" + WM + " · Meeting*"),
    inp("room", "Room", radio("room_radio", [opt("Likha", d="Recommended"), opt("Salin"), opt("Katha")])),
    dv,
    inp("title", "Meeting title", text_in("title_in", "Q4 planning")),
    inp("notes", "Notes", text_in("notes_in", multiline=True), optional=True),
    ctx("Calendar title: *LIKHA - Q4 planning*"),
], submit="Book", close="Back"))
S["32-booking-likha"] = ("modal", booking("Likha", WM))
S["33-booked-likha"] = ("modal", booked("LIKHA - Q4 planning", "Likha · " + WM, "Likha"))
S["34-result-likha"] = ("message", msg([sec("✅ *Booked.*\n*LIKHA - Q4 planning*\nLikha · " + WM), ctx("Meeting"),
                                         acts(btn("Move", "move"), btn("Cancel", "cancel", "danger"))]))
WL = "Thursday, Oct 15 · 9:00 AM – 2:00 PM"
S["35-step1-localization"] = ("modal", step1("2026-10-15", "09:00", "14:00", "Localization Dubbing"))
S["36-step2-localization"] = ("modal", modal("Book a room", [
    ctx("*Step 2 of 2* · room and details"),
    sec("🗓️ *" + WL + " · Localization Dubbing*"),
    inp("room", "Room and booth", radio("room_radio", [opt("Studio 1 + Studio A", "Studio 1|Studio A", "Recommended · control room and its booth"),
                                                       opt("Studio 2 + Studio B", "Studio 2|Studio B", "Control room and its booth")])),
    dv,
    inp("code", "Project code", text_in("code_in", "LOPH S2"), hint="As in Localization Projects. The client and the title come from it."),
    inp("engineer", "Engineer", users("engineer_pick", "You"), hint="Set to you."),
    inp("notes", "Notes", text_in("notes_in", multiline=True), optional=True),
    ctx("Booking type: Entertainment · Calendar title: *LOPH S2 / HL*"),
], submit="Book", close="Back"))
S["37-booking-loc"] = ("modal", booking("Studio 1 + Studio A", WL))
S["38-booked-loc"] = ("modal", booked("LOPH S2 / HL", "Studio 1 + Studio A · " + WL, "Studio 1 and Studio A"))

# ---- my bookings, cancel, move ---------------------------------------------------------------------------------------
CONFIRM = {"title": pt("Cancel this booking?"), "text": md("*" + T1 + "*\nThu, Oct 15 · 2:00–4:00 PM · Studio 8"),
           "confirm": pt("Cancel booking"), "deny": pt("Keep it"), "style": "danger"}


def my_bookings(first_state="live"):
    if first_state == "live":
        first = [sec("*" + T1 + "*\nThu, Oct 15 · 2:00–4:00 PM · Studio 8"), ctx("VO Recording · Engineer: you"),
                 acts(btn("Move", "move"), btn("Cancel", "cancel", "danger", confirm=CONFIRM))]
    elif first_state == "cancelled":
        first = [sec("~" + T1 + "~\n~Thu, Oct 15 · 2:00–4:00 PM · Studio 8~"), ctx("❌ Cancelled by you · the engineer was told")]
    else:
        first = [sec("*" + T1 + "*\nFri, Oct 16 · 2:00–4:00 PM · Studio 8"), ctx("✅ Moved from Thu, Oct 15 · the engineer was told"),
                 acts(btn("Move", "move"), btn("Cancel", "cancel", "danger"))]
    return msg([sec("*Your bookings · next 7 days*")] + first + [
        dv,
        sec("*QAW7 / HL*\nMon, Oct 19 · 1:00–3:00 PM · Studio 8"), ctx("Music Mixing · Engineer: you"),
        acts(btn("Move", "move2"), btn("Cancel", "cancel2", "danger")),
        dv,
        sec("*You're engineering*"),
        sec("*BLUE BIRD / Harold Orozco / HL*\nFri, Oct 16 · 10:00 AM – 12:00 PM · Studio F"), ctx("Booked by Glenn Mariano · you can change it too"),
        acts(btn("Move", "move3"), btn("Cancel", "cancel3", "danger")),
    ])


S["40-my-bookings"] = ("message", my_bookings())
S["41-my-bookings-cancelled"] = ("message", my_bookings("cancelled"))
S["42-move-form"] = ("modal", modal("Move booking", [
    sec("*" + T1 + "*\nNow: Thu, Oct 15 · 2:00–4:00 PM · Studio 8"),
    dv,
    inp("date", "New date", date("date_pick", "2026-10-16")),
    inp("start", "Start", time("start_pick", "14:00")),
    inp("end", "End", time("end_pick", "16:00"), hint="Set to keep the same length (2 hours)."),
    inp("room", "Room", {"type": "static_select", "action_id": "room_pick", "initial_option": opt("Keep Studio 8", "keep"),
                         "options": [opt("Keep Studio 8", "keep"), opt("Studio F"), opt("Studio C"), opt("Studio 7")]}),
    ctx("The new time is checked first. The booking stays where it is until the new one is in place."),
], submit="Move", close="Cancel"))
S["43-moving"] = ("modal", modal("Move booking", [sec("⏳ *Moving " + T1 + "…*\nto Friday, Oct 16 · 2:00–4:00 PM · Studio 8")], close="Close"))
S["44-moved"] = ("modal", modal("Move booking", [sec("✅ *Moved.*\n*" + T1 + "*\nFriday, Oct 16 · 2:00–4:00 PM · Studio 8"),
                                                 ctx("The engineer was told. Your bookings list is updated.")], close="Done"))
S["45-my-bookings-moved"] = ("message", my_bookings("moved"))

# ---- typed changes and questions -------------------------------------------------------------------------------------
C2 = {"title": pt("Cancel this booking?"), "text": md("*QAW9 / HL*\nFri, Oct 16 · 4:00–5:00 PM · Studio 8"),
      "confirm": pt("Cancel booking"), "deny": pt("Keep it"), "style": "danger"}


def typed_matches(second_cancelled=False):
    second = ([sec("~QAW9 / HL~\n~Fri, Oct 16 · 4:00–5:00 PM · Studio 8~"), ctx("❌ Cancelled by you")] if second_cancelled else
              [sec("*QAW9 / HL*\nFri, Oct 16 · 4:00–5:00 PM · Studio 8"), acts(btn("Move", "move_b"), btn("Cancel", "cancel_b", "danger", confirm=C2))])
    return msg([sec("You have two bookings on Friday, Oct 16:"),
                sec("*QAW9 / HL*\nFri, Oct 16 · 10:00–11:00 AM · Studio 8"), acts(btn("Move", "move"), btn("Cancel", "cancel", "danger"))] + second)


S["50-typed-cancel"] = ("message", typed_matches())
S["51-typed-cancel-done"] = ("message", typed_matches(True))
S["52-typed-question"] = ("message", msg([
    sec("🗓️ *Free tomorrow, Thu Oct 15, 12:00 – 6:00 PM*"),
    {"type": "section", "text": md("*Studio 8* · free the whole afternoon"), "accessory": btn("Book", "book_s8")},
    {"type": "section", "text": md("*Studio 6* · free 3:00 – 6:00 PM"), "accessory": btn("Book", "book_s6")},
    {"type": "section", "text": md("*Studio C* · free 12:00 – 2:00 PM"), "accessory": btn("Book", "book_sc")},
    ctx("Studios only. Afternoon = 12:00 – 6:00 PM."),
]))
_q = step1("2026-10-15", "12:00", "18:00", "VO Recording")
_q["blocks"][0] = ctx("*Step 1 of 2* · _Studio 8 and the free window came from the answer - shorten the time and pick what it's for_")
S["53-step1-from-question"] = ("modal", _q)
S["54-step2-from-question"] = ("modal", step2("Thursday, Oct 15 · 12:00–2:00 PM · VO Recording",
    [opt("Studio 8", d="You picked this · usual for VO Recording")] + VO_ROOMS[1:], None, "QAW1"))
