#!/usr/bin/env python3
"""main v252 - the date and time are settled before anything else is asked (Howard, 9 Oct, on v250's 11:51 reply).

  "book studio f for me tomorrow" with Studio F part-booked got the heads-up, the free times, then "Studio F · Sunday,
  October 10 / What's the time, session type, project and client?" - the restated line read as a stray label under the
  options. Decided: the requester locks in the date and time first; the booking is said back (room · date · time) in the
  message that then asks for the rest.
main v252, Guard Probe (v247/v249 details question): with the date or the time still unknown, only they are asked ("What
  time works?", "What date and time work?"); the restated line is written only once the time is known; a room the early
  check found free with no time yet is said as "✅ Studio F is free on Sunday, October 10".

  scripts/build-v252.py <main-v251> <main-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
OLD = """      const _left = _it.filter(x => !((x === 'room' && _kn.room) || (x === 'date' && _kn.date) || ((x === 'time' || x === 'length') && _kn.time)));
      if (_it.length >= 2 && _left.length) {
        const _j = _left.length === 1 ? _left[0] : _left.length === 2 ? _left.join(' and ') : _left.slice(0, -1).join(', ') + ' and ' + _left[_left.length - 1];
        const _pre = [_kn.room && _freeSaid === _kn.room ? '✅ ' + _kn.room + ' is free' : _kn.room, _kn.date, _kn.time].filter(Boolean).join(' · ');
        text = (_pre ? _pre + '\\n' : '') + "What's the " + _j + '?' + (_left.indexOf('client') !== -1 ? ' (or "none" for no client)' : '');
      }"""
NEW = """      let _left = _it.filter(x => !((x === 'room' && _kn.room) || (x === 'date' && _kn.date) || ((x === 'time' || x === 'length') && _kn.time)));
      // v252 (decided 9 Oct): the date and time are settled first - while either is unknown only they are asked, and the
      // booking is said back (room · date · time) in the message that asks for the rest
      const _dtq = _left.filter(x => x === 'date' || x === 'time');
      if (_it.length >= 2 && _dtq.length) {
        text = (_freeSaid ? '✅ ' + _freeSaid + ' is free' + (_kn.date ? ' on ' + _kn.date : '') + '\\n' : '')
          + (_dtq.length === 2 ? 'What date and time work?' : _dtq[0] === 'date' ? 'What date works?' : 'What time works?');
        _freeSaid = '';
      } else if (_it.length >= 2 && _left.length) {
        const _j = _left.length === 1 ? _left[0] : _left.length === 2 ? _left.join(' and ') : _left.slice(0, -1).join(', ') + ' and ' + _left[_left.length - 1];
        const _pre = _kn.time ? [_kn.room && _freeSaid === _kn.room ? '✅ ' + _kn.room + ' is free' : _kn.room, _kn.date, _kn.time].filter(Boolean).join(' · ') : '';
        text = (_pre ? _pre + '\\n' : '') + "What's the " + _j + '?' + (_left.indexOf('client') !== -1 ? ' (or "none" for no client)' : '');
      }"""
def main(w):
    w["name"] = "Project Jessie — v252 (date and time first)"
    gp = node(w, "Guard Probe")["parameters"]; gp["jsCode"] = once(gp["jsCode"], OLD, NEW, "details")
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2: print(__doc__.strip()); sys.exit(2)
    json.dump(main(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
