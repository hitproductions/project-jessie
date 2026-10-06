#!/usr/bin/env python3
"""Cancel Booking v22 + Find Booking v8 + main v221 (name search includes past) - decided 6 Oct (Howard): a booking named
without a date ("cancel RUNWAY") is looked for in the last 60 days as well as ahead, e.g. to delete one made the previous
week. When the name is on more than one booking - one coming up and one already passed - that is always said. Mostly it
will be used for upcoming bookings, so those are listed first.
  Before: Find By Title (Cancel v20, Find v7) searched from now on only; a past booking named without a date was "no
  upcoming booking is titled ..." and Jessie asked for the date.
  - Cancel Booking v22: Find By Title from 60 days back. One match is the card (a past one says "Heads up: this booking has
    already passed."). Several: one question, coming-up bookings first, past ones marked "(already passed)":
      There are two bookings named "RUNWAY" - one coming up and one that has already passed:
      - Thursday, October 15, 2026, 3:00 PM – 5:00 PM, Studio 8
      - Thursday, October 1, 2026, 3:00 PM – 5:00 PM, Studio 8 (already passed)
      Which one should I cancel?
    Return Rejection now passes `ask` and `matches` on (it dropped every field but reason / human).
  - Find Booking v8: the same window, list order and labels; `matches` (all, with `passed`) beside `upcoming` (coming up
    only, as before); `ask` when two or more match.
  - main v221 Prepared Cancel: the yes still carries out a card with the past note or "_Also named_" lines.
  - main v221 Guard Probe: when a name search this turn found two or more bookings, the reply names every one of them or is
    replaced by that question; when a cancel card was prepared after it, the card lists the others ("_Also named ..._").
    Prepare Cancel / Find Booking tool descriptions say "the last 60 days and coming up".
  scripts/build-name-search-past.py <cancel-v21> <cancel-out> <find-v7> <find-out> <main-v220> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# the question, shared by Cancel and Find (each node carries its own copy)
DUPQ = r"""// v22 / v8 (decided 6 Oct): the same name on several bookings is asked in one fixed question - coming up first, then
// any that have already passed, each marked, and a line that says when both kinds are there.
const __numW = k => (['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'])[k] || String(k);
const __dupQ = (title, list, verb) => {
  const up = list.filter(x => !x.passed), past = list.filter(x => x.passed);
  const head = up.length && past.length
    ? 'There are ' + __numW(list.length) + ' bookings named "' + title + '" - ' + __numW(up.length) + ' coming up and ' + __numW(past.length) + ' that ' + (past.length === 1 ? 'has' : 'have') + ' already passed:'
    : 'There are ' + __numW(list.length) + ' bookings named "' + title + '"' + (past.length ? ', all already passed' : '') + ':';
  return head + '\n' + up.concat(past).map(x => '- ' + x.label + (x.passed ? ' (already passed)' : '')).join('\n') + '\nWhich one ' + (verb ? 'should I ' + verb : 'do you mean') + '?';
};
const __evMs = v => { const s = String(v || ''); return /^\d{4}-\d{2}-\d{2}$/.test(s) ? Date.parse(s + 'T00:00:00+08:00') : Date.parse(s); };
const __order = (list, startOf, endOf) => {   // coming up (soonest first), then past (most recent first)
  const now = Date.now(), up = [], past = [];
  for (const x of list) (__evMs(endOf(x)) < now ? past : up).push(x);
  up.sort((a, b) => __evMs(startOf(a)) - __evMs(startOf(b))); past.sort((a, b) => __evMs(startOf(b)) - __evMs(startOf(a)));
  return up.map(x => ({ x, passed: false })).concat(past.map(x => ({ x, passed: true })));
};
"""

# ---------------------------------------------------------------- Cancel Booking
C_URL_OLD = "&timeMin={{ encodeURIComponent(DateTime.now().toISO()) }}"
C_URL_NEW = "&timeMin={{ encodeURIComponent(DateTime.now().minus({ days: 60 }).toISO()) }}"

C_BLOCK_OLD_START = "  if (_wh.length === 1) { ev = _wh[0]; how = 'title, upcoming'; }"
C_BLOCK_OLD_END = """      human: 'Nothing was cancelled - no upcoming booking is titled exactly "' + wantedTitle + '". Ask for the date of the booking, or check the title with Find Booking.' } }];
  }
"""
C_BLOCK_NEW = r"""  // v22 (decided 6 Oct): the last 60 days count too; several are asked in one fixed question, coming up first
  const _ord = __order(_wh, e => (e.start && (e.start.dateTime || e.start.date)) || '', e => (e.end && (e.end.dateTime || e.end.date)) || '');
  const _lab = e => { const s = (e.start && (e.start.dateTime || e.start.date)) || '', en = (e.end && (e.end.dateTime || e.end.date)) || '';
    const D = /^\d{4}-\d{2}-\d{2}$/.test(s) ? new Date(s + 'T00:00:00+08:00') : new Date(s);
    const t = x => new Date(x).toLocaleTimeString('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' });
    return D.toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
      + ', ' + (e.start && e.start.dateTime ? t(s) + ' – ' + t(en) : 'all day') + (cxRoom(e) ? ', ' + cxRoom(e) : ''); };
  if (_ord.length === 1) { ev = _ord[0].x; how = _ord[0].passed ? 'title, past' : 'title, upcoming'; }
  else if (_ord.length > 1) {
    const _q = __dupQ(wantedTitle, _ord.map(o => ({ label: _lab(o.x), passed: o.passed })), 'cancel');
    return [{ json: { verdict:'REJECTED', reason:'AMBIGUOUS_TITLE', ask: _q,
      matches: _ord.map(o => ({ id: o.x.id, start: (o.x.start && (o.x.start.dateTime || o.x.start.date)) || '', label: _lab(o.x), date: _lab(o.x).split(', ').slice(0, 3).join(', '), passed: o.passed })),
      human: 'Nothing was cancelled. Ask exactly this, in one message: "' + _q.replace(/"/g, '\\"') + '" Then prepare the cancel again with the date of the one they pick - do not search again.' } }];
  }
  else if (__noDate) {
    return [{ json: { verdict:'REJECTED', reason:'NOT_ON_CALENDAR',
      human: 'Nothing was cancelled - no booking in the last 60 days or coming up is titled exactly "' + wantedTitle + '". Ask for the date of the booking, or check the title with Find Booking.' } }];
  }
"""
C_CARD_OLD = """    .concat(['', 'Confirm to cancel.']).join('\\n');   // Guard Probe sends it with the one-line confirmation"""
C_CARD_NEW = """    .concat(Date.parse(en || s) < Date.now() ? ['Heads up: this booking has already passed.'] : [])   // v22: past bookings can be cancelled
    .concat(['', 'Confirm to cancel.']).join('\\n');   // Guard Probe sends it with the one-line confirmation"""
C_REJ_OLD = """return [{ json: { status:'REJECTED', reason: v.reason || 'FAILED',
  human: v.human || 'Nothing was cancelled and the reason is unclear. Tell the requester it did not go through.' } }];"""
C_REJ_NEW = """return [{ json: Object.assign({ status:'REJECTED', reason: v.reason || 'FAILED',
  human: v.human || 'Nothing was cancelled and the reason is unclear. Tell the requester it did not go through.' },
  v.ask ? { ask: v.ask } : {}, Array.isArray(v.matches) ? { matches: v.matches } : {}) }];   // v22: the question and matches reach main"""
C_ANCHOR = "// --- v20 (PENDING 56): no date, or the title is not on the date given -> look for it among upcoming bookings ---------"

def cancel(w):
    w["name"] = "Jessie — Cancel Booking — v22 (name search includes past)"
    fb = node(w, "Find By Title")["parameters"]; fb["url"] = sub1(fb["url"], C_URL_OLD, C_URL_NEW, "cancel url")
    co = node(w, "Check Ownership")["parameters"]; s = co["jsCode"]
    i = s.index(C_BLOCK_OLD_START); j = s.index(C_BLOCK_OLD_END, i) + len(C_BLOCK_OLD_END)
    if s.count(C_BLOCK_OLD_START) != 1: raise SystemExit("cancel block start")
    s = s[:i] + C_BLOCK_NEW + s[j:]
    s = sub1(s, C_ANCHOR, DUPQ + C_ANCHOR, "cancel dupq")
    s = sub1(s, C_CARD_OLD, C_CARD_NEW, "cancel card")
    co["jsCode"] = s
    rr = node(w, "Return Rejection")["parameters"]; rr["jsCode"] = sub1(rr["jsCode"], C_REJ_OLD, C_REJ_NEW, "cancel rejection")
    return w

# ---------------------------------------------------------------- Find Booking
F_URL_OLD = "&timeMin={{ encodeURIComponent(DateTime.now().toISO()) }}"
F_URL_NEW = "&timeMin={{ encodeURIComponent((String(($('When Executed by Another Workflow').first().json).title || '').trim() ? DateTime.now().minus({ days: 60 }) : DateTime.now()).toISO()) }}"
F_LOOP_OLD = """    upcoming.push({ id: ev.id, title: ev.summary, booking_date: iso, date: _day(s),
      time: (!(ev.start || {}).dateTime || isWholeDay(s, e)) ? 'all day' : hhmm(s) + ' - ' + hhmm(e),
      room: roomOf(ev) || 'not identifiable', booked_by: by ? by[1].trim() : 'not recorded - made outside Jessie', engineer: eng ? eng[1].trim() : '' });
    if (upcoming.length >= 10) break;
  }"""
F_LOOP_NEW = """    upcoming.push({ id: ev.id, title: ev.summary, booking_date: iso, date: _day(s),
      time: (!(ev.start || {}).dateTime || isWholeDay(s, e)) ? 'all day' : hhmm(s) + ' - ' + hhmm(e),
      room: roomOf(ev) || 'not identifiable', booked_by: by ? by[1].trim() : 'not recorded - made outside Jessie', engineer: eng ? eng[1].trim() : '', __s: s, __e: e });
  }
  // v8 (decided 6 Oct): the last 60 days count too - coming up first (soonest), then past (most recent), ten at most
  matches = __order(upcoming, u => u.__s, u => u.__e).slice(0, 10).map(o => { const u = Object.assign({}, o.x, { passed: o.passed }); delete u.__s; delete u.__e;
    u.label = u.date + ', ' + (u.time === 'all day' ? 'all day' : u.time.replace(' - ', ' – ')) + (u.room && u.room !== 'not identifiable' ? ', ' + u.room : ''); return u; });
  upcoming = matches.filter(u => !u.passed);
  // one title for all -> named in the question's first line; different titles -> each line starts with its title
  const _same = new Set(matches.map(u => u.title)).size === 1;
  const _ask = matches.length >= 2 ? __dupQ(_same ? matches[0].title : title, matches.map(u => ({ label: (_same ? '' : u.title + ', ') + u.label, passed: u.passed })), '') : '';"""
F_RET_OLD = """    return [{ json: { status: 'OK', date: date, count: bookings.length, bookings: date ? bookings : [], upcoming,
      human: upcoming.length
        ? (date ? 'Nothing on ' + date + ' is titled "' + title + '". ' : '') + 'Upcoming bookings named "' + title + '":\\n'
          + upcoming.map(u => '- ' + u.title + ' on ' + u.date + ', ' + u.time + ', ' + u.room + ' (booked by ' + u.booked_by + ')').join('\\n')
          + '\\nIf one of these is the booking, use its title and booking_date exactly as given. If several could be, ask which date.'
        : (date ? 'Nothing on ' + date + ' is titled "' + title + '", and n' : 'N') + 'o upcoming booking is named "' + title + '". Ask the requester which date the booking is on, or to check the name.' } }];"""
F_RET_NEW = """    return [{ json: Object.assign({ status: 'OK', date: date, count: bookings.length, bookings: date ? bookings : [], upcoming, matches,
      human: matches.length
        ? (date ? 'Nothing on ' + date + ' is titled "' + title + '". ' : '') + 'Bookings named "' + title + '" (coming up first, then any from the last 60 days that have already passed):\\n'
          + matches.map(u => '- ' + u.title + ' on ' + u.date + ', ' + u.time + ', ' + u.room + ' (booked by ' + u.booked_by + ')' + (u.passed ? ' - already passed' : '')).join('\\n')
          + '\\nIf one of these is the booking, use its title and booking_date exactly as given.'
          + (_ask ? ' More than one matches. Ask exactly this, in one message: "' + _ask.replace(/"/g, '\\\\"') + '" When they pick one, use its booking_date - do not search again.' : '')
        : (date ? 'Nothing on ' + date + ' is titled "' + title + '", and n' : 'N') + 'o booking in the last 60 days or coming up is named "' + title + '". Ask the requester which date the booking is on, or to check the name.' },
      _ask ? { ask: _ask } : {}) }];"""
F_LET_OLD = "let upcoming = [];\n"
F_LET_NEW = "let upcoming = [], matches = [];\n"
F_ANCHOR = "// --- v7: the booking by name, among upcoming bookings --------------------------------------------------------------"

def find(w):
    w["name"] = "Jessie — Find Booking — v8 (name search includes past)"
    fb = node(w, "Find By Title")["parameters"]; fb["url"] = sub1(fb["url"], F_URL_OLD, F_URL_NEW, "find url")
    sr = node(w, "Shape Results")["parameters"]; s = sr["jsCode"]
    s = sub1(s, F_ANCHOR, DUPQ + F_ANCHOR, "find dupq"); s = sub1(s, F_LET_OLD, F_LET_NEW, "find let")
    s = sub1(s, F_LOOP_OLD, F_LOOP_NEW, "find loop"); s = sub1(s, F_RET_OLD, F_RET_NEW, "find return")
    sr["jsCode"] = s
    return w

# ---------------------------------------------------------------- main
GP_ANCHOR = "// --- v203: a move card whose new time and room are where the booking already is --------------------------------------"
GP_BLOCK = r"""// --- v221 (decided 6 Oct): a name on several bookings - one coming up, one already passed - is always said -------------
// Find Booking and Prepare Cancel search the last 60 days as well as ahead. When the latest name search this turn found
// two or more bookings: a cancel card prepared after it lists the others; otherwise the reply names every one of them, or
// it is replaced by the tool's own question (coming up first, past ones marked "(already passed)").
try {
  const _sD = (($input.first().json || {}).intermediateSteps) || [];
  let _dI = -1, _cI = -1, _dO = null;
  for (let i = 0; i < _sD.length; i++) {
    const _tD = String(((_sD[i] || {}).action || {}).tool || '').replace(/[_\s]+/g, ' ').toLowerCase();
    if (!/^(find booking|prepare cancel|cancel booking)$/.test(_tD)) continue;
    let _oD = null; try { _oD = [].concat(JSON.parse(String((_sD[i] || {}).observation || '')))[0]; } catch (e) {}
    if (!_oD) continue;
    if (_oD.status === 'PREPARED' && _oD.card_text) _cI = i;
    else if (Array.isArray(_oD.matches) && _oD.matches.length >= 2) { _dI = i; _dO = _oD; }
  }
  if (_dO) {
    const _md = m => String(m.date || '').replace(/^[A-Za-z]+,\s*/, '').replace(/,\s*\d{4}.*$/, '');   // "October 15"
    const _tt = String(((_dO.matches[0] || {}).title) || '').trim() || ((String(_dO.ask || '').match(/named "([^"]+)"/) || [])[1] || '');
    if (_cI > _dI && _prepared) {
      const _cd = ((text.match(/^\*Date:\*\s*([^\n]+)$/m) || [])[1] || '').trim();
      const _ct = ((text.match(/^\*Time:\*\s*([^\n]+)$/m) || [])[1] || '').trim();
      const _others = _dO.matches.filter(m => !(_cd && String(m.label || '').indexOf(_cd) === 0 && (!_ct || String(m.label || '').indexOf(_ct) !== -1)));
      const _lines = _others.map(m => '_Also named "' + (String(m.title || '').trim() || _tt) + '": ' + m.label + (m.passed ? ' (already passed)' : '') + '._');
      if (_lines.length && _lines.length < _dO.matches.length)
        text = text.replace(/\n*((?:Confirm to cancel\.|Cancel it\? Reply yes or no\.)\s*)$/i, '\n' + _lines.join('\n') + '\n\n$1');
    } else if (_dI > _cI && _dO.ask && !_dO.matches.every(m => _md(m) && new RegExp('\\b' + _md(m) + '\\b').test(text))) {   // "October 1" is not in "October 15"
      text = String(_dO.ask); _prepared = false;
    }
  }
} catch (e) {}

"""
PC_OLD = "the booking is then found by its title among upcoming bookings."
PC_NEW = "the booking is then found by its title among the last 60 days and coming up."
FB_OLD = "it then finds their upcoming bookings with that name, with dates."
FB_NEW = "it then finds bookings with that name from the last 60 days and coming up, with dates."

PCN_OLD = """|| /^_Next: .+_$/.test(l)"""
PCN_NEW = """|| /^_Next: .+_$/.test(l) || /^_Also named .+_$/.test(l) || /^Heads up: this booking has already passed\\.$/.test(l)   // v221: Cancel Booking v22's past note and the other bookings with that name"""
def main(w):
    w["name"] = "Project Jessie — v221 (name search includes past)"
    pc = node(w, "Prepared Cancel")["parameters"]; pc["jsCode"] = sub1(pc["jsCode"], PCN_OLD, PCN_NEW, "prepared cancel shape")
    gp = node(w, "Guard Probe")["parameters"]; gp["jsCode"] = sub1(gp["jsCode"], GP_ANCHOR, GP_BLOCK + GP_ANCHOR, "gp dup")
    for n, old, new in [("Prepare Cancel", PC_OLD, PC_NEW), ("Find Booking", FB_OLD, FB_NEW)]:
        nd = node(w, n); s = json.dumps(nd["parameters"], ensure_ascii=False); nd["parameters"] = json.loads(sub1(s, old, new, n))
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    for f, i, o in [(cancel, 0, 1), (find, 2, 3), (main, 4, 5)]:
        json.dump(f(json.load(open(a[i]))), open(a[o], "w"), indent=2, ensure_ascii=False); print("wrote", a[o])
