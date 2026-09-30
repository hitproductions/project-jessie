#!/usr/bin/env python3
"""main v195 (date carry fix) - live QA 30 Sep 13:18 PHT.
  scripts/build-date-carry.py <main-live> <main-out>

"book qaorange studio 8 tomorrow 2pm to 4pm, vo recording, engineer drey" -> Jessie asked about the client and booking
type (13:18:15) -> "no client" three seconds later (13:18:18) -> "What is the date for this booking?".

Gate Context remembers the date under discussion in workflow static data, and n8n saves static data only when an
execution FINISHES. Since v193 a turn keeps running after the reply is sent (Turn Log Row -> Log Turn, a sheet write),
so an answer typed within a few seconds starts a new execution that loads the store before the previous one saved it:
no carried date, datesUnderDiscussion empty, Prepare Booking -> MISSING_DATE. Offline, with the store saved between
turns, the same two turns carry 1 Oct correctly.

Now, when this message names no date and nothing is carried, Gate Context reads the requester's own earlier messages
(newest first, today in Manila only, stopping at a "reset") and takes the first single date one of them names - the
same rules as the resolver above (written dates, next-week days, next / this / bare weekdays, tomorrow, today). A range
("this week") or a date phrase it cannot resolve ("the 30th") stops the search, exactly as it retires a carried date.
The date found is written back to the store, so the next turn has it either way.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

OLD = """const carriedRec = store[dateKey];
const carriedOk = Boolean(carriedRec && carriedRec.date
                          && carriedRec.epoch === epoch && carriedRec.day === todayStamp);
"""
NEW = """let carriedRec = store[dateKey];
let carriedOk = Boolean(carriedRec && carriedRec.date
                          && carriedRec.epoch === epoch && carriedRec.day === todayStamp);

// v195 (live QA 30 Sep 13:18): static data is saved only when an execution finishes, and a turn now runs on after its
// reply (the Turn Log). "no client" typed three seconds after the question loaded the store before the previous turn
// had saved "tomorrow" -> no date, MISSING_DATE, "What is the date for this booking?". So when nothing is carried, the
// requester's own earlier messages today (newest first, back to a reset) are read for the date - same rules as above.
// A range or an unresolved date phrase stops the search, as it retires a carried date.
const firstDateIn = text => {
  const t = clean(text);
  const hits = [];
  const add = (i, d) => { if (i >= 0) hits.push({ i, d }); };
  const xd = explicitDate(t);
  if (xd) add(t.indexOf(xd.shown), new Date(Date.UTC(xd.y, xd.mo, xd.d)));
  const MD = /\\b(?:(\\d{1,2})(?:st|nd|rd|th)?\\s+(?:of\\s+)?([A-Za-z]{3,9})|([A-Za-z]{3,9})\\.?\\s+(\\d{1,2})(?:st|nd|rd|th)?)\\b(?!,?\\s*\\d{4})/g;
  let m;
  while ((m = MD.exec(t)) !== null) {
    const mon = MONTHS[String(m[2] || m[3] || '').slice(0, 3).toLowerCase()], day = +(m[1] || m[4]);
    if (mon !== undefined && day >= 1 && day <= 31) add(m.index, new Date(Date.UTC(today.getUTCFullYear(), mon, day)));
  }
  const nwd = new RegExp('\\\\b' + DAYRE + '\\\\s+(?:of\\\\s+)?next\\\\s+week\\\\b|\\\\bnext\\\\s+week(?:\\'s)?\\\\s+' + DAYRE + '\\\\b', 'gi');
  while ((m = nwd.exec(t)) !== null) add(m.index, addDays(weekMonday, 7 + ((dayIndex(m[1] || m[2]) + 6) % 7)));
  const nx = new RegExp('\\\\bnext\\\\s+' + DAYRE + '\\\\b', 'gi');
  while ((m = nx.exec(t)) !== null) add(m.index, addDays(weekMonday, 7 + ((dayIndex(m[1]) + 6) % 7)));
  const th = new RegExp('\\\\bthis\\\\s+' + DAYRE + '\\\\b', 'gi');
  while ((m = th.exec(t)) !== null) add(m.index, addDays(weekMonday, (dayIndex(m[1]) + 6) % 7));
  const bare = new RegExp('(?<!\\\\b(?:next|this|last|every|each)\\\\s)(?<!\\\\bnext\\\\s+week(?:\\'s)?\\\\s+)\\\\b' + DAYRE + '\\\\b(?!\\\\s+(?:of\\\\s+)?next\\\\s+week)', 'gi');
  while ((m = bare.exec(t)) !== null) {
    let d = addDays(weekMonday, (dayIndex(m[1]) + 6) % 7);
    if (d.getTime() < today.getTime()) d = addDays(d, 7);
    add(m.index, d);
  }
  if ((m = t.match(/\\btomorrow\\b/i))) add(m.index, addDays(today, 1));
  if ((m = t.match(/\\b(today|tonight)\\b/i))) add(m.index, today);
  const ranged = /\\b(?:this|next)\\s+(?:week|month)\\b|\\bweekend\\b/i.test(t);
  if (!hits.length) return (ranged || /\\b\\d{1,2}(?:st|nd|rd|th)\\b/i.test(t)) ? { stop: true } : null;
  if (ranged && !/\\b(?:(?:this|next)\\s+week(?:'s)?\\s+|next\\s+)?(?:sun|mon|tues|wednes|thurs|fri|satur)day\\b/i.test(t)) return { stop: true };
  return { date: hits[0].d };   // rule order, as primaryDate above: written dates first, then weekdays, then tomorrow
};
if (!isReset && !msgDates.length && !dateUnresolved && !sawRange && !carriedOk) {
  const _manilaDay = ts => new Date(parseFloat(ts) * 1000 + 8 * 3600 * 1000).toISOString().slice(0, 10);
  const _nowDay = manila.toISOString().slice(0, 10);
  for (const m of msgs) {
    if (!m || isBot(m) || String(m.ts || '') === String(trigger.ts || '')) continue;
    if (/^reset$/i.test(clean(m.text))) break;
    if (!m.ts || _manilaDay(m.ts) !== _nowDay) break;
    if (epoch && parseFloat(m.ts) < parseFloat(epoch)) break;
    const f = firstDateIn(m.text);
    if (!f) continue;
    if (f.stop) break;
    carriedRec = { date: f.date.toISOString().slice(0, 10), epoch: epoch, day: todayStamp, from: 'history' };
    store[dateKey] = carriedRec;
    carriedOk = true;
    break;
  }
}
"""

def fix(w):
    w["name"] = "Project Jessie — v195 (date carry fix)"
    g = node(w, "Gate Context")["parameters"]; g["jsCode"] = sub1(g["jsCode"], OLD, NEW, "carry")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
