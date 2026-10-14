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
        acts({"type": "checkboxes", "action_id": "repeat_toggle", "options": [{"text": md("_Repeats_"), "value": "repeat"}]}),
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
          warn=None, extras=None):
    b = []
    if warn:
        b += [sec(warn), dv]
    b += [ctx(lead), sec("🗓️ *" + when + "*"), inp("room", "Room", radio("room_radio", rooms))]
    if note:
        b.append(ctx(note))
    if extras:
        b += extras
    return modal("Book a room", b + studio_details(project, client, title), submit="Book", close="Back", cb="book_step2")


def add_check(action, label, ticked=False):
    """One small unlabeled checkbox line under the room list - ticking it redraws the form with that picker."""
    o = {"text": md("_" + label + "_"), "value": action}
    e = {"type": "checkboxes", "action_id": action, "options": [o]}
    if ticked:
        e["initial_options"] = [o]
    return acts(e)


def booth_picker(note):
    return inp("booth", "Booth", {"type": "static_select", "action_id": "booth_pick", "initial_option": opt("Studio A"),
                                  "option_groups": [{"label": pt("Free then"), "options": [opt("Studio A"), opt("Studio B"), opt("Studio D")]}]},
               hint=note)


VO_EXTRAS = [add_check("add_booth", "+ Vocal booth")]


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
S["11-step2"] = ("modal", step2(W1 + " · VO Recording", VO_ROOMS, "Not free then: Studio 7 (free from 4:00 PM)", "QAW1", extras=VO_EXTRAS))
S["12-booking-s8"] = ("modal", booking("Studio 8", W1))
S["13-booked-s8"] = ("modal", booked(T1, "Studio 8 · " + W1, "Studio 8"))
S["14-result-s8"] = ("message", result(T1, "Studio 8 · " + W1, "VO Recording · Engineer: you · Advertising"))

S["15-step2-prefilled"] = ("modal", step2(W1 + " · VO Recording",
    [opt("Studio 7", d="You asked for this · usual for VO Recording")] + VO_ROOMS[:2], None, "QAW1", "Sasa Abella",
    "*QAW1 / Sasa Abella / HL*", "*Step 2 of 2* · _date, time and session type came from your message - Back to change them_", extras=VO_EXTRAS))
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
def studio_booth(booth, studios, booth_note, series=False):
    """Studio and booth chosen separately: the booth defaults to the studio's usual one (Airtable Paired with) and any free
    vocal booth can be picked instead - the engineer patches it (Dante)."""
    booths = [opt("Studio A"), opt("Studio B"), opt("Studio D")]
    return [inp("room", "Studio", radio("room_radio", studios)),
            inp("booth", "Booth", {"type": "static_select", "action_id": "booth_pick", "initial_option": opt(booth),
                                   "option_groups": [{"label": pt("Free then" + (" on all dates" if series else "")), "options": booths}]},
                hint=booth_note)]


WL = "Thursday, Oct 15 · 9:00 AM – 2:00 PM"
S["35-step1-localization"] = ("modal", step1("2026-10-15", "09:00", "14:00", "Localization Dubbing"))
def loc_step2(booth, note):
    return modal("Book a room", [
    ctx("*Step 2 of 2* · room and details"),
    sec("🗓️ *" + WL + " · Localization Dubbing*"),
] + studio_booth(booth, [opt("Studio 1", d="Recommended · usual for Localization Dubbing"), opt("Studio 2", d="Usual for Localization Dubbing"), opt("Studio 6", d="Usual for Localization Dubbing")], note) + [
    dv,
    inp("code", "Project code", text_in("code_in", "LOPH S2"), hint="As in Localization Projects. The client and the title come from it."),
    inp("engineer", "Engineer", users("engineer_pick", "You"), hint="Set to you."),
    inp("notes", "Notes", text_in("notes_in", multiline=True), optional=True),
    ctx("Booking type: Entertainment · Calendar title: *LOPH S2 / HL*"),
], submit="Book", close="Back")


S["36-step2-localization"] = ("modal", loc_step2("Studio A", "Set to Studio 1's usual booth. Any free booth works - the engineer patches it."))
S["36b-step2-localization-booth-b"] = ("modal", loc_step2("Studio B", "Not Studio 1's usual booth - the engineer patches it (Dante)."))
S["37-booking-loc"] = ("modal", booking("Studio 1 + Studio B", WL))
S["38-booked-loc"] = ("modal", booked("LOPH S2 / HL", "Studio 1 + Studio B · " + WL, "Studio 1 and Studio B"))

# ---- my bookings, cancel, move ---------------------------------------------------------------------------------------
CONFIRM = {"title": pt("Cancel this booking?"), "text": md("*" + T1 + "*\nThu, Oct 15 · 2:00–4:00 PM · Studio 8"),
           "confirm": pt("Cancel booking"), "deny": pt("Keep it"), "style": "danger"}


def my_bookings(first_state="live"):
    if first_state == "live":
        first = [sec("*" + T1 + "*\nThu, Oct 15 · 2:00–4:00 PM · Studio 8"), ctx("VO Recording · Engineer: you"),
                 acts(btn("Move", "move"), btn("Cancel", "cancel", "danger", confirm=CONFIRM))]
    elif first_state == "cancelled":
        first = [sec("~" + T1 + "~\n~Thu, Oct 15 · 2:00–4:00 PM · Studio 8~"), ctx("❌ Cancelled by you")]
    else:
        first = [sec("*" + T1 + "*\nFri, Oct 16 · 2:00–4:00 PM · Studio 8"), ctx("✅ Moved from Thu, Oct 15"),
                 acts(btn("Move", "move"), btn("Cancel", "cancel", "danger"))]
    return msg([sec("*Your bookings · next 7 days*")] + first + [
        dv,
        sec("*QAW7 / HL*\nMon, Oct 19 · 1:00–3:00 PM · Studio 8"), ctx("Music Mixing · Engineer: you"),
        acts(btn("Move", "move2"), btn("Cancel", "cancel2", "danger")),
        dv,
        sec("*You're engineering*"),
        sec("*BLUE BIRD / Harold Orozco / HL*\nFri, Oct 16 · 10:00 AM – 12:00 PM · Studio F"), ctx("Booked by Glenn Mariano · you can change it too"),
        acts(btn("Move", "move3"), btn("Cancel", "cancel3", "danger")),
        dv,
        acts(btn("Next 7 days", "week_next")),
        ctx("Or ask, like _what do I have next month?_"),
    ])


S["40-my-bookings"] = ("message", my_bookings())
S["46-my-bookings-week2"] = ("message", msg([
    sec("*Your bookings · Oct 22 – 28*"),
    sec("*SUMMER JINGLE / Dante Nora / DR x HL*\nTue, Oct 27 · 1:00–5:00 PM · Studio F"), ctx("Music Mixing · Arranger: you"),
    acts(btn("Move", "move4"), btn("Cancel", "cancel4", "danger")),
    dv,
    acts(btn("Previous 7 days", "week_prev"), btn("Next 7 days", "week_next2")),
]))
S["41-my-bookings-cancelled"] = ("message", my_bookings("cancelled"))
def move_form(day, warn=None):
    b = []
    if warn:
        b += [sec(warn), dv]
    b += [sec("*" + T1 + "*\nNow: Thu, Oct 15 · 2:00–4:00 PM · Studio 8"),
          dv,
          ctx("Starts at the booking's current date, time and room - change only what moves."),
          inp("date", "Date", date("date_pick", day)),
          inp("start", "Start", time("start_pick", "14:00")),
          inp("end", "End", time("end_pick", "16:00"), hint="Keeps the same length (2 hours) unless you change it."),
          inp("room", "Room", {"type": "static_select", "action_id": "room_pick", "initial_option": opt("Studio 8 (now)", "keep"),
                               "options": [opt("Studio 8 (now)", "keep"), opt("Studio F"), opt("Studio C"), opt("Studio 7")]}),
          ctx("The new time is checked first. The booking stays where it is until the new one is in place.")]
    return modal("Move booking", b, submit="Move", close="Cancel")


S["42-move-form"] = ("modal", move_form("2026-10-15"))
S["42b-move-form-changed"] = ("modal", move_form("2026-10-16"))
S["42c-move-unchanged"] = ("modal", move_form("2026-10-15", "⚠️ *Nothing changed.* This is the booking's current date, time and room. Change one of them, or press Cancel - nothing is moved or booked again."))
S["43-moving"] = ("modal", modal("Move booking", [sec("⏳ *Moving " + T1 + "…*\nto Friday, Oct 16 · 2:00–4:00 PM · Studio 8")], close="Close"))
S["44-moved"] = ("modal", modal("Move booking", [sec("✅ *Moved.*\n*" + T1 + "*\nFriday, Oct 16 · 2:00–4:00 PM · Studio 8"),
                                                 ctx("Your bookings list is updated.")], close="Done"))
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
    [opt("Studio 8", d="You picked this · usual for VO Recording")] + VO_ROOMS[1:], None, "QAW1", extras=VO_EXTRAS))

# ---- series (moved into slice 1 on 14 Oct for Localization batches) ----------------------------------------------------
_days = [opt(a, b) for a, b in [("Mon", "MO"), ("Tue", "TU"), ("Wed", "WE"), ("Thu", "TH"), ("Fri", "FR"), ("Sat", "SA"), ("Sun", "SU")]]
_rep = {"text": md("_Repeats_"), "value": "repeat"}


def series_step1(ticked):
    b = [ctx("*Step 1 of 2* · when, and what for"),
         inp("date", "First date" if ticked else "Date", date("date_pick", "2026-10-19")),
         inp("start", "Start", time("start_pick", "09:00")),
         inp("end", "End", time("end_pick", "14:00")),
         acts(dict({"type": "checkboxes", "action_id": "repeat_toggle", "options": [_rep]}, **({"initial_options": [_rep]} if ticked else {})))]
    if ticked:
        b += [inp("freq", "How often", radio("freq_pick", [opt("Weekly", "weekly"), opt("Daily", "daily")])),
              inp("days", "On", {"type": "checkboxes", "action_id": "days_pick", "options": _days, "initial_options": _days[:5]}),
              inp("ends", "Ends", radio("ends_pick", [opt("After a number of occurrences", "count"), opt("On a date", "until")])),
              inp("count", "Number of occurrences", {"type": "number_input", "action_id": "count_in", "is_decimal_allowed": False,
                                                     "min_value": "2", "max_value": "16", "initial_value": "10"}, hint="Up to 16, within a year.")]
    b.append(what_for("Localization Dubbing"))
    return modal("Book a room", b, submit="Find rooms", cb="book_step1")


S["60-series-step1"] = ("modal", series_step1(False))
S["61-series-step1-repeats"] = ("modal", series_step1(True))
_dates = ["Mon, Oct 19", "Tue, Oct 20", "Wed, Oct 21", "Thu, Oct 22", "Fri, Oct 23", "Mon, Oct 26", "Tue, Oct 27", "Wed, Oct 28", "Thu, Oct 29", "Fri, Oct 30"]


def _date_line(t):
    return {"type": "section", "text": md(t),
            "accessory": {"type": "overflow", "action_id": "date_menu", "options": [{"text": pt(x), "value": x} for x in ("Skip this date", "Use another room", "Change the time")]}}


S["62-series-step2"] = ("modal", modal("Book a room", [
    ctx("*Step 2 of 2* · room and details"),
    sec("🗓️ *Mon – Fri · 9:00 AM – 2:00 PM · 10 dates from Oct 19 · Localization Dubbing*"),
] + studio_booth("Studio A", [opt("Studio 1", d="Recommended · free on all 10 dates"), opt("Studio 2", d="Free on 9 of 10 dates")],
                 "Set to Studio 1's usual booth. Any booth free on all dates works.", series=True) + [
    dv,
    sec("*Dates*"),
] + [_date_line("✓ " + d) for d in _dates] + [
    ctx("Use ⋯ on a date to skip it, change its room or its time."),
    dv,
    inp("code", "Project code", text_in("code_in", "LOPH S2"), hint="As in Localization Projects. The client and the title come from it."),
    inp("engineer", "Engineer", users("engineer_pick", "You"), hint="Set to you."),
    inp("notes", "Notes", text_in("notes_in", multiline=True), optional=True),
], submit="Book 10 dates", close="Back"))
S["63-series-booking"] = ("modal", modal("Book a room", [
    sec("⏳ *Booking 10 dates…*\nStudio 1 + Studio A · Mon – Fri · 9:00 AM – 2:00 PM"),
    ctx("Each date is checked and written to the calendar. This takes a few minutes - you can close this; the result comes to your DM."),
], close="Close"))
S["64-series-result"] = ("message", msg([
    sec("✅ *Booked 10 of 10 dates.* LOPH S2 / HL · Studio 1 + Studio A · 9:00 AM – 2:00 PM\n" + "\n".join("• " + d for d in _dates)),
    acts(btn("Move a date", "move_date"), btn("Cancel a date", "cancel_date", "danger")),
]))


# ---- recording with extras: Celebrity Recording (holding rooms + optional vocal booth) ---------------------------------
WC = "Thursday, Oct 15 · 1:00–5:00 PM"
CELEB_ROOMS = [opt("Studio F", d="Recommended · usual for Celebrity Recording · records vocals in the room"),
               opt("Studio C", d="Usual for Celebrity Recording · records vocals in the room")]


def celeb_step2(holding=False, booth=False):
    ex = [add_check("add_holding", "+ Holding room", holding)]
    if holding:
        ex.append(inp("holding", "Holding rooms", {"type": "checkboxes", "action_id": "holding_pick",
                                                   "options": [opt("Likha", d="Free 1:00–5:00 PM"), opt("Katha", d="Free 1:00–5:00 PM")],
                                                   "initial_options": [opt("Likha", d="Free 1:00–5:00 PM")]},
                      hint="For the talent and their team. Salin isn't free then."))
    ex.append(add_check("add_booth", "+ Vocal booth", booth))
    if booth:
        ex.append(booth_picker("Studio F records vocals in the room - add a booth only if the session needs one."))
    return modal("Book a room", [ctx("*Step 2 of 2* · room and details"), sec("🗓️ *" + WC + " · Celebrity Recording*"),
                                 inp("room", "Room", radio("room_radio", CELEB_ROOMS))] + ex +
                 studio_details("CELEB VO", "Harold Orozco", "*CELEB VO / Harold Orozco / HL*"), submit="Book", close="Back", cb="book_step2")


S["70-step1-celeb"] = ("modal", step1("2026-10-15", "13:00", "17:00", "Celebrity Recording"))
S["71-step2-celeb"] = ("modal", celeb_step2())
S["72-step2-celeb-holding"] = ("modal", celeb_step2(holding=True))
S["73-step2-celeb-holding-booth"] = ("modal", celeb_step2(holding=True, booth=True))
S["74-booking-celeb"] = ("modal", booking("Studio F, Likha and Studio A", WC))
S["75-booked-celeb"] = ("modal", booked("CELEB VO / Harold Orozco / HL", "Studio F + Studio A, holding room Likha · " + WC, "Studio F, Studio A and Likha"))
S["76-result-celeb"] = ("message", msg([sec("✅ *Booked.*\n*CELEB VO / Harold Orozco / HL*\nStudio F + Studio A · " + WC + "\nHolding room: Likha"),
                                        ctx("Celebrity Recording · Engineer: you · Advertising"),
                                        acts(btn("Move", "move"), btn("Cancel", "cancel", "danger"))]))
