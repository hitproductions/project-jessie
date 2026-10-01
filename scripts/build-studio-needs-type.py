#!/usr/bin/env python3
"""Book Session v82 (studio needs a session type) - fixes v80/v81: live 1 Oct 19:11, "book studio 8 tonight for project
CATS 3-6pm" went straight to a card titled "CATS / Howard Luistro" - the model sent no session type at all, and the
session-type check (v80/v81) only judged a type the model did send. With no type a booking is treated like an internal
room (no initials rewrite either). Now a studio or booth room (not a conference room, the lobby or an M booth hold) with
no session type gets the same handling: the type named in the requester's words is told to the model, else asked.
  scripts/build-studio-needs-type.py <book-live> <book-out>
"""
import json, sys
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
OPEN_OLD = """if (__prep && String(REQ.session_type || '').trim() && String(REQ.requester_text || '').trim()) {
  let _RT = {}; try { _RT = JSON.parse(String(REQ.reference_data || '{}')); } catch (e) {}
  const _types = (_RT.types || []).map(t => String(t.type || '').trim()).filter(Boolean);
  const _cur = _types.find(t => t.toLowerCase() === String(REQ.session_type).trim().toLowerCase());
  if (_cur) {"""
OPEN_NEW = """// v82 (live 1 Oct 19:11): the model sent no session type at all for a studio ("CATS / Howard Luistro") - a studio or
// booth room (not a conference room, the lobby or an M booth hold) with no type is judged the same way.
let __RT0 = {}; try { __RT0 = JSON.parse(String(REQ.reference_data || '{}')); } catch (e) {}
const __commonRooms = new Set((__RT0.rooms || []).filter(r => r.common).map(r => String(r.name).toLowerCase()));
const __studioRoom = String(REQ.rooms || '').split(',').map(x => x.trim()).filter(Boolean).some(r => !__commonRooms.has(r.toLowerCase()) && !/^M[1-8]$/i.test(r));
if (__prep && (String(REQ.session_type || '').trim() || __studioRoom) && String(REQ.requester_text || '').trim()) {
  let _RT = __RT0;
  const _types = (_RT.types || []).map(t => String(t.type || '').trim()).filter(Boolean);
  const _cur = _types.find(t => t.toLowerCase() === String(REQ.session_type || '').trim().toLowerCase()) || '';
  if (_types.length) {"""
OK_OLD = "    const _ok = _fulls.length ? (_fulls.length === 1 && _fulls[0].t === _cur) : _named(_curO);"
OK_NEW = "    const _ok = _fulls.length ? (_fulls.length === 1 && _fulls[0].t === _cur) : (!!_curO && _named(_curO));   // v82: no type sent -> never ok"
IS_OLD = "    if (_fulls.length === 1 && _fulls[0].t !== _cur) {"
w = json.load(open(sys.argv[1])); w["name"] = "Jessie — Book Session — v82 (studio needs a session type)"
cc = node(w, "Check Conflicts")["parameters"]; s = cc["jsCode"]
s = sub1(s, OPEN_OLD, OPEN_NEW, "open"); s = sub1(s, OK_OLD, OK_NEW, "ok")
assert s.count(IS_OLD) == 1
cc["jsCode"] = s
json.dump(w, open(sys.argv[2], "w"), indent=2, ensure_ascii=False); print("wrote", sys.argv[2])
