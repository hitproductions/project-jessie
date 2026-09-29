#!/usr/bin/env python3
"""main v189 (duplicates + move fixes) and Move Booking v25 (move card) - 29 Sep, the three next fixes after live QA.
  scripts/build-dedupe-move-card.py <main-pull> <main-out> <move-pull> <move-out>

1. PENDING 57 - a late Slack retry after a re-send ran twice (15:41 and 16:16 PHT: two identical summaries, then
   "That's already booked"). New main node Duplicate Check (after Gate Context): a message whose text matches another
   one from the same person within 2 minutes, with no Jessie message between the two and a Jessie reply after both,
   was already answered - it is dropped quietly (the eyes reaction is cleared, nothing is sent). Two "yes" replies to
   two different summaries always have a Jessie message between them, so both still count.
2. The move card showed only where the booking was going. Move Booking v25 checks the booking (title, date, owner)
   before asking for the yes, and its NOT_CONFIRMED answer carries a card written in code - "*Now:* ... *Moving to:*
   ..." - which Guard Probe sends as the reply, the way it sends prepared summaries and cancel cards. A move of a
   booking that is not theirs, or not on the calendar, is now refused before the card, not after the yes.
3. A change right after "Moved" (not only after "Booked.") is a move of that booking with the length kept: Booked For
   reads the booking from Jessie's "Moved ..." message, and the same move_instead / Move Booking times apply. The gate
   no longer flags a lone time right after "Moved" as start-time-only.
"""
import json, sys, uuid

def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# ---------------------------------------------------------------- 1. Duplicate Check (main)
DUP_CODE = r"""// Duplicate Check (main v189, PENDING 57). Slack sometimes fails a delivery and retries it a minute later; by then the
// requester has often re-sent the same text, which was answered. The late copy used to run as a new message (29 Sep
// 15:41 and 16:16 PHT: two identical summaries, then "That's already booked"). A message is dropped here when the same
// person sent the same text within 2 minutes, no Jessie message falls between the two, and Jessie has replied after
// both - that one was answered already. Passes Gate Context's output through untouched otherwise. Never throws.
let dup = false, why = '';
try {
  const trig = $('Slack Trigger').first().json || {};
  const norm = s => String(s || '').replace(/\s+/g, ' ').trim().toLowerCase();
  const me = String(trig.user || ''), myTs = parseFloat(String(trig.ts || '0')) || 0, mine = norm(trig.text);
  let msgs = []; try { msgs = $('Get Recent Messages').all().map(i => (i && i.json) || {}); } catch (e) {}
  const isBot = m => Boolean(m.bot_id || (m.message && m.message.bot_id)) || m.subtype === 'bot_message';
  const L = msgs.map(m => ({ ts: parseFloat(String(m.ts || '0')) || 0, bot: isBot(m), user: String(m.user || ''), t: norm(m.text || (m.message && m.message.text)) }))
    .filter(x => x.ts);
  if (me && myTs && mine) {
    for (const o of L) {
      if (o.bot || o.user !== me || o.t !== mine || o.ts === myTs || Math.abs(o.ts - myTs) > 120) continue;
      const lo = Math.min(o.ts, myTs), hi = Math.max(o.ts, myTs);
      const between = L.some(x => x.bot && x.ts > lo && x.ts < hi);
      const after = L.some(x => x.bot && x.ts > hi);
      if (!between && after) { dup = true; why = 'same text as the message at ' + o.ts + ', already answered'; break; }
    }
  }
} catch (e) { dup = false; }
if (dup) return [{ json: { _dup: true, _dupWhy: why } }];
return $input.all();
"""

# ---------------------------------------------------------------- 3. Booked For: after "Moved" too
BF_SCAN_OLD = """      if (/^\\s*\\*?(booked\\b|done\\s*-|moved\\b|cancell?ed\\b)|has been booked/i.test(t)) { if (/^\\s*\\*?booked\\b|has been booked/i.test(t)) __bookedAt = n; break; }"""
BF_SCAN_NEW = """      if (/^\\s*\\*?(booked\\b|done\\s*-|moved\\b|cancell?ed\\b)|has been booked/i.test(t)) { if (/^\\s*\\*?booked\\b|has been booked/i.test(t)) __bookedAt = n; else if (/^\\s*\\*?moved\\b/i.test(t)) { __bookedAt = n; __movedText = t; } break; }"""
BF_LET_OLD = "  let __bookedAt = -1;   // v184: where the scan met Jessie's \"Booked.\""
BF_LET_NEW = BF_LET_OLD + "\n  let __movedText = '';   // v189: or her \"Moved ...\" - the booking is read from that message itself"
BF_SUM_OLD = """      let sum = '';
      for (let k = __bookedAt; k < msgs.length && k < __bookedAt + 6; k++) {"""
BF_SUM_NEW = """      let sum = '';
      // v189: after "Moved ...", the booking (now where it was moved to) is in that message, not in a summary
      if (__movedText) {
        const _mt = __movedText, _g = re => ((_mt.match(re) || [])[1] || '').trim();
        const _ti = _g(/^\\s*\\*?Moved\\s+["“]([^"”\\n]+)["”]/i), _dt = _g(/((?:[A-Za-z]+day,\\s+)?[A-Za-z]+\\s+\\d{1,2},\\s*\\d{4})/),
              _tm = _g(/(\\d{1,2}:\\d{2}\\s*[AP]M\\s*(?:–|-|—|to)\\s*\\d{1,2}:\\d{2}\\s*[AP]M)/i), _rm = _g(/\\bin\\s+([A-Z][^.\\n,]*?)\\s*\\.?\\s*$/m);
        if (_ti && _dt && _tm) sum = '*' + _ti + '*\\n*Date:* ' + _dt + '\\n*Time:* ' + _tm.replace(/\\s*(?:to|—)\\s*/i, ' – ') + (_rm ? '\\n*Room:* ' + _rm : '');
      }
      for (let k = __bookedAt; !sum && k < msgs.length && k < __bookedAt + 6; k++) {"""
BF_NOTE_OLD = "          notes.push('THEY ARE CHANGING THE BOOKING THEY JUST MADE: \"'"
BF_NOTE_NEW = "          notes.push((__movedText ? 'THEY ARE CHANGING THE BOOKING THEY JUST MOVED: \"' : 'THEY ARE CHANGING THE BOOKING THEY JUST MADE: \"')"

GATE_OLD = "|| /^\\s*\\*?booked\\b/i.test(lastBotText))) { delete store[soKey]; }"
GATE_NEW = "|| /^\\s*\\*?(?:booked|moved)\\b/i.test(lastBotText))) { delete store[soKey]; }   // v189: after \"Moved\" too"

# ---------------------------------------------------------------- 2. Guard Probe: the move card is the reply
GP_ANCHOR = "// --- v168 (live, 28 Sep): they said no, and the same summary went out again -----------------------------------"
GP_MOVE = """// --- v189: the move card IS the reply -------------------------------------------------------------------------------
// Move Booking v25 checks the booking before asking for the yes and writes the card itself - where it is now and where it
// is going - so the requester sees both before approving. Same rule as a cancel card: the latest Move Booking call this
// turn decides, and nothing below may change it.
try {
  const _s2 = (($input.first().json || {}).intermediateSteps) || [];
  for (let i = _s2.length - 1; i >= 0; i--) {
    const _t = String(((_s2[i] || {}).action || {}).tool || '').replace(/[_\\s]+/g, ' ').toLowerCase();
    if (_t !== 'move booking') continue;
    let _o = null; try { _o = [].concat(JSON.parse(String((_s2[i] || {}).observation || '')))[0]; } catch (e) {}
    if (_o && _o.reason === 'NOT_CONFIRMED' && _o.card_text) { text = String(_o.card_text); _prepared = true; }
    break;
  }
} catch (e) {}

"""

# ---------------------------------------------------------------- 2. Move Booking v25
MV_NC_OLD = """if (!confirmed) return bad('NOT_CONFIRMED',
  'Nothing was moved. Show the requester the booking and the new time, end that message with the line '
  + '"Confirm to move. (yes/no)", and stop. Move it only after they reply yes.');
"""
MV_NC_NEW = """// v25: an unconfirmed move is answered further down, once the booking is found and theirs - with a card showing where
// it is now and where it is going. It used to be refused here, before the booking was even looked up.
"""
MV_RET_OLD = "const roomNote = outLocation ? (' to ' + outLocation) : '';\nreturn [{ json: { verdict:'CLEAR',"
MV_RET_NEW = """const roomNote = outLocation ? (' to ' + outLocation) : '';
if (!confirmed) {
  const _day = iso => { const d = /^\\d{4}-\\d{2}-\\d{2}$/.test(iso) ? new Date(iso + 'T12:00:00+08:00') : new Date(iso);
    return new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }).format(d); };
  const _hm = iso => new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' }).format(new Date(iso));
  const _names = (atts, loc) => { const em = (atts || []).map(a => String(a.email || '').toLowerCase()), lc = String(loc || '').toLowerCase();
    const k = Object.keys(ROOMS).filter(r => em.indexOf(ROOMS[r].toLowerCase()) !== -1);
    return (k.length ? k : Object.keys(ROOMS).filter(r => new RegExp('(^|[^a-z0-9])' + r.toLowerCase() + '(?![a-z0-9])').test(lc))).join(', '); };
  const os = (ev.start && (ev.start.dateTime || ev.start.date)) || '', oe = (ev.end && (ev.end.dateTime || ev.end.date)) || '';
  const _when = (s, e) => /^\\d{4}-\\d{2}-\\d{2}$/.test(s) ? _day(s) + ', all day' : _day(s) + ', ' + _hm(s) + ' – ' + _hm(e);
  const nowRoom = _names(ev.attendees, ev.location), newRoom = newRooms.length ? outLocation : nowRoom;
  const card = '*' + title + '*\\n*Now:* ' + _when(os, oe) + (nowRoom ? ', ' + nowRoom : '')
    + '\\n*Moving to:* ' + _when(REQ.new_start_iso, REQ.new_end_iso) + (newRoom ? ', ' + newRoom : '') + '\\n\\nConfirm to move.';
  return [{ json: { verdict:'REJECTED', reason:'NOT_CONFIRMED', title, card_text: card,
    human: 'Nothing was moved yet. The move card is sent to the requester automatically - do not write one. When they reply yes, '
         + 'call Move Booking again with exactly the same title, booking date and new times.' } }];
}
return [{ json: { verdict:'CLEAR',"""
MV_REJ_OLD = """return [{ json: { status:'REJECTED', reason: v.reason || 'FAILED',
  human: v.human || 'Nothing was moved and the reason is unclear. Tell the requester it did not go through.' } }];"""
MV_REJ_NEW = """return [{ json: { status:'REJECTED', reason: v.reason || 'FAILED', card_text: v.card_text || undefined,   // v25: the move card
  human: v.human || 'Nothing was moved and the reason is unclear. Tell the requester it did not go through.' } }];"""

def main_fix(w):
    w["name"] = "Project Jessie — v189 (duplicates + move fixes)"
    b = node(w, "Booked For")["parameters"]; c = b["jsCode"]
    c = sub1(c, BF_LET_OLD, BF_LET_NEW, "let")
    c = sub1(c, BF_SCAN_OLD, BF_SCAN_NEW, "scan")
    c = sub1(c, BF_SUM_OLD, BF_SUM_NEW, "sum")
    c = sub1(c, BF_NOTE_OLD, BF_NOTE_NEW, "note")
    b["jsCode"] = c
    g = node(w, "Gate Context")["parameters"]; g["jsCode"] = sub1(g["jsCode"], GATE_OLD, GATE_NEW, "gate")
    p = node(w, "Guard Probe")["parameters"]; p["jsCode"] = sub1(p["jsCode"], GP_ANCHOR, GP_MOVE + GP_ANCHOR, "guard move")

    gc = node(w, "Gate Context"); x, y = gc["position"]
    C = w["connections"]
    nxt = C["Gate Context"]["main"][0]
    if [t["node"] for t in nxt] != ["All Rooms"]: raise SystemExit("Gate Context no longer feeds All Rooms: " + str(nxt))
    # shift everything right of Gate Context on its row? No - place the two new nodes below it.
    dc = {"id": str(uuid.uuid4()), "name": "Duplicate Check", "type": "n8n-nodes-base.code", "typeVersion": 2,
          "position": [x, y - 192], "parameters": {"jsCode": DUP_CODE}}
    ifn = json.loads(json.dumps(node(w, "Cancel Direct?")))
    ifn.update(id=str(uuid.uuid4()), name="Duplicate?", position=[x + 176, y - 192])
    ifn["parameters"]["conditions"]["conditions"][0].update(id=str(uuid.uuid4()), leftValue="={{ $json._dup === true ? 'yes' : 'no' }}")
    w["nodes"] += [dc, ifn]
    C["Gate Context"] = {"main": [[{"node": "Duplicate Check", "type": "main", "index": 0}]]}
    C["Duplicate Check"] = {"main": [[{"node": "Duplicate?", "type": "main", "index": 0}]]}
    C["Duplicate?"] = {"main": [[{"node": "Clear Ack", "type": "main", "index": 0}], nxt]}
    return w

def move_fix(w):
    w["name"] = "Jessie — Move Booking — v25 (move card)"
    r = node(w, "Resolve Booking")["parameters"]
    s = sub1(r["jsCode"], MV_NC_OLD, MV_NC_NEW, "nc")
    r["jsCode"] = sub1(s, MV_RET_OLD, MV_RET_NEW, "ret")
    j = node(w, "Return Rejection")["parameters"]; j["jsCode"] = sub1(j["jsCode"], MV_REJ_OLD, MV_REJ_NEW, "rej")
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(main_fix(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False)
    json.dump(move_fix(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False)
    print("wrote", a[1], a[3])
