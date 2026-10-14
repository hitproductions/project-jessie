"""Block Kit screens for the Slack-app pivot (design agreed 13 Oct 2026).

Each screen is real Block Kit JSON: build.py writes every one to docs/design/blockkit/<id>.json (paste into
app.slack.com/block-kit-builder with the matching preview type) and embeds the same JSON in the pivot deck, which
renders it. Sample data only: test projects, fictional clients and people.
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


def mopt(t, v):
    return {"text": md(t), "value": v}


def btn(t, a, v="x", style=None, confirm=None):
    b = {"type": "button", "text": pt(t), "action_id": a, "value": v}
    if style:
        b["style"] = style
    if confirm:
        b["confirm"] = confirm
    return b


def acts(*els, bid=None):
    b = {"type": "actions", "elements": list(els)}
    if bid:
        b["block_id"] = bid
    return b


def overflow(a, *items):
    return {"type": "overflow", "action_id": a, "options": [{"text": pt(t), "value": v} for t, v in items]}


def inp(bid, label, el, optional=False, hint=None, dispatch=False):
    b = {"type": "input", "block_id": bid, "label": pt(label), "element": el}
    if optional:
        b["optional"] = True
    if hint:
        b["hint"] = pt(hint)
    if dispatch:
        b["dispatch_action"] = True
    return b


def radio(a, options, initial=0):
    return {"type": "radio_buttons", "action_id": a, "options": options, "initial_option": options[initial]}


def text_in(a, value=None, multiline=False, ph=None):
    e = {"type": "plain_text_input", "action_id": a}
    if value:
        e["initial_value"] = value
    if multiline:
        e["multiline"] = True
    if ph:
        e["placeholder"] = pt(ph)
    return e


def users(a, ph):
    return {"type": "users_select", "action_id": a, "placeholder": pt(ph)}


def small_check(a, label, checked=False, bid=None):
    o = mopt("_" + label + "_", a)
    e = {"type": "checkboxes", "action_id": a, "options": [o]}
    if checked:
        e["initial_options"] = [o]
    return acts(e, bid=bid)


def modal(title, blocks, submit=None, close="Cancel", cb="view"):
    m = {"type": "modal", "callback_id": cb, "title": pt(title), "close": pt(close), "blocks": blocks}
    if submit:
        m["submit"] = pt(submit)
    return m


def message(blocks):
    return {"blocks": blocks}


MENU_BTNS = (btn("Book a room", "open_book", style="primary"), btn("My bookings", "my_bookings"), btn("Studios", "board"))
MORE = overflow("more", ("Book another", "open_book"), ("Book again, another day", "again"), ("My bookings", "my_bookings"), ("Studios", "board"))

SESSION_GROUPS = [
    {"label": pt("Sessions"), "options": [opt(t) for t in [
        "VO Recording", "Post Mixing", "Music Mixing", "Music Vocal Recording", "Band Recording", "Celebrity Recording",
        "QC", "Post Processing", "Localization Dubbing", "Localization Editing", "Localization Mixing",
        "Localization Atmos Mixing"]]},
    {"label": pt("Not a session"), "options": [opt("Meeting"), opt("Event"), opt("Booth time (M booth)", "booth")]},
]

S = {}

# ---- 1. Starting a request ------------------------------------------------------------------------------------
S["01-menu"] = ("message", message([
    sec("Hi! What would you like to do?"),
    acts(*MENU_BTNS),
    ctx("Or just type it, like _book studio 7 tomorrow 2-4pm_ or _is studio 8 free friday?_"),
]))
S["02-not-understood"] = ("message", message([
    sec("I didn't catch that. Here's what I can do:"),
    acts(*MENU_BTNS),
]))
S["03-typed-request"] = ("message", message([
    sec("🗓️ *Studio 7 · Thursday, Oct 14 · 2:00–4:00 PM*\nVO Recording · QAW1"),
    acts(btn("Book a room", "open_book_prefilled", style="primary")),
    ctx("Opens the form with these filled in."),
]))

# ---- 2. Booking a room -----------------------------------------------------------------------------------------
vo = opt("VO Recording")
S["04-book-step1"] = ("modal", modal("Book a room", [
    ctx("*Step 1 of 2* · when, and what for"),
    inp("date", "Date", {"type": "datepicker", "action_id": "date_pick", "initial_date": "2027-10-14"}),
    inp("start", "Start", {"type": "timepicker", "action_id": "start_pick", "initial_time": "14:00", "timezone": "Asia/Manila"}),
    inp("end", "End", {"type": "timepicker", "action_id": "end_pick", "initial_time": "16:00", "timezone": "Asia/Manila"}),
    small_check("repeat_toggle", "Repeats", bid="repeat_opt"),
    inp("purpose", "What's it for?", {"type": "static_select", "action_id": "purpose_pick", "initial_option": vo,
                                      "option_groups": SESSION_GROUPS},
        hint="Jessie offers the rooms that can do this, the usual ones first."),
], submit="Find rooms", cb="book_step1"))

ROOMS_VO = [opt("Studio 8", d="Recommended · usual for VO Recording"), opt("Studio F", d="Usual for VO Recording"),
            opt("Studio C", d="Usual for VO Recording")]
DATE_LINE = {"type": "section", "text": md("🗓️ *Thursday, Oct 14 · 2:00–4:00 PM · VO Recording*"),
             "accessory": overflow("room_more", ("Show all suitable rooms", "show_all"), ("Pair with a vocal booth", "booth"))}
S["05-book-step2"] = ("modal", modal("Book a room", [
    ctx("*Step 2 of 2* · room and details"),
    DATE_LINE,
    inp("room", "Room", radio("room_radio", ROOMS_VO)),
    ctx("Not free then: Studio 7 (free from 4:00 PM)"),
    dv,
    inp("project", "Project", text_in("project_in", "QAW1")),
    inp("client", "Client", text_in("client_in"), optional=True, hint="Leave empty if there's no client. A new name is fine."),
    inp("engineer", "Engineer", users("engineer_pick", "You"), hint="Set to you. Change it if someone else is engineering."),
    small_check("for_toggle", "Booking for someone else", bid="for_opt"),
    inp("notes", "Notes", text_in("notes_in", multiline=True), optional=True),
    ctx("Calendar title: *QAW1 / <client> / HL* · Booking type: Advertising (from your department)"),
], submit="Book", close="Back", cb="book_step2"))

kind = [opt("Client work", "client"), opt("Internal", "internal"), opt("Personal project", "personal")]
S["06-details-arranger"] = ("modal", modal("Book a room", [
    sec("🗓️ *Friday, Oct 15 · 1:00–5:00 PM · Music Mixing · Studio F*"),
    dv,
    inp("kind", "What kind of booking?", radio("kind_pick", kind)),
    inp("project", "Project", text_in("project_in", "SUMMER JINGLE")),
    inp("client", "Client", text_in("client_in", "Sasa Abella"), optional=True, hint="For client work. Leave empty for internal or personal."),
    inp("engineer", "Engineer", users("engineer_pick", "Who's engineering?"), hint="A music engineer"),
    inp("arranger", "Arranger", users("arranger_pick", "You"), hint="Set to you"),
    ctx("Calendar title: *SUMMER JINGLE / Sasa Abella / <engineer> x <arranger>*"),
], submit="Book", close="Back"))
S["07-details-localization"] = ("modal", modal("Book a room", [
    sec("🗓️ *Thursday, Oct 14 · 9:00 AM – 2:00 PM · Localization Dubbing · Studio 1 + Studio A*"),
    dv,
    inp("code", "Project code", text_in("code_in", "LOPH S2"),
        hint="As in Localization Projects. The client and the title come from it."),
    inp("engineer", "Engineer", users("engineer_pick", "You"), hint="Set to you"),
    ctx("Booking type: Entertainment (always, for Localization) · Calendar title: *<project code> / HL*"),
], submit="Book", close="Back"))
S["08-details-meeting"] = ("modal", modal("Book a room", [
    sec("🗓️ *Thursday, Oct 14 · 3:00–4:00 PM · Meeting*"),
    inp("room", "Room", radio("room_radio", [opt("Likha", d="Recommended"), opt("Salin"), opt("Katha")])),
    dv,
    inp("title", "Meeting title", text_in("title_in", "Q4 planning")),
    inp("notes", "Notes", text_in("notes_in", multiline=True), optional=True),
    ctx("Calendar title: *LIKHA - Q4 planning* · no engineer, no client"),
], submit="Book", close="Back"))

# paired rooms
pair = [opt("Studio 1 + Studio A", "Studio 1|Studio A", "Recommended · control room and its booth"),
        opt("Studio 2 + Studio B", "Studio 2|Studio B", "Control room and its booth"),
        opt("Studio 6 + Studio D", "Studio 6|Studio D", "Control room and its booth")]
S["09-paired-booth"] = ("modal", modal("Book a room", [
    {"type": "section", "text": md("🗓️ *Thursday, Oct 14 · 9:00 AM – 2:00 PM · Localization Dubbing*"),
     "accessory": overflow("room_more", ("Show all suitable rooms", "show_all"), ("Choose the booth myself", "booth"))},
    inp("room", "Room and booth", radio("room_radio", pair)),
    ctx("Pairs come from each room's *Paired with* in Airtable. Only pairs where both rooms are free are listed."),
], submit="Next", close="Back"))
S["10-holding-rooms"] = ("modal", modal("Book a room", [
    DATE_LINE | {"text": md("🗓️ *Thursday, Oct 14 · 1:00–5:00 PM · Celebrity Recording*")},
    inp("room", "Room", radio("room_radio", [opt("Studio F", d="Recommended · usual for Celebrity Recording"),
                                             opt("Studio C", d="Usual for Celebrity Recording")])),
    inp("holding", "Holding rooms", {"type": "checkboxes", "action_id": "holding_pick",
                                     "options": [opt("Likha", d="Free 1:00–5:00 PM"), opt("Katha", d="Free 1:00–5:00 PM")]},
        optional=True, hint="For the talent and their team. One or more, or none."),
    ctx("Salin isn't free then."),
], submit="Next", close="Back"))
S["11-vocal-booth"] = ("modal", modal("Book a room", [
    DATE_LINE,
    inp("room", "Room", radio("room_radio", ROOMS_VO[:2])),
    small_check("booth_toggle", "Pair with a vocal booth", checked=True, bid="booth_opt"),
    inp("booth", "Which booth?", {"type": "static_select", "action_id": "booth_pick", "initial_option": opt("Studio A"),
                                  "options": [opt("Studio A"), opt("Studio D")]},
        hint="Free then. Not the usual pairing for Studio 8 - the engineer patches it."),
], submit="Next", close="Back"))

# after Book
S["12-booking"] = ("modal", modal("Book a room", [
    sec("⏳ *Booking Studio 8…*\nThursday, Oct 14 · 2:00–4:00 PM"),
    ctx("Checking the room and writing it to the calendar. This takes a few seconds."),
], close="Close"))
S["13-booked"] = ("modal", modal("Book a room", [
    sec("✅ *Booked.*\n*QAW1 / Sasa Abella / HL*\nStudio 8 · Thursday, Oct 14 · 2:00–4:00 PM"),
    ctx("The details and the Move / Cancel buttons are in your DM with Jessie."),
], close="Done"))
S["14-problem"] = ("modal", modal("Book a room", [
    sec("⚠️ *Studio 8 was just booked by someone else* for 2:00–3:00 PM. Pick another room below, or go Back to change the time."),
    dv,
    DATE_LINE,
    inp("room", "Room", radio("room_radio", [opt("Studio F", d="Recommended · usual for VO Recording"),
                                             opt("Studio C", d="Usual for VO Recording")])),
    inp("client", "Client", text_in("client_in", "Sasa Abela"), optional=True, hint="Did you mean Sasa Abella? Change it, or keep it as typed."),
    ctx("Everything else you entered is kept."),
], submit="Book", close="Back"))
S["15-result-booked"] = ("message", message([
    sec("✅ *Booked.*\n*QAW1 / Sasa Abella / HL*\nStudio 8 · Thursday, Oct 14 · 2:00–4:00 PM"),
    ctx("VO Recording · Engineer: you · Advertising"),
    ctx("✓ Studio 8 accepted"),
    acts(btn("Move", "move"), btn("Cancel", "cancel", style="danger"), MORE),
]))
S["16-result-declined"] = ("message", message([
    sec("❌ *Studio 8 turned this booking down.* Nothing is booked, and it was taken off the calendar.\n~QAW1 / Sasa Abella / HL · Thu, Oct 14 · 2:00–4:00 PM~"),
    ctx("Studio F and Studio C are free then."),
    acts(btn("Book Studio F instead", "rebook_room", style="primary"), btn("Pick another room or time", "reopen")),
]))

# series
days = [opt(a, b) for a, b in [("Mon", "MO"), ("Tue", "TU"), ("Wed", "WE"), ("Thu", "TH"), ("Fri", "FR"), ("Sat", "SA"), ("Sun", "SU")]]
S["17-series-step1"] = ("modal", modal("Book a room", [
    ctx("*Step 1 of 2* · when, and what for"),
    inp("date", "First date", {"type": "datepicker", "action_id": "date_pick", "initial_date": "2027-10-19"}),
    inp("start", "Start", {"type": "timepicker", "action_id": "start_pick", "initial_time": "10:00", "timezone": "Asia/Manila"}),
    inp("end", "End", {"type": "timepicker", "action_id": "end_pick", "initial_time": "12:00", "timezone": "Asia/Manila"}),
    small_check("repeat_toggle", "Repeats", checked=True, bid="repeat_opt"),
    inp("freq", "How often", radio("freq_pick", [opt("Weekly", "weekly"), opt("Daily", "daily")])),
    inp("days", "On", {"type": "checkboxes", "action_id": "days_pick", "options": days, "initial_options": [days[1]]}),
    inp("ends", "Ends", radio("ends_pick", [opt("After a number of occurrences", "count"), opt("On a date", "until")])),
    inp("count", "Number of occurrences", {"type": "number_input", "action_id": "count_in", "is_decimal_allowed": False,
                                           "min_value": "2", "max_value": "16", "initial_value": "4"},
        hint="Up to 16, within a year."),
    inp("purpose", "What's it for?", {"type": "static_select", "action_id": "purpose_pick", "initial_option": vo,
                                      "option_groups": SESSION_GROUPS}),
], submit="Find rooms", cb="book_step1"))


def date_line(t):
    return {"type": "section", "text": md(t),
            "accessory": overflow("date_menu", ("Skip this date", "skip"), ("Use another room", "room"), ("Change the time", "time"))}


S["18-series-step2"] = ("modal", modal("Book a room", [
    ctx("*Step 2 of 2* · room and details"),
    sec("🗓️ *Every Tuesday · 10:00 AM – 12:00 PM · 4 dates · VO Recording*"),
    inp("room", "Room", radio("room_radio", [opt("Studio 7", d="Usual · free on 3 of 4 dates"),
                                             opt("Studio 8", d="Usual · free on all 4 dates")])),
    dv,
    sec("*Dates*"),
    date_line("✓ Tue, Oct 19"),
    date_line("⚠️ ~Tue, Oct 26~ — Studio 7 is taken. *Studio 8 is free then*, or skip it."),
    acts(btn("Use Studio 8 on Oct 26", "date_swap", "2027-10-26|Studio 8", style="primary")),
    date_line("✓ Tue, Nov 2"),
    date_line("✓ Tue, Nov 9"),
    ctx("Use ⋯ on a date to skip it, change its room or its time."),
    dv,
    inp("project", "Project", text_in("project_in", "QAW5")),
], submit="Book 3 dates", close="Back"))
S["19-series-result"] = ("message", message([
    sec("✅ *Booked 3 of 4 dates.* QAW5 / HL · Studio 7 · 10:00 AM – 12:00 PM\n• Tue, Oct 19\n• Tue, Nov 2\n• Tue, Nov 9"),
    sec("⚠️ *Skipped Tue, Oct 26* — Studio 7 was already taken."),
    acts(btn("Book Oct 26 another way", "series_fix", style="primary"), btn("Move the whole series", "move_series"),
         btn("Cancel the whole series", "cancel_series", style="danger")),
]))

# ---- 4. Finding out ---------------------------------------------------------------------------------------------
def room_line(name, dot, free, taken=None, book=True):
    t = f"{dot} *{name}*\n{free}" + (f"\n_Taken {taken}_" if taken else "")
    b = {"type": "section", "text": md(t)}
    if book:
        b["accessory"] = btn("Book", "board_book", f"{name}|2027-10-14")
    return b


S["20-day-board"] = ("message", message([
    {"type": "section", "text": md("*Studios · Thursday, Oct 14*"),
     "accessory": {"type": "datepicker", "action_id": "board_date", "initial_date": "2027-10-14"}},
    acts({"type": "static_select", "action_id": "board_filter", "initial_option": opt("Studios", "studios"),
          "options": [opt("Studios", "studios"), opt("Booths", "booths"), opt("Conference rooms and Lobby", "common"), opt("All rooms", "all")]},
         btn("Previous day", "board_prev"), btn("Next day", "board_next")),
    dv,
    room_line("Studio 4", "🟢", "Free all day"),
    room_line("Studio 6", "🟡", "Free 8:00 AM – 1:00 PM, 3:00 – 11:00 PM", "6:00 – 8:00 AM, 1:00 – 3:00 PM"),
    room_line("Studio 7", "🟡", "Free 8:00 AM – 2:00 PM, 4:00 – 11:00 PM", "2:00 – 4:00 PM"),
    room_line("Studio 8", "🟡", "Free 8:00 AM – 8:00 PM", "8:00 – 11:00 PM"),
    room_line("Studio F", "🔴", "No free time between 8:00 AM and 11:00 PM", "8:00 AM – 11:00 PM", book=False),
    dv,
    ctx("🟢 nothing booked all day · 🟡 partly free · 🔴 no free time 8 AM – 11 PM · Free times shown 8 AM – 11 PM; bookings at any hour are listed"),
]))
S["21-typed-room-day"] = ("message", message([
    sec("🗓️ *Studio 7 · Friday, Oct 15*\nFree 8:00 AM – 1:00 PM, 3:00 – 11:00 PM\n_Taken 1:00 – 3:00 PM_"),
    acts(btn("Book Studio 7 on Friday", "book_prefill", "Studio 7|2027-10-15", style="primary"), btn("All studios on Friday", "board", "2027-10-15")),
]))
S["22-typed-part-day"] = ("message", message([
    sec("🗓️ *Free tomorrow, Thu Oct 14, 12:00 – 6:00 PM*"),
    {"type": "section", "text": md("*Studio 8* · free the whole afternoon"), "accessory": btn("Book", "book_prefill", "Studio 8")},
    {"type": "section", "text": md("*Studio 6* · free 3:00 – 6:00 PM"), "accessory": btn("Book", "book_prefill", "Studio 6")},
    {"type": "section", "text": md("*Studio C* · free 12:00 – 2:00 PM"), "accessory": btn("Book", "book_prefill", "Studio C")},
    ctx("Studios only. Afternoon = 12:00 – 6:00 PM. Ask about rooms or booths to include those."),
]))

# ---- 5. My bookings, cancel and move ----------------------------------------------------------------------------
def cancel_confirm(title, line):
    return {"title": pt("Cancel this booking?"), "text": md(f"*{title}*\n{line}"), "confirm": pt("Cancel booking"),
            "deny": pt("Keep it"), "style": "danger"}


def booking(title, line, meta, eid, buttons=True):
    out = [sec(f"*{title}*\n{line}"), ctx(meta)]
    if buttons:
        out.append(acts(btn("Move", "move", eid), btn("Cancel", "cancel", eid, style="danger", confirm=cancel_confirm(title, line))))
    return out


S["23-my-bookings"] = ("message", message(
    [sec("*Your bookings · next 7 days*")]
    + booking("QAW1 / Harold Orozco / HL", "Thu, Oct 14 · 2:00–4:00 PM · Studio 8", "VO Recording · Engineer: you", "EV1")
    + [dv] + booking("QAW7 / HL", "Mon, Oct 18 · 1:00–3:00 PM · Studio 8", "Music Mixing · Engineer: you", "EV2")
    + [dv, sec("*You're tagged on*")]
    + booking("BLUE BIRD / MGM", "Fri, Oct 15 · 10:00 AM – 12:00 PM · Studio F", "You're the engineer · booked by Glenn Mariano", "EV3", buttons=False)
    + [dv, acts(btn("See all upcoming", "all_upcoming"))]))
S["24-typed-cancel"] = ("message", message(
    [sec("You have two bookings on Friday, Oct 15:")]
    + booking("QAW9 / HL", "Fri, Oct 15 · 10:00–11:00 AM · Studio 8", "VO Recording", "EV4")
    + booking("QAW9 / HL", "Fri, Oct 15 · 4:00–5:00 PM · Studio 8", "VO Recording", "EV5")))
S["25-typed-move"] = ("message", message([
    sec("*QAW1 / Harold Orozco / HL* · Thu, Oct 14 · 2:00–4:00 PM · Studio 8"),
    acts(btn("Move to 3:00–5:00 PM", "move_quick", "EV1|15:00-17:00", style="primary"), btn("Pick another time", "move", "EV1")),
    ctx("Studio 8 is free 3:00–5:00 PM on Thursday."),
]))
S["26-move-form"] = ("modal", modal("Move booking", [
    sec("*QAW1 / Harold Orozco / HL*\nNow: Thu, Oct 14 · 2:00–4:00 PM · Studio 8"),
    dv,
    inp("date", "Date", {"type": "datepicker", "action_id": "date_pick", "initial_date": "2027-10-14"}),
    inp("start", "Start", {"type": "timepicker", "action_id": "start_pick", "initial_time": "14:00", "timezone": "Asia/Manila"}),
    inp("end", "End", {"type": "timepicker", "action_id": "end_pick", "initial_time": "16:00", "timezone": "Asia/Manila"},
        hint="Set to keep the same length (2 hours)."),
    inp("room", "Room", {"type": "static_select", "action_id": "room_pick", "initial_option": opt("Studio 8 (now)", "keep"),
                         "options": [opt("Studio 8 (now)", "keep"), opt("Studio 7"), opt("Studio F"), opt("Studio C")]}),
    ctx("The new time is checked first. The booking stays where it is until the new one is in place."),
], submit="Move", close="Cancel"))
S["27-after-change"] = ("message", message([
    sec("~QAW9 / HL~\n~Fri, Oct 15 · 10:00–11:00 AM · Studio 8~"),
    ctx("❌ Cancelled by you at 10:42 AM"),
    dv,
    sec("✅ *Moved.* QAW1 / Harold Orozco / HL\nFri, Oct 15 · 2:00–4:00 PM · Studio 8"),
    ctx("Was Thu, Oct 14 · 2:00–4:00 PM"),
    acts(btn("Move", "move"), btn("Cancel", "cancel", style="danger")),
]))

# ---- 6. Approvals and notices -----------------------------------------------------------------------------------
S["28-approval-holder"] = ("message", message([
    sec("🔁 *Priority request for your booking*\n*QAW3 / MGM* · Studio F · Thu, Oct 14 · 2:00–4:00 PM"),
    ctx("Requested by Lea Lardizabal for a Celebrity Recording, which takes priority over VO Recording in Studio F."),
    sec("If you agree, move your session first. Free for you that day:\n• Studio 7 · 2:00–4:00 PM (same time)\n• Studio F · 4:00–6:00 PM (same room, later)"),
    ctx("Sent to you and the booking's engineer; the first answer decides. Answer by 6:00 PM today, or your booking stays."),
    acts(btn("Agree and move my booking", "consent_move", style="primary"),
         btn("Decline", "consent_no", confirm={"title": pt("Decline the request?"), "text": md("Your booking stays where it is."),
                                               "confirm": pt("Decline"), "deny": pt("Go back")})),
]))
S["29-approval-requester"] = ("message", message([
    sec("⏳ *Requested.* Studio F on Thu, Oct 14, 2:00–4:00 PM is held by *QAW3 / MGM*. Jessie asked the booker and the engineer."),
    ctx("You'll hear back here by 6:00 PM today. Nothing is booked until then."),
    acts(btn("I've already cleared it with them", "attest"), btn("Withdraw request", "withdraw", style="danger"),
         btn("Pick another room or time", "reopen")),
]))
S["30-shared-booth"] = ("message", message([
    sec("🎙️ *Someone would like your booth*\n*M4* · Thu, Oct 14 · 3:00–4:00 PM — held for you"),
    ctx("Requested by Glenn Mariano. If you don't answer by 2:00 PM, they get it for that hour."),
    acts(btn("Let them use it", "mbooth_yes", style="primary"), btn("Keep it", "mbooth_no")),
]))
S["31-notices"] = ("message", message([
    sec("🎧 *You're engineering* *QAW1 / Sasa Abella / HL* · Studio 8 · Thu, Oct 14 · 2:00–4:00 PM"),
    acts(btn("Got it", "ack")),
    dv,
    sec("⏰ *Tomorrow:* QAW1 / Sasa Abella / HL · Studio 8 · 2:00–4:00 PM. Still on?"),
    acts(btn("Still on", "keep", style="primary"), btn("Move", "move"), btn("Free up the room", "release", style="danger")),
    dv,
    sec("📅 *Your booths and meeting rooms this week*"),
    {"type": "section", "text": md("*M4* · Tue, Oct 19 · all day _(standing hold)_"), "accessory": overflow("wk", ("Keep", "keep"), ("Free up this week", "free"))},
    {"type": "section", "text": md("*Likha* · Thu, Oct 21 · 3:00–4:00 PM · Q4 planning"), "accessory": overflow("wk", ("Keep", "keep"), ("Free up", "free"))},
    ctx("Every Monday at 9:00 AM."),
]))
