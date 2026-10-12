#!/usr/bin/env python3
"""Book Session v106 - PENDING 44, and no engineer line on internal rooms.

  44: "Booked." even when the room declines seconds later. Verify read only Create Event's response, where a room resource is
      always 'needsAction' - it answers the invitation a few seconds later - so a room whose own calendar has something Jessie
      cannot see (a tablet booking, PENDING 42) declined after Jessie had said "Booked.". 12 Oct 16:58 on v104: the M4 hold
      still 'needsAction' when read back.
  Internal rooms: the M4 hold carried "Engineer: Howard Luistro" (12 Oct) - an M booth, conference room or the Lobby has no
      engineer.
Book Session v106:
  - Create Event -> Wait for Room (6 s) -> Reread Event (GET the event; on any error the create response stands) -> Verify.
  - Verify reads the re-read event: a room that declined -> ROOM_DECLINED with a reply written for the requester ("❌ Studio 7
    turned this booking down - its own calendar shows it is taken then. Nothing is booked. Want another time or studio?").
    The declined event is left as it is (deleting it is a decision for later).
  - Check Conflicts: no "Engineer:" line in the description of an M booth, conference room or Lobby booking.

  scripts/build-book-v106.py <book-v105> <book-out>
"""
import json, sys, uuid, copy
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def once(s, old, new, what):
    if s.count(old) != 1: raise SystemExit(f"{what}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
CC_OLD = "if (eng && !segs.some(s => /^engineer\\s*:/i.test(s))) segs.unshift('Engineer: ' + eng);\n"
CC_NEW = CC_OLD + ("// v106 (12 Oct: \"M4 - Howard\" carried \"Engineer: Howard Luistro\"): an M booth, conference room or the Lobby has no engineer\n"
                   "if (/^(?:M[1-8]|Salin|Katha|Likha|Lobby)$/i.test(String(REQ.rooms || '').trim())) for (let i = segs.length - 1; i >= 0; i--) if (/^engineer\\s*:/i.test(segs[i])) segs.splice(i, 1);\n")
V_OLD = "const ev = $input.first().json || {};\n"
V_NEW = ("// v106 (PENDING 44): the event as read back a few seconds after it was made (Wait for Room -> Reread Event), so a room that\n"
         "// declined is seen; on any error reading it back, the create response stands\n"
         "let ev = {};\n"
         "try { const _r = $input.first().json || {}; ev = _r.id ? _r : ($('Create Event').first().json || {}); } catch (e) { ev = {}; }\n"
         "if (!ev.id) { try { ev = $('Create Event').first().json || {}; } catch (e) {} }\n")
D_OLD = """  return [{ json: { status:'ROOM_DECLINED', event_id: ev.id, declined,
    human:'The room declined the booking because it is already taken, so this booking is NOT valid. Tell the requester and offer 2-3 alternatives. Do not delete whatever holds the room.' } }];"""
D_NEW = """  // v106: written for the requester - Book Direct sends it as it is
  const _rm = declined.map(x => (String(x).match(/(Studio [0-9A-Z]|M[1-8]|Salin|Katha|Likha|Lobby)\\b/) || [])[1] || String(x)).join(' and ');
  return [{ json: { status:'ROOM_DECLINED', event_id: ev.id, declined,
    human: '❌ ' + _rm + ' turned this booking down - its own calendar shows it is taken then. Nothing is booked. Want another time or studio?' } }];"""
def book(w):
    w["name"] = "Jessie — Book Session — v106 (room decline seen, no engineer on internal rooms)"
    cc = node(w, "Check Conflicts")["parameters"]; cc["jsCode"] = once(cc["jsCode"], CC_OLD, CC_NEW, "engineer line")
    v = node(w, "Verify")["parameters"]; c = once(v["jsCode"], V_OLD, V_NEW, "verify ev"); v["jsCode"] = once(c, D_OLD, D_NEW, "declined text")
    ce = node(w, "Create Event"); x, y = ce["position"]
    wait = {"parameters": {"amount": 6, "unit": "seconds"}, "id": str(uuid.uuid4()), "name": "Wait for Room", "type": "n8n-nodes-base.wait", "typeVersion": 1.1,
            "position": [x + 80, y + 160], "webhookId": str(uuid.uuid4())}
    gev = node(w, "Get Events In Window")
    reread = {"parameters": {"url": "=https://www.googleapis.com/calendar/v3/calendars/{{ encodeURIComponent('c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com') }}/events/{{ encodeURIComponent(String($('Create Event').first().json.id || '')) }}",
                             "authentication": "predefinedCredentialType", "nodeCredentialType": "googleCalendarOAuth2Api", "options": {}},
              "id": str(uuid.uuid4()), "name": "Reread Event", "type": "n8n-nodes-base.httpRequest", "typeVersion": 4.2, "position": [x + 160, y + 160],
              "credentials": copy.deepcopy(gev["credentials"]), "onError": "continueRegularOutput", "alwaysOutputData": True}
    w["nodes"] += [wait, reread]
    con = w["connections"]
    assert con["Create Event"]["main"][0] == [{"node": "Verify", "type": "main", "index": 0}]
    con["Create Event"]["main"][0] = [{"node": "Wait for Room", "type": "main", "index": 0}]
    con["Wait for Room"] = {"main": [[{"node": "Reread Event", "type": "main", "index": 0}]]}
    con["Reread Event"] = {"main": [[{"node": "Verify", "type": "main", "index": 0}]]}
    return w
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) != 2: print(__doc__.strip()); sys.exit(2)
    json.dump(book(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
