#!/usr/bin/env python3
"""main v261 + Move Booking v28 - PENDING 102 (the Move Booking part): a move into a taken time offers the room's nearest
free times that day, like a booking does (Book Session v101 / main v249).

  Move Booking read only the new window, so its taken-time reply could only say "That time is already booked ... Want a
  different time or room?".
Move Booking v28: Get New Window reads the new day 8 AM - 10 PM (or wider); Check New Window still judges only the new window,
  and on a clash returns same_day_slots - the same room's nearest free time of the same length before and after (nearer first,
  a tie the earlier, back-to-back allowed, the booking being moved not counted, an event with no room blocking) and the
  clashing times; Return Rejection passes them on.
main v261: Guard Probe's move heads-up lists them - "✅ Free the same day at: • 11:00 AM – 1:00 PM • 3:00 PM – 5:00 PM", then
  "The booking stays where it is. Want one of those, or another time or room?".

  scripts/build-v261.py <main-v260> <main-out> <move-v27> <move-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
URL_OLD = "events?timeMin={{ encodeURIComponent($json.new_start) }}&timeMax={{ encodeURIComponent($json.new_end) }}&singleEvents=true&maxResults=250"
URL_NEW = ("events?timeMin={{ encodeURIComponent((() => { const a = String($json.new_start || '').slice(0, 10) + 'T08:00:00+08:00'; return new Date($json.new_start).getTime() < new Date(a).getTime() ? $json.new_start : a; })()) }}"
           "&timeMax={{ encodeURIComponent((() => { const b = String($json.new_start || '').slice(0, 10) + 'T22:00:00+08:00'; return new Date($json.new_end).getTime() > new Date(b).getTime() ? $json.new_end : b; })()) }}&singleEvents=true&maxResults=250")
CNW_OLD = """if (clashes.length) {
  return [{ json: { verdict:'REJECTED', reason:'ROOM_OCCUPIED', conflicts: clashes,"""
CNW_NEW = r"""// v28 (PENDING 102): the new day is read 8 AM - 10 PM, so a clash comes with the room's nearest free times that day
let __sameDay = [];
if (clashes.length) {
  try {
    const D = ne - ns, day = new Date(ns + 8 * 3600000).toISOString().slice(0, 10);
    const lo = Date.parse(day + 'T08:00:00+08:00'), hi = Date.parse(day + 'T22:00:00+08:00');
    const blk = items.filter(e => String(e.id) !== String(R.original_id)).map(e => {
      const emails = (e.attendees || []).map(a => String(a.email || '').toLowerCase());
      const same = mine.some(m => emails.indexOf(m) !== -1) || (loc && String(e.location || '').toLowerCase() === loc);
      const noRoom = !emails.some(x => /resource\.calendar\.google\.com$/.test(x)) && !String(e.location || '').trim();
      return { s: evMs(e.start && (e.start.dateTime || e.start.date)), e: evMs(e.end && (e.end.dateTime || e.end.date)), hit: same || noRoom }; })
      .filter(b => b.hit && b.s < hi && b.e > lo);
    const c = new Set(); for (let t = lo; t + D <= hi; t += 30 * 60000) c.add(t);
    for (const b of blk) { c.add(b.e); c.add(b.s - D); }
    const okT = [...c].filter(t => t >= lo && t + D <= hi && t !== ns && blk.every(b => !(b.s < t + D && b.e > t)));
    const b4 = okT.filter(t => t < ns).sort((x, y) => y - x)[0], af = okT.filter(t => t > ns).sort((x, y) => x - y)[0];
    const iso = ms => new Date(ms + 8 * 3600000).toISOString().slice(0, 19) + '+08:00';
    __sameDay = [b4, af].filter(t => t !== undefined).sort((x, y) => Math.abs(x - ns) - Math.abs(y - ns) || x - y).map(t => ({ start: iso(t), end: iso(t + D) }));
  } catch (e) { __sameDay = []; }
}
if (clashes.length) {
  return [{ json: { verdict:'REJECTED', reason:'ROOM_OCCUPIED', conflicts: clashes, same_day_slots: __sameDay,"""
RR_OLD = "return [{ json: { status:'REJECTED', reason: v.reason || 'FAILED', card_text: v.card_text || undefined,   // v25: the move card"
RR_NEW = ("return [{ json: { status:'REJECTED', reason: v.reason || 'FAILED', card_text: v.card_text || undefined,   // v25: the move card\n"
          "  same_day_slots: Array.isArray(v.same_day_slots) ? v.same_day_slots : undefined,   // v28: the room's nearest free times that day")
GP_OLD = """        text = '❌ Heads up: *That time is already booked*' + (_ti ? ' by ' + (/", "/.test(_ti) ? 'these sessions: ' + _ti.split('", "').join(' · ') : 'this session: ' + _ti) : '')
          + '\\n\\nThe booking stays where it is. Want a different time or room?';"""
GP_NEW = """        // v261 (PENDING 102): the room's nearest free times that day (Move Booking v28)
        const _sdM = [].concat(_oT.same_day_slots || []).filter(x => x && x.start && x.end);
        text = '❌ Heads up: *That time is already booked*' + (_ti ? ' by ' + (/", "/.test(_ti) ? 'these sessions: ' + _ti.split('", "').join(' · ') : 'this session: ' + _ti) : '')
          + (_sdM.length ? '\\n\\n✅ Free the same day at:\\n' + _sdM.map(x => '• ' + _hmT(x.start) + ' – ' + _hmT(x.end)).join('\\n') + '\\n\\nThe booking stays where it is. Want one of those, or another time or room?'
            : '\\n\\nThe booking stays where it is. Want a different time or room?');"""
def main(w):
    w["name"] = "Project Jessie — v261 (move alternatives)"
    gp = node(w, "Guard Probe")["parameters"]; gp["jsCode"] = once(gp["jsCode"], GP_OLD, GP_NEW, "move heads-up"); return w
def move(w):
    w["name"] = "Jessie — Move Booking — v28 (nearest free times)"
    g = node(w, "Get New Window")["parameters"]; g["url"] = once(g["url"], URL_OLD, URL_NEW, "url")
    c = node(w, "Check New Window")["parameters"]; c["jsCode"] = once(c["jsCode"], CNW_OLD, CNW_NEW, "clash")
    r = node(w, "Return Rejection")["parameters"]; r["jsCode"] = once(r["jsCode"], RR_OLD, RR_NEW, "rr")
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 4: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(move(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
