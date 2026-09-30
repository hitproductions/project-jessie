#!/usr/bin/env python3
"""Book Session v68 (ISR shorthand fix) - live QA 30 Sep 12:44 PHT.
  scripts/build-session-shorthand.py <book-live> <book-out>

"book isr for studio 8 with rico tomorrow at 9am" was summarised as ISR / ISR / EG - Client: ISR, Project: ISR. ISR is
studio shorthand for In-Studio Recording, a VO Recording session: a session type, not a project or a client. And with
client == project the "not in the client list yet" note did not show, so nothing flagged it.

Prepare mode now checks the project and client against a list of session-type nicknames (built in: ISR / In-Studio
Recording -> VO Recording; plus an "aka" list on a session type in the reference data, if Session Types ever carries
one). A nickname in either slot, when the requester never wrote "project ISR" / "client ISR", prepares nothing and asks
once: "Just to check - by ISR, do you mean an In-Studio Recording (a VO Recording session)? What's the project name, and
who is the client?" If it was asked already (asked_text) and ISR is still in the slot, it only asks for the project
name, so it cannot loop.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

ANCHOR = "let __assumedMins = 0;\n"
BLOCK = ANCHOR + r"""// v68 (live QA 30 Sep): studio shorthand for a session type used as the project or client - "book isr ..." became
// ISR / ISR / EG. ISR = In-Studio Recording, a VO Recording session. Asked once, never booked as a project or client
// unless the requester said so ("project ISR", "client ISR").
if (__prep) {
  const _n = s => String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  const _AKA = { 'isr': { type: 'VO Recording', long: 'In-Studio Recording' },
                 'in studio recording': { type: 'VO Recording', long: 'In-Studio Recording' } };
  try { const _R0 = JSON.parse(String(REQ.reference_data || '{}'));
    for (const t of (_R0.types || [])) for (const a of [].concat(t.aka || [])) if (_n(a)) _AKA[_n(a)] = { type: t.type, long: String(a).trim() }; } catch (e) {}
  const _seg = String(REQ.summary || '').split(' / ').map(s => s.trim());
  const _slots = [['project', _seg[0] || ''], ['client', String(REQ.client || '').trim() || (_seg.length >= 3 ? _seg[1] : '')]];
  const _said = ' ' + _n(REQ.requester_text) + ' ', _asked = String(REQ.asked_text || '');
  const _hit = _slots.find(([k, v]) => _AKA[_n(v)] && _said.indexOf(' ' + k + ' ' + _n(v) + ' ') === -1);
  if (_hit) {
    const _w = String(_hit[1]).trim(), _a = _AKA[_n(_w)];
    const _again = /\bdo you mean an? /i.test(_asked) && new RegExp(_w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i').test(_asked);
    return [{ json: { verdict:'REJECTED', reason:'SESSION_SHORTHAND', shorthand: _w, session_type: _a.type, slot: _hit[0],
      human: _again
        ? 'Nothing was prepared. "' + _w + '" is the session type (' + _a.type + '), not the ' + _hit[0] + '. Ask exactly this, in one message: "What\'s the project name, and who is the client?"'
        : 'Nothing was prepared. Ask exactly this, in one message: "Just to check - by ' + _w + ', do you mean an ' + _a.long + ' (a ' + _a.type + ' session)? What\'s the project name, and who is the client?"' } }];
  }
}
"""

def fix(w):
    w["name"] = "Jessie — Book Session — v68 (ISR shorthand fix)"
    c = node(w, "Check Conflicts")["parameters"]; c["jsCode"] = sub1(c["jsCode"], ANCHOR, BLOCK, "anchor")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
