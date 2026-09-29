#!/usr/bin/env python3
"""Find Booking v7 (find by title) + main v191 (find by title) - live Slack test 29 Sep 17:45 PHT (exec 17079).
  scripts/build-find-by-title.py <find-pull> <find-out> <main-pull> <main-out>

"cancel QANODATE" (booked for 7 Oct): the model called Find Booking with today's date, found nothing and asked "Which
date is the booking on?". Cancel Booking v20 searches by title, but the model never reached it - it looks the
booking up first, and Find Booking only took a date.
  Find v7   optional `title`. Find By Title (new, runs first) searches upcoming bookings (now to ~15 months ahead)
            when a title is given. Shape Results still returns the day's bookings; when the title matches nothing
            that day (or no date was given) it adds `upcoming`: the bookings whose title contains it, each with its
            date, time, room and who booked it. Read-only, so a partial name ("QANODATE") is fine - the cancel card
            still needs the exact title and a yes. With no date the day read is today's.
  main v191 Find Booking takes the title the requester used; its date is optional ("never guess a date").
"""
import json, sys, uuid

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

CAL = "c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com"
W = "$('When Executed by Another Workflow').first().json"
DAY_OLD = "(String($json.booking_date || '').match(/\\d{4}-\\d{2}-\\d{2}/) || [$json.booking_date])[0]"
DAY_NEW = "(String(" + W + ".booking_date || '').match(/\\d{4}-\\d{2}-\\d{2}/) || [DateTime.now().setZone('Asia/Manila').toISODate()])[0]"
TT = "String((" + W + ").title || '').trim()"
FIND_URL = ("=https://www.googleapis.com/calendar/v3/calendars/{{ encodeURIComponent('" + CAL + "') }}/events"
            "?q={{ encodeURIComponent(" + TT + " || 'none') }}"
            "&timeMin={{ encodeURIComponent(DateTime.now().toISO()) }}"
            "&timeMax={{ encodeURIComponent(DateTime.now().plus(" + TT + " ? { days: 450 } : { minutes: 1 }).toISO()) }}"
            "&singleEvents=true&orderBy=startTime&maxResults=250")

SR_DATE_OLD = """if (!date) {
  return [{ json: { status: 'MISSING_DATE', bookings: [],"""
SR_DATE_NEW = """const title = String(REQ.title || '').trim();   // v7: the booking's name, as the requester gave it
if (!date && !title) {
  return [{ json: { status: 'MISSING_DATE', bookings: [],"""
SR_RET_OLD = """return [{ json: { status: 'OK', date: date, count: bookings.length, bookings: bookings,"""
SR_RET_NEW = r"""// --- v7: the booking by name, among upcoming bookings --------------------------------------------------------------
// "cancel QANODATE" was looked up on today's date (the model's guess) and found nothing. When a title is given and
// nothing that day carries it - or no date was given - the upcoming bookings whose title contains it are returned
// with their dates, so the model can use the real one.
const _n = s => String(s || '').toLowerCase().replace(/\s+/g, ' ').trim();
const _has = t => !!title && _n(t).indexOf(_n(title)) !== -1;
let upcoming = [];
if (title && !bookings.some(b => _has(b.title))) {
  let _W = {}; try { _W = $('Find By Title').first().json || {}; } catch (e) {}
  const _wi = Array.isArray(_W.items) && !_W.nextPageToken ? _W.items : [];
  const _day = iso => { const d = /^\d{4}-\d{2}-\d{2}$/.test(iso) ? new Date(iso + 'T12:00:00+08:00') : new Date(iso);
    return d.toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }); };
  for (const ev of _wi) {
    if (!ev || ev.status === 'cancelled' || !_has(ev.summary)) continue;
    const desc = String(ev.description || ''), by = desc.match(/Booked by:\s*([^|]+)/), eng = desc.match(/Engineer:\s*([^|]+)/);
    const s = (ev.start || {}).dateTime || (ev.start || {}).date || '', e = (ev.end || {}).dateTime || (ev.end || {}).date || '';
    const iso = /^\d{4}-\d{2}-\d{2}$/.test(s) ? s : new Date(s).toLocaleDateString('en-CA', { timeZone: 'Asia/Manila' });
    upcoming.push({ id: ev.id, title: ev.summary, booking_date: iso, date: _day(s),
      time: (!(ev.start || {}).dateTime || isWholeDay(s, e)) ? 'all day' : hhmm(s) + ' - ' + hhmm(e),
      room: roomOf(ev) || 'not identifiable', booked_by: by ? by[1].trim() : 'not recorded - made outside Jessie', engineer: eng ? eng[1].trim() : '' });
    if (upcoming.length >= 10) break;
  }
  {   // a name was asked about and nothing that day carries it: always say what the search found
    return [{ json: { status: 'OK', date: date, count: bookings.length, bookings: date ? bookings : [], upcoming,
      human: upcoming.length
        ? (date ? 'Nothing on ' + date + ' is titled "' + title + '". ' : '') + 'Upcoming bookings named "' + title + '":\n'
          + upcoming.map(u => '- ' + u.title + ' on ' + u.date + ', ' + u.time + ', ' + u.room + ' (booked by ' + u.booked_by + ')').join('\n')
          + '\nIf one of these is the booking, use its title and booking_date exactly as given. If several could be, ask which date.'
        : (date ? 'Nothing on ' + date + ' is titled "' + title + '", and n' : 'N') + 'o upcoming booking is named "' + title + '". Ask the requester which date the booking is on, or to check the name.' } }];
  }
}

return [{ json: { status: 'OK', date: date, count: bookings.length, bookings: bookings,"""

MF_DESC_OLD = "Use this ONLY once the requester has said which date the booking is on; if you do not know the date, ask."
MF_DESC_NEW = ("Pass the date if the requester said it. If they named the booking (a title or project name) but not the date, "
               "leave the date empty and pass the name as title: it then finds their upcoming bookings with that name, with dates. Never guess a date.")
MF_DATE_OLD = "$fromAI('booking_date', 'The single calendar date of the booking, as YYYY-MM-DD, for example 2027-09-09. The date only - never a time, never a range. If the requester has not said which date, ask them rather than guessing.', 'string')"
MF_DATE_NEW = ("$fromAI('booking_date', 'The single calendar date of the booking, as YYYY-MM-DD, for example 2027-09-09, if the requester said it. "
               "The date only - never a time, never a range. Leave it empty if they did not say - never guess a date.', 'string', '')")
MF_TITLE = ("={{ $fromAI('title', 'The name of the booking the requester is asking about - a title or project name such as QANODATE, "
            "exactly as they typed it. Leave empty if they did not name one.', 'string', '') }}")

def find_fix(w):
    w["name"] = "Jessie — Find Booking — v7 (find by title)"
    t = node(w, "When Executed by Another Workflow")["parameters"]["workflowInputs"]["values"]
    if not any(v.get("name") == "title" for v in t): t.append({"name": "title"})
    ld = node(w, "List Day Events"); u = ld["parameters"]["url"]
    if u.count(DAY_OLD) != 2: raise SystemExit("day url: expected 2, found " + str(u.count(DAY_OLD)))
    ld["parameters"]["url"] = u.replace(DAY_OLD, DAY_NEW)
    fb = json.loads(json.dumps(ld)); x, y = ld["position"]
    fb.update(id=str(uuid.uuid4()), name="Find By Title", position=[x - 176, y + 160]); fb["parameters"]["url"] = FIND_URL
    fb["onError"] = "continueRegularOutput"; fb["alwaysOutputData"] = True
    w["nodes"].append(fb)
    C = w["connections"]
    if [q["node"] for q in C["When Executed by Another Workflow"]["main"][0]] != ["List Day Events"]: raise SystemExit("wiring changed")
    C["When Executed by Another Workflow"] = {"main": [[{"node": "Find By Title", "type": "main", "index": 0}]]}
    C["Find By Title"] = {"main": [[{"node": "List Day Events", "type": "main", "index": 0}]]}
    sr = node(w, "Shape Results")["parameters"]
    s = sub1(sr["jsCode"], SR_DATE_OLD, SR_DATE_NEW, "date")
    sr["jsCode"] = sub1(s, SR_RET_OLD, SR_RET_NEW, "ret")
    return w

def main_fix(w):
    w["name"] = "Project Jessie — v191 (find by title)"
    fbn = node(w, "Find Booking")["parameters"]
    fbn["description"] = sub1(fbn["description"], MF_DESC_OLD, MF_DESC_NEW, "desc")
    wi = fbn["workflowInputs"]
    wi["value"]["booking_date"] = sub1(wi["value"]["booking_date"], MF_DATE_OLD, MF_DATE_NEW, "date")
    wi["value"]["title"] = MF_TITLE
    if not any(sc.get("id") == "title" for sc in wi["schema"]):
        sc = json.loads(json.dumps(wi["schema"][0])); sc.update(id="title", displayName="title"); wi["schema"].append(sc)
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(find_fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    json.dump(main_fix(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1], a[3])
