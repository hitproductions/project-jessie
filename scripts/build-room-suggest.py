#!/usr/bin/env python3
"""Book Session v63 (bugs 11 + 13 fix) - QA 28 Sep, decided 29 Sep: "if no room picked, suggest a room (the highest
ranked), and ask if they are ok with it".
  scripts/build-room-suggest.py <book-pull> <book-out>

QA 11/13: with no room named, the model chose one itself (Studio 1 + booth Studio A for Localization, Studio 7 for a
celebrity session), sometimes one that was taken, and put it in the summary as if it had been asked for.
Now, in prepare mode, when the requester's own messages (requester_text) name no room, Check Conflicts replaces the
model's room with the highest-ranked room for the session type that is free in the window (the session type's
Priority list in order, then Last Resort; conference rooms and the lobby never). Booths the model paired are kept
only if free. The summary shows that room and says it is a suggestion: "I picked Studio 7 - the first choice for VO
Recording that is free then. OK with that room? If not, tell me which one you'd like." The yes books it; naming a
room in any message uses theirs instead. When no ranked room is free, nothing is prepared and the model is told to
offer other times. Not in prepare mode (the yes, series, consent placements): unchanged.
"""
import json, sys

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

REQ_ROOM_OLD = "if (!String(REQ.rooms || '').trim())     missing.push('a room');"
REQ_ROOM_NEW = ("// v63: in prepare mode a missing room is picked below (the top-ranked free room), not refused here.\n"
                "if (!String(REQ.rooms || '').trim() && !(__prep && String(REQ.requester_text || '').trim() && String(REQ.session_type || '').trim())) missing.push('a room');")

PICK_ANCHOR = "const roomOverride = REQ.room_override === true || String(REQ.room_override).toLowerCase() === 'true';\n"
PICK_NEW = PICK_ANCHOR + r"""// --- v63 (QA bugs 11/13): no room named -> the highest-ranked free room, shown as a suggestion ----------------------
// The model chose rooms itself when none was asked for, sometimes a taken one. In prepare mode, when the requester's
// own messages name no room, the room is the session type's first free ranked room (Priority in order, then Last
// Resort; never a conference room or the lobby), and the summary says it was picked and asks if it is OK.
let __roomSuggested = '';
if (__prep && !roomOverride && !allDay && String(REQ.requester_text || '').trim() && (priorityIds.length || lastIds.length)) {
  const _rt = ' ' + String(REQ.requester_text || '').toLowerCase().replace(/\s+/g, ' ') + ' ';
  const _esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const _named = Object.keys(ROOMS).some(n => {
    const ln = n.toLowerCase();
    return new RegExp('[^a-z0-9]' + _esc(ln) + '(?![a-z0-9])').test(_rt) || new RegExp('[^a-z0-9]' + _esc(ln.replace(/\s+/g, '')) + '(?![a-z0-9])').test(_rt);
  });
  if (!_named) {
    let _R = {}; try { _R = JSON.parse(String(REQ.reference_data || '{}')); } catch (e) {}
    const _common = new Set((_R.rooms || []).filter(r => r.common).map(r => String(r.name).toLowerCase()));
    const _s = new Date(REQ.start_iso).getTime(), _e = new Date(REQ.end_iso).getTime();
    const _ex = String(REQ.exclude_event_id || '').trim();
    const _busy = new Set();
    for (const ev of EVENTS) {
      if (!ev || !ev.id || ev.status === 'cancelled' || (_ex && ev.id === _ex)) continue;
      const s0 = evMs(ev.start && (ev.start.dateTime || ev.start.date)), e0 = evMs(ev.end && (ev.end.dateTime || ev.end.date));
      if (!(s0 < _e && e0 > _s)) continue;
      const emails = (ev.attendees || []).map(a => String(a.email || '').toLowerCase());
      const loc = String(ev.location || '').toLowerCase(), firstSeg = String(ev.summary || '').split(' - ')[0].trim().toLowerCase();
      for (const k of Object.keys(ROOMS)) {
        const lk = k.toLowerCase();
        if (emails.indexOf(ROOMS[k].toLowerCase()) !== -1 || (loc && loc.indexOf(lk) !== -1) || firstSeg === lk) _busy.add(lk);
      }
    }
    const _ranked = [...new Set(priorityIds.concat(lastIds).map(id => nameById[id]).filter(Boolean))]
      .filter(r => ROOMS[r] && !_common.has(r.toLowerCase()) && !isBooth[r.toLowerCase()]);
    const _top = _ranked.find(r => !_busy.has(r.toLowerCase()));
    if (!_top) {
      return [{ json: { verdict:'REJECTED', reason:'NO_ROOM', ranked: _ranked,
        human: 'None of the usual rooms for ' + ((stRec ? stRec.type : '') || 'this session') + ' (' + _ranked.join(', ')
             + ') is free then, so nothing was prepared. Offer 2-3 other times, or ask which room they would like.' } }];
    }
    const _booths = String(REQ.rooms || '').split(',').map(r => r.trim()).filter(r => r && isBooth[r.toLowerCase()] && !_busy.has(r.toLowerCase()));
    REQ.rooms = [_top].concat(_booths).join(', ');
    __roomSuggested = _top;
  }
}
"""

CLEAR_OLD = "return [{ json: { verdict:'CLEAR', duration_note: durationNote,"
CLEAR_NEW = "return [{ json: { verdict:'CLEAR', duration_note: durationNote, final_rooms: REQ.rooms, room_suggested: __roomSuggested,   // v63"
OCC_OLD = "  return [{ json: { verdict:'REJECTED', reason:'ROOM_OCCUPIED', conflicts,\n    final_description:"
OCC_NEW = "  return [{ json: { verdict:'REJECTED', reason:'ROOM_OCCUPIED', conflicts, final_rooms: REQ.rooms, room_suggested: __roomSuggested,   // v63\n    final_description:"

RS_ROOMS_OLD = "const rooms = String(REQ.rooms || '').split(',').map(r => r.trim()).filter(Boolean).join(', ');"
RS_ROOMS_NEW = ("// v63: the room Check Conflicts settled on (the suggested one when none was named).\n"
                "const rooms = String(CC.final_rooms || REQ.rooms || '').split(',').map(r => r.trim()).filter(Boolean).join(', ');")
RS_NOTE_OLD = "if (newClient) notes.push("
RS_NOTE_NEW = ("// v63 (QA bugs 11/13): the room was picked, not asked for - say so and ask if it is OK.\n"
               "if (CC.room_suggested) notes.push('I picked ' + CC.room_suggested + ' - the first choice for ' + (st || 'this session') + \" that is free then. OK with that room? If not, tell me which one you'd like.\");\n"
               + RS_NOTE_OLD)

def book_fix(w):
    w["name"] = "Jessie — Book Session — v63 (bugs 11 + 13 fix)"
    c = node(w, "Check Conflicts")["parameters"]
    s = sub1(c["jsCode"], REQ_ROOM_OLD, REQ_ROOM_NEW, "required room")
    s = sub1(s, PICK_ANCHOR, PICK_NEW, "pick")
    s = sub1(s, CLEAR_OLD, CLEAR_NEW, "clear")
    s = sub1(s, OCC_OLD, OCC_NEW, "occupied")
    c["jsCode"] = s
    r = node(w, "Render Summary")["parameters"]
    t = sub1(r["jsCode"], RS_ROOMS_OLD, RS_ROOMS_NEW, "rs rooms")
    r["jsCode"] = sub1(t, RS_NOTE_OLD, RS_NOTE_NEW, "rs note")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(book_fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1])
