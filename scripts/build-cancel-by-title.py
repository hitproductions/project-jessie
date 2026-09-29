#!/usr/bin/env python3
"""Cancel Booking v20 (cancel without a date) + main v190 (PENDING 56 + series label fix) - 29 Sep.
  scripts/build-cancel-by-title.py <cancel-pull> <cancel-out> <main-pull> <main-out>

PENDING 56  "cancel QANEW" was looked up on 21 Nov (the date of a booking just cancelled) when QANEW was on 18 Nov;
            "cancel qamove from november" on 18 Nov only. Both ended in "nothing found - which date?".
  Cancel    When a card is being prepared (prepare mode, or an unconfirmed call) and the title is not on the date
  v20       given - or no date was given - the new Find By Title node searches upcoming bookings (from now, about 15
            months ahead) for that exact title. One match -> the card, with its real date; several -> the dates are
            listed and the model asks which. Ownership is checked as before, and the yes still cancels only the
            card's booking by its check code. No date at all is no longer MISSING_DATE when there is a title.
  main v190 Prepare Cancel's date is optional: "leave it empty rather than guess".
Series      Model-written series summaries showed "*Engineer:* Engineer: Daryl Reyes" (the description's own label
            copied in). Guard Probe collapses a repeated label on a summary line (Engineer, Arranger, Client ...).
"""
import json, sys, uuid

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

CAL = "c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com"
DAY_OLD = "(String($json.booking_date || '').match(/\\d{4}-\\d{2}-\\d{2}/) || [$json.booking_date])[0]"
DAY_NEW = "(String($('When Executed by Another Workflow').first().json.booking_date || '').match(/\\d{4}-\\d{2}-\\d{2}/) || [DateTime.now().setZone('Asia/Manila').toISODate()])[0]"
W = "$('When Executed by Another Workflow').first().json"
NEED = f"(String(({W}).title || '').trim() && (String(({W}).mode || '').toLowerCase() === 'prepare' || String(({W}).confirmed).toLowerCase() !== 'true'))"
FIND_URL = ("=https://www.googleapis.com/calendar/v3/calendars/{{ encodeURIComponent('" + CAL + "') }}/events"
            "?q={{ encodeURIComponent(String((" + W + ").title || '').trim() || 'none') }}"
            "&timeMin={{ encodeURIComponent(DateTime.now().toISO()) }}"
            "&timeMax={{ encodeURIComponent(DateTime.now().plus(" + NEED + " ? { days: 450 } : { minutes: 1 }).toISO()) }}"
            "&singleEvents=true&maxResults=250")

CO_DATE_OLD = "if (!String(REQ.booking_date || '').trim()) {"
CO_DATE_NEW = "if (!String(REQ.booking_date || '').trim() && !(prepareMode && wantedTitle)) {   // v20: a title alone is searched for"
CO_WIDE_ANCHOR = "if (!ev && wantedTitle) {\n  const want = norm(wantedTitle);"
CO_WIDE = r"""// --- v20 (PENDING 56): no date, or the title is not on the date given -> look for it among upcoming bookings ---------
// "cancel QANEW" was looked up on the date of a booking just cancelled and found nothing. When a card is being prepared,
// an exact title missing from that day is searched for from now on (Find By Title). One match is the booking - the card
// shows its real date, and the yes still cancels only that card's booking. Several are listed so the model asks which.
let __noDate = !String(REQ.booking_date || '').trim();
if (!ev && prepareMode && wantedTitle && !wantCode && !items.some(e => norm(e.summary) === norm(wantedTitle))) {
  let _W = {}; try { _W = $('Find By Title').first().json || {}; } catch (e) {}
  const _wide = Array.isArray(_W.items) && !_W.nextPageToken ? _W.items.filter(e => e.status !== 'cancelled') : [];
  const _wh = _wide.filter(e => norm(e.summary) === norm(wantedTitle));
  const _d = e => { const s = (e.start && (e.start.dateTime || e.start.date)) || ''; const D = /^\d{4}-\d{2}-\d{2}$/.test(s) ? new Date(s + 'T00:00:00+08:00') : new Date(s);
    return D.toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }) + ' ' + when(e); };
  if (_wh.length === 1) { ev = _wh[0]; how = 'title, upcoming'; }
  else if (_wh.length > 1) {
    return [{ json: { verdict:'REJECTED', reason:'AMBIGUOUS_TITLE', matches: _wh.map(e => ({ id: e.id, start: (e.start && (e.start.dateTime || e.start.date)) || '' })),
      human: 'Nothing was cancelled - there is more than one upcoming booking titled "' + wantedTitle + '":\n'
        + _wh.map(e => '- ' + _d(e)).join('\n') + '\nAsk which date they mean, then prepare the cancel again with that date.' } }];
  }
  else if (__noDate) {
    return [{ json: { verdict:'REJECTED', reason:'NOT_ON_CALENDAR',
      human: 'Nothing was cancelled - no upcoming booking is titled exactly "' + wantedTitle + '". Ask for the date of the booking, or check the title with Find Booking.' } }];
  }
}
"""

GP_ANCHOR = "// 29 Sep: the confirmation goes out as one line"
GP_LABEL = r"""// --- v190: "*Engineer:* Engineer: Daryl Reyes" - a label copied in twice (model-written series summaries) --------------
if (!_prepared) text = text.replace(/^([ \t]*[-•]?[ \t]*\*?(Engineer|Arranger|Client|Project|Rooms?|Department|Booked by|Session Type|Booking Type)\*?:\*?[ \t]*)\2[ \t]*:[ \t]*/gim, '$1');

"""
PC_DATE_OLD = "$fromAI('booking_date', 'The date the booking falls on, as yyyy-MM-dd, from the Find Booking result.', 'string')"
PC_DATE_NEW = ("$fromAI('booking_date', 'The date the booking falls on, as yyyy-MM-dd, if the requester named it or Find Booking showed it. "
               "Leave it empty if you do not know it - the booking is then found by its title among upcoming bookings. Never guess a date.', 'string', '')")
PC_DESC_OLD = "Give it the booking title exactly as Find Booking returned it and the date it falls on, and the event id if Find Booking gave one."
PC_DESC_NEW = ("Give it the booking title exactly as the requester or Find Booking gave it, the date it falls on if you know it "
               "(leave the date empty rather than guess - it then finds the booking by its title), and the event id if Find Booking gave one.")

def cancel_fix(w):
    w["name"] = "Jessie — Cancel Booking — v20 (cancel without a date)"
    ld = node(w, "List Day Events")
    u = ld["parameters"]["url"]
    if u.count(DAY_OLD) != 2: raise SystemExit("day url: expected 2, found " + str(u.count(DAY_OLD)))
    ld["parameters"]["url"] = u.replace(DAY_OLD, DAY_NEW)
    fb = json.loads(json.dumps(ld)); x, y = ld["position"]
    fb.update(id=str(uuid.uuid4()), name="Find By Title", position=[x - 176, y + 160])
    fb["parameters"]["url"] = FIND_URL
    w["nodes"].append(fb)
    # Find By Title runs first, so Check Ownership's input is still the day's events (List Day Events), as before.
    C = w["connections"]
    if [t["node"] for t in C["When Executed by Another Workflow"]["main"][0]] != ["List Day Events"]: raise SystemExit("wiring changed")
    C["When Executed by Another Workflow"] = {"main": [[{"node": "Find By Title", "type": "main", "index": 0}]]}
    C["Find By Title"] = {"main": [[{"node": "List Day Events", "type": "main", "index": 0}]]}
    co = node(w, "Check Ownership")["parameters"]
    s = sub1(co["jsCode"], CO_DATE_OLD, CO_DATE_NEW, "date")
    s = sub1(s, CO_WIDE_ANCHOR, CO_WIDE + CO_WIDE_ANCHOR, "wide")
    co["jsCode"] = s
    return w

def main_fix(w):
    w["name"] = "Project Jessie — v190 (PENDING 56 + series label fix)"
    g = node(w, "Guard Probe")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GP_ANCHOR, GP_LABEL + GP_ANCHOR, "guard")
    pc = node(w, "Prepare Cancel")["parameters"]
    v = pc["workflowInputs"]["value"]; v["booking_date"] = sub1(v["booking_date"], PC_DATE_OLD, PC_DATE_NEW, "pc date")
    pc["description"] = sub1(pc["description"], PC_DESC_OLD, PC_DESC_NEW, "pc desc")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(cancel_fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    json.dump(main_fix(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1], a[3])
