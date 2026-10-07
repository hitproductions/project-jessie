#!/usr/bin/env python3
"""main v230 + Room Availability v18 (early room check) - QA B4, 7 Oct (PENDING 95):
  Jess had Studio F on 14 Oct 1-4 PM and sent "book studio f on oct 14, 1-4pm plz". Jessie asked "What kind of session is
  this, what's the project title, and who's the client and engineer?" - no word that the room was taken. The room was only
  checked by Prepare Booking at the end, after every detail had been collected, and this reply was the model's own.
  Decided (Howard, 7 Oct): when the date is known, check the room at once. Free -> carry on collecting. Taken -> say so, and
  offer other rooms or another date.

  main v230: two nodes before the agent and one after.
    - Early Room Plan (Code, after Already Done?): runs the check when a booking names ONE room and ONE date, and this message
      named the room, a date or a time. The room comes from this message, else the requester's latest message for this
      booking - unless Jessie has since named a different room (an offer). Not for a yes, a cancel, a move, a series or an
      availability question (the model answers those with Room Availability itself).
    - Early Room Check? -> Early Room Check (Room Availability, the date and the six days after, the requested hours or
      8 AM - 10 PM) -> Early Room Result (Code): what to say. The agent's prompt gets it as a ROOM CHECK notice.
    - Guard Probe: taken at the requested time (or all day, when no time is known) -> the reply is replaced:
        "Studio F is already booked on Thursday, October 14, 1:00 PM – 4:00 PM (“TITLE”)." / "You already have Studio F ..."
        "Free at that time: Studio 1 · Studio 2 · ..." (the session type's ranking when one was named, else rooms of the same
        kind) and "Studio F is free at that time on Friday, October 15 · ..." (the next free days that week), then
        "Want one of those, or another day or time?"
      Booked for part of the day and no time given yet -> "Heads up: Studio F is already booked 1:00 PM – 4:00 PM on ..." on
      top of the model's reply. A booking card (Prepare Booking ran) is never touched - Book Session checks the room itself.
  Room Availability v18: day by day with a room asked, each day also carries free_rooms, and a taken room carries its events
  (start, end, title, ref) - so the one call answers the room, the other rooms that day, and the room on the next days.
  scripts/build-early-room-check.py <ra-v17> <ra-out> <main-v229> <main-out>
"""
import json, sys, uuid
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)

# ---------------------------------------------------------------- Room Availability v18
RA_EV_OLD = """      title: ev.summary || '(no title)', allDay: !!(ev.start && ev.start.date && !ev.start.dateTime), rooms: _roomsOf(ev) }));"""
RA_EV_NEW = """      title: ev.summary || '(no title)', allDay: !!(ev.start && ev.start.date && !ev.start.dateTime), rooms: _roomsOf(ev),
      ref: ((String(ev.description || '').match(/ref:\\s*([A-Za-z0-9]+)/) || [])[1] || '') }));   // v18: whose it is (main's early room check)"""
RA_ROOMS_OLD = """            return busyD[hit] ? { room: hit, status: 'BUSY', taken: _desc(busyD[hit]) } : { room: hit, status: 'FREE' }; });"""
RA_ROOMS_NEW = """            return busyD[hit] ? { room: hit, status: 'BUSY', taken: _desc(busyD[hit]),
              // v18: the events themselves, clipped to the day, for main's early room check
              events: busyD[hit].map(ev => ({ start: new Date(Math.max(ev.s, d0)).toISOString(), end: new Date(Math.min(ev.e, d0 + _D)).toISOString(),
                title: ev.title, ref: ev.ref, allDay: ev.allDay })) } : { room: hit, status: 'FREE' }; });
          // v18: and the other rooms free in that day's window, so one call also gives the alternatives
          day.free_rooms = Object.keys(active).filter(n => !busyD[n]).filter(n => !(_studiosOnly && isCommon[n])).sort();"""

def ra(w):
    w["name"] = "Jessie — Room Availability — v18 (early room check)"
    ca = node(w, "Compute Availability")["parameters"]; s = ca["jsCode"]
    s = sub1(s, RA_EV_OLD, RA_EV_NEW, "ra events"); s = sub1(s, RA_ROOMS_OLD, RA_ROOMS_NEW, "ra rooms")
    ca["jsCode"] = s
    return w

# ---------------------------------------------------------------- main v230
PLAN = r"""// v230 (QA B4, 7 Oct - PENDING 95): check the room as soon as the date is known. Jess asked for Studio F on 14 Oct 1-4 PM,
// which she already had, and was asked for the session type, project, client and engineer - the room was only checked by
// Prepare Booking once every detail was in. This decides whether to check now; Early Room Check asks Room Availability
// (the date and the six days after, the requested hours or 8 AM - 10 PM), Early Room Result decides what to say, and Guard
// Probe says it. Never throws: on any doubt it does not check.
const item = Object.assign({}, $input.first().json);
const plan = { run: false, why: '' };
try {
  const g = $('Gate Context').first().json || {}, gate = g.gate || {};
  const bf = $('Booked For').first().json || {};
  const trig = $('Slack Trigger').first().json || {};
  const clean = s => String(s || '').replace(/\*sent using\*[\s\S]*$/i, '').trim();
  const t = clean(trig.text);
  const NAMES = $('All Rooms').all().map(i => String((((i.json || {}).fields || {})['Room Name']) || '').trim()).filter(Boolean);
  const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const roomsIn = s => {
    const hit = new Set(), x = String(s || ''); let m;
    const r1 = /\bstudio\s*([1-8a-fm])\b/gi; while ((m = r1.exec(x))) hit.add('Studio ' + m[1].toUpperCase());
    const r2 = /\bm[\s-]?booth\s*([1-8])\b|\bm-?([1-8])\b/gi; while ((m = r2.exec(x))) hit.add('M' + (m[1] || m[2]));
    const r3 = /\b(?:vocal\s+)?booth\s+([abd])\b/gi; while ((m = r3.exec(x))) hit.add('Studio ' + m[1].toUpperCase());
    for (const n of NAMES) if (!/^Studio\s|^M[1-8]$/i.test(n) && new RegExp('\\b' + esc(n) + '\\b', 'i').test(x)) hit.add(n);
    return [...hit].filter(n => NAMES.indexOf(n) !== -1);
  };
  const ctx = String(bf.requesterText || t);
  const skip = why => { plan.why = why; return true; };
  const dates = String(g.datesUnderDiscussion || '').split(',').map(x => x.trim()).filter(x => /^\d{4}-\d{2}-\d{2}$/.test(x));
  const saidDate = !!String(g.datesInMessage || '').trim();
  const saidTime = /\b\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.|nn)\b|\bnoon\b/i.test(t);
  const now = roomsIn(t);
  // this booking's messages, newest first: Jessie's own (to see what she has said), and the requester's latest room -
  // unless Jessie has named a different room since (an offer)
  let msgs = []; try { msgs = $('Get Recent Messages').all().map(i => (i && i.json) || {}); } catch (e) {}
  const isBot = m => Boolean(m.bot_id || (m.message && m.message.bot_id)) || m.subtype === 'bot_message';
  const epoch = parseFloat(String(g.epoch || '0')) || 0, tts = String(trig.ts || '');
  const botRooms = new Set(), botTexts = []; let n = 0, carried = '', found = false;
  for (const m of msgs) {
    if (++n > 25) break;
    if (tts && String(m.ts || '') === tts) continue;
    const x = clean(m.text || (m.message && m.message.text) || '');
    if (isBot(m)) {
      if (/^\s*\*?(?:booked\b|done\s*-|moved\b|cancell?ed\b)|has been booked/i.test(x)) break;
      botTexts.push(x); if (!found) roomsIn(x).forEach(r => botRooms.add(r)); continue;
    }
    const ts = parseFloat(String(m.ts || '0')) || 0;
    if ((epoch && ts && ts <= epoch) || /^reset$/i.test(x)) break;
    const r = roomsIn(x);
    if (!found && r.length) { found = true; if (r.length === 1 && ![...botRooms].some(b => b !== r[0])) carried = r[0]; }
    if (/\b(?:book|rebook)\b/i.test(x) && x.length > 20) break;
  }
  let room = '';
  if (g.confirmed || g.confirmedCancel || g.confirmedMove) skip('a yes');
  else if (gate.presentedCancel || gate.presentedMove) skip('answering a cancel or move card');
  else if (/\b(?:cancel|move|moving|moved|resched\w*|delete|remove)\b/i.test(t) || /\b(?:cancel|move|resched\w*)\b/i.test(ctx)) skip('a cancel or move');
  else if (/\b(?:every|weekly|daily|biweekly|fortnightly|recurring|series|weekdays)\b/i.test(t) || dates.length !== 1) skip('no single date');
  else if (/\b(?:free|available|availability|vacant|open)\b/i.test(t) && (/\?/.test(t) || /^\s*(?:is|are|any|which|what|check)\b/i.test(t))) skip('an availability question');
  else if (now.length > 1) skip('several rooms named');
  else if (now.length === 1) room = now[0];
  else if (saidDate || saidTime) { room = carried; if (!room) skip('no room for this booking'); }
  else skip('nothing new about the room, date or time');
  // said once per booking: a requester who still wants the room after being told goes on to the normal flow, where Book
  // Session decides (a priority request through the consent engine, or ROOM_OCCUPIED)
  if (room) {
    const lbl = new Date(dates[0] + 'T12:00:00+08:00').toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' });
    const told = new RegExp('^(?:you already have ' + esc(room) + ' booked|' + esc(room) + ' is already booked) on ' + esc(lbl) + '\\b', 'i');
    if (botTexts.some(x => told.test(x))) { room = ''; skip('already told this booking'); }
  }
  if (room) {
    const date = dates[0];
    const ts0 = String(bf.timeStart || ''), te0 = String(bf.timeEnd || '');
    const timed = /^\d{2}:\d{2}$/.test(ts0) && /^\d{2}:\d{2}$/.test(te0) && ts0 < te0;
    const last = new Date(Date.parse(date + 'T00:00:00Z') + 6 * 86400000).toISOString().slice(0, 10);
    // a session type the requester named (longest match), for ranking the alternatives
    let st = '';
    try { for (const i of $('All Session Types').all()) { const ty = String((((i.json || {}).fields || {}).Type) || '').trim();
      if (ty && ty.length > st.length && new RegExp('\\b' + esc(ty) + '\\b', 'i').test(ctx)) st = ty; } } catch (e) {}
    Object.assign(plan, { run: true, room, date, timed, timeStart: timed ? ts0 : '', timeEnd: timed ? te0 : '', sessionType: st,
      start_iso: date + 'T' + (timed ? ts0 : '08:00') + ':00+08:00', end_iso: last + 'T' + (timed ? te0 : '22:00') + ':00+08:00' });
  }
} catch (e) { plan.run = false; plan.why = 'error: ' + ((e && e.message) || e); }
item.earlyPlan = plan;
item.earlyRoomNotice = '';
return [{ json: item }];
"""

RESULT = r"""// v230 (QA B4): what the early room check found, for the prompt (earlyRoomNotice) and for Guard Probe (earlyRoom).
// Taken at the requested time, or all day when no time is known yet -> Guard Probe replaces the reply: taken, by whom,
// other rooms free then (the session type's ranking when one was named, else rooms of the same kind) and the room's next
// free days. Taken for part of the day with no time yet -> a heads-up line on top of the reply. Free -> carry on.
const base = Object.assign({}, $('Early Room Plan').first().json);
const P = base.earlyPlan || {};
let early = null, notice = '';
try {
  const r = $input.first().json || {};
  const me = String(($('Slack Trigger').first().json || {}).user || '');
  if (r.status === 'OK' && r.multi_day && Array.isArray(r.days) && r.days.length) {
    const d0 = r.days.find(d => d.date === P.date) || r.days[0];
    const a0 = (d0.rooms || []).find(x => x.room === P.room) || {};
    const hm = iso => new Date(iso).toLocaleTimeString('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' });
    const f12 = s => { let [h, m] = s.split(':').map(Number); const ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(m).padStart(2, '0') + ' ' + ap; };
    const when = d0.label + (P.timed ? ', ' + f12(P.timeStart) + ' – ' + f12(P.timeEnd) : '');
    if (a0.status === 'FREE') {
      early = { mode: 'free' };
      notice = 'ROOM CHECK (done by code this turn): ' + P.room + ' is free on ' + when + (P.timed ? '' : ' (8 AM – 10 PM)')
        + '. Carry on collecting the details; do not call Room Availability for it again.';
    } else if (a0.status === 'BUSY') {
      const evs = [].concat(a0.events || []);
      const own = evs.length > 0 && evs.every(e => e.ref && e.ref === me);
      const desc = evs.map(e => (e.allDay ? 'all day' : hm(e.start) + ' – ' + hm(e.end)) + ' (“' + e.title + '”)').join(' and ');
      // is the whole window taken? (always, with a time: the window is what was asked for)
      const ws = Date.parse(d0.window.start), we = Date.parse(d0.window.end);
      const iv = evs.map(e => [Math.max(Date.parse(e.start), ws), Math.min(Date.parse(e.end), we)]).filter(x => x[1] > x[0]).sort((x, y) => x[0] - y[0]);
      let at = ws; for (const x of iv) { if (x[0] > at) break; at = Math.max(at, x[1]); }
      // an M booth is only ever a heads-up: one with a standing hold is shared through the consent engine (Book Session)
      const covered = (P.timed || at >= we) && !/^M[1-8]$/.test(P.room);
      // alternatives: the session type's ranking when the room is in it, else rooms of the same kind (Room Type)
      const free = new Set([].concat(d0.free_rooms || [])); free.delete(P.room);
      let order = [];
      try {
        const REF = JSON.parse(String($('Room Table').first().json.referenceData || '{}'));
        const nameOf = {}; for (const x of (REF.rooms || [])) nameOf[x.id] = x.name;
        const ty = (REF.types || []).find(x => String(x.type || '').toLowerCase() === String(P.sessionType || '').toLowerCase());
        if (ty) { const rk = [].concat(ty.priority || [], ty.last || []).map(i => nameOf[i]).filter(Boolean); if (rk.indexOf(P.room) !== -1) order = rk; }
      } catch (e) {}
      if (!order.length) {
        const kinds = {}; for (const i of $('All Rooms').all()) { const f = (i.json || {}).fields || {}; if (f['Room Name']) kinds[String(f['Room Name']).trim()] = [].concat(f['Room Type'] || []).map(String); }
        const k0 = kinds[P.room] || [];
        const _sk = x => { const t = String(x).replace(/^Studio\s+/i, ''); return /^M[1-8]$/i.test(t) ? [2, +t.slice(1)] : /^\d+$/.test(t) ? [0, +t] : [1, t.charCodeAt(0)]; };
        const score = n => { const k = kinds[n] || []; const sh = k.filter(x => k0.indexOf(x) !== -1).length; return sh - 0.1 * (k.length - sh) - 0.1 * (k0.length - sh); };
        order = Object.keys(kinds).filter(n => n !== P.room && k0.length && (kinds[n] || [])[0] === k0[0])
          .sort((p, q) => score(q) - score(p) || _sk(p)[0] - _sk(q)[0] || _sk(p)[1] - _sk(q)[1]);
      }
      const alts = order.filter(n => free.has(n)).slice(0, 5);
      const days = r.days.filter(d => d !== d0 && ((d.rooms || []).find(x => x.room === P.room) || {}).status === 'FREE').slice(0, 3).map(d => d.label);
      if (covered) {
        const head = (own ? 'You already have ' + P.room + ' booked on ' : P.room + ' is already booked on ') + d0.label + ', ' + desc + '.';
        const opts = [];
        if (alts.length) opts.push((P.timed ? 'Free at that time: ' : 'Free that day: ') + alts.join(' · '));
        if (days.length) opts.push(P.room + ' is free ' + (P.timed ? 'at that time ' : '') + 'on ' + days.join(' · '));
        const text = head + '\n\n' + (opts.length ? opts.join('\n') + '\n\nWant one of those, or another day or time?'
          : 'Nothing like it is free then, and ' + P.room + ' is taken at that time all week. What other day or time works?');
        early = { mode: 'replace', text, own, room: P.room };
        notice = 'ROOM CHECK (done by code this turn - do not call Room Availability for it): ' + head + ' Your whole reply this turn is '
          + 'exactly this, and nothing else - do not ask for any other details yet:\n' + text;
      } else {
        const text = 'Heads up: ' + (own ? 'you already have ' + P.room + ' booked ' : P.room + ' is already booked ') + desc + ' on ' + d0.label + '.';
        early = { mode: 'prepend', text, own, room: P.room };
        notice = 'ROOM CHECK (done by code this turn): ' + text.replace(/^Heads up: /, '') + ' That line is added above your reply - do not '
          + 'repeat it. Carry on collecting the details' + (P.timed ? '.' : '; when you ask for the time, do not suggest those hours.');
      }
    }
  }
} catch (e) { early = null; notice = ''; }
base.earlyRoom = early;
base.earlyRoomNotice = notice;
return [{ json: base }];
"""

GP_ANCHOR = "// v194: a compact list of this turn's tool calls, for the Turn Log"
GP_BLOCK = r"""// v230 (QA B4, 7 Oct): the early room check. The room asked for is taken at the requested time (or all day) -> the reply is
// what Early Room Result wrote: taken, by whom, and other rooms or days. Taken for part of a day with no time yet -> its
// heads-up goes on top. A booking card is never touched (Book Session checked the room itself).
try {
  const _er = (($('Early Room Result').first() || {}).json || {}).earlyRoom;
  const _isCard = _prepared || /Book it\? Reply yes or no|Confirm to (?:book|move|cancel)|Cancel it\?|Move it\?|_check [0-9a-f]{8}_/i.test(text);
  if (_er && _er.text && !_isCard) {
    if (_er.mode === 'replace') text = String(_er.text);
    else if (_er.mode === 'prepend' && !/^\s*heads up:[^\n]*already (?:booked|have)/i.test(text)) text = String(_er.text) + '\n\n' + text;
  }
} catch (e) {}

"""
PROMPT_OLD = "{{ $('Room Table').first().json.consentNote }}"
PROMPT_NEW = "{{ $('Room Table').first().json.consentNote }}\n{{ $json.earlyRoomNotice || '' }}"

RA_INPUTS = ["start_iso", "end_iso", "session_type", "room", "reference_data", "scope"]
def main(w):
    w["name"] = "Project Jessie — v230 (early room check)"
    gp = node(w, "Guard Probe")["parameters"]; gp["jsCode"] = sub1(gp["jsCode"], GP_ANCHOR, GP_BLOCK + GP_ANCHOR, "gp")
    ag = node(w, "Jessie AI Agent")["parameters"]["options"]
    ag["systemMessage"] = sub1(ag["systemMessage"], PROMPT_OLD, PROMPT_NEW, "prompt")
    x, y = node(w, "Already Done?")["position"]
    plan = {"parameters": {"jsCode": PLAN}, "id": str(uuid.uuid4()), "name": "Early Room Plan", "type": "n8n-nodes-base.code",
            "typeVersion": 2, "position": [x + 200, y - 400], "onError": "continueRegularOutput"}
    iff = {"parameters": {"conditions": {"combinator": "and", "conditions": [{"id": str(uuid.uuid4()),
             "leftValue": "={{ (($json.earlyPlan || {}).run === true) ? 'yes' : 'no' }}",
             "operator": {"name": "filter.operator.equals", "operation": "equals", "type": "string"}, "rightValue": "yes"}],
             "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 3}}, "options": {}},
           "id": str(uuid.uuid4()), "name": "Early Room Check?", "type": "n8n-nodes-base.if", "typeVersion": 2.3, "position": [x + 400, y - 400]}
    vals = {"start_iso": "={{ $json.earlyPlan.start_iso }}", "end_iso": "={{ $json.earlyPlan.end_iso }}", "session_type": "",
            "room": "={{ $json.earlyPlan.room }}", "reference_data": "={{ $('Room Table').first().json.referenceData }}", "scope": "all"}
    call = {"parameters": {"workflowId": {"__rl": True, "cachedResultName": "Jessie — Room Availability", "cachedResultUrl": "/workflow/e7tBQB458nstrqei",
              "mode": "list", "value": "e7tBQB458nstrqei"},
            "workflowInputs": {"attemptToConvertTypes": False, "convertFieldsToString": False, "mappingMode": "defineBelow", "matchingColumns": [],
              "schema": [{"canBeUsedToMatch": True, "defaultMatch": False, "display": True, "displayName": k, "id": k, "required": False, "type": "string"} for k in RA_INPUTS],
              "value": vals}, "options": {}},
            "id": str(uuid.uuid4()), "name": "Early Room Check", "type": "n8n-nodes-base.executeWorkflow", "typeVersion": 1.2,
            "position": [x + 600, y - 500], "onError": "continueRegularOutput"}
    res = {"parameters": {"jsCode": RESULT}, "id": str(uuid.uuid4()), "name": "Early Room Result", "type": "n8n-nodes-base.code",
           "typeVersion": 2, "position": [x + 800, y - 500], "onError": "continueRegularOutput"}
    tv = node(w, "Guard Probe")["typeVersion"]; plan["typeVersion"] = tv; res["typeVersion"] = tv
    w["nodes"] += [plan, iff, call, res]
    C = w["connections"]
    ad = C["Already Done?"]["main"]
    if [o["node"] for o in ad[1]] != ["Jessie AI Agent"]: raise SystemExit("Already Done? false branch is not the agent")
    ad[1] = [{"node": "Early Room Plan", "type": "main", "index": 0}]
    agent = lambda: [{"node": "Jessie AI Agent", "type": "main", "index": 0}]
    C["Early Room Plan"] = {"main": [[{"node": "Early Room Check?", "type": "main", "index": 0}]]}
    C["Early Room Check?"] = {"main": [[{"node": "Early Room Check", "type": "main", "index": 0}], agent()]}
    C["Early Room Check"] = {"main": [[{"node": "Early Room Result", "type": "main", "index": 0}]]}
    C["Early Room Result"] = {"main": [agent()]}
    return w

if __name__ == "__main__":
    a = sys.argv[1:]
    json.dump(ra(json.load(open(a[0]))), open(a[1], "w"), indent=2, ensure_ascii=False); print("wrote", a[1])
    json.dump(main(json.load(open(a[2]))), open(a[3], "w"), indent=2, ensure_ascii=False); print("wrote", a[3])
