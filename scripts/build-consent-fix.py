#!/usr/bin/env python3
"""Consent engine rebuild (29 Sep review), from fresh pulls.

  scripts/build-consent-fix.py <pull-dir> <out-dir>

pull-dir: main.json, open.json, finalize.json, sweep.json, book.json, move.json (fresh `n8n pull`s).
Writes project-jessie-v176, open-consent-request-v11, finalize-consent-v10, consent-sweep-v2, book-session-v57,
move-booking-v25.

One writer. main and Move only RECORD a decision on the row (Decision / Decision At). Consent Sweep, once a minute,
hands at most ONE due row to Finalize, which re-reads the row and is the only thing that changes Status, the hold or
the requester's booking. No lock is claimed: Sheets cannot do one, Google does not guarantee event-id collision
detection, and the n8n Data Table upsert is unverified. Two Finalize runs can only overlap if one run takes longer
than the minute between sweeps.

New Consent Requests columns (setup): Decision, Decision At, Stage, Hold Snapshot, Placement Event Id.
"""
import copy, json, os, sys, uuid

def load(d, k): return json.load(open(os.path.join(d, k + ".json")))
def node(w, n): return next(x for x in w["nodes"] if x["name"] == n)
def uid(): return str(uuid.uuid4())
def link(C, a, b, br=0):
    arr = C.setdefault(a, {}).setdefault("main", [])
    while len(arr) <= br: arr.append([])
    arr[br].append({"node": b, "type": "main", "index": 0})
def sub1(s, old, new, label):
    if s.count(old) != 1: raise SystemExit(f"{label}: expected 1 match, found {s.count(old)}")
    return s.replace(old, new)
def code(name, js, pos):
    return {"parameters": {"mode": "runOnceForAllItems", "jsCode": js}, "id": uid(), "name": name, "position": pos,
            "type": "n8n-nodes-base.code", "typeVersion": 2}
def ifeq(tmpl, name, left, right, pos):
    n = copy.deepcopy(tmpl); n["id"] = uid(); n["name"] = name; n["position"] = pos
    c = n["parameters"]["conditions"]["conditions"][0]
    c["id"] = uid(); c["leftValue"] = left; c["rightValue"] = right
    c["operator"] = {"name": "filter.operator.equals", "operation": "equals", "type": "string"}
    n["parameters"]["conditions"]["conditions"] = [c]
    return n
def clone(tmpl, name, pos, **over):
    n = copy.deepcopy(tmpl); n["id"] = uid(); n["name"] = name; n["position"] = pos
    for k in ("webhookId",):
        if k in n: n[k] = uid()
    n.update(over); return n

# Short request code shown in consent DMs; the reply router binds a "yes"/"no" to the request whose code Jessie
# last showed. Same function in Open Consent Request and main.
CODEFN = r"""function consentCode(id) { let h = 0; for (const c of String(id || '')) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  const A = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; let s = ''; for (let i = 0; i < 4; i++) { s += A[h % 32]; h = Math.floor(h / 32); } return s; }"""
WHENFN = r"""function whenPhrase(s,e){try{if(/^\d{4}-\d{2}-\d{2}$/.test(String(s||''))){return new Date(s+'T00:00:00+08:00').toLocaleDateString('en-US',{timeZone:'Asia/Manila',month:'short',day:'numeric'})+' (all day)';}const o={timeZone:'Asia/Manila',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'};const a=new Date(s).toLocaleString('en-US',o);const b=e?new Date(e).toLocaleTimeString('en-US',{timeZone:'Asia/Manila',hour:'numeric',minute:'2-digit'}):'';return b?(a+'–'+b):a;}catch(_){return String(s||'');}}"""

# ---------------------------------------------------------------- main: Consent Router
ROUTER = r"""// Consent-reply router (main v176, review 29 Sep). A reply DECIDES a consent request only when it is an
// unambiguous yes or no AND it is tied to that request: it carries the request's code, or Jessie's last message in
// this DM was that request's prompt. It used to approve on the first word ("yes but only after 5pm", "no problem"
// rejected), pick the newest pending row, and a "yes" to the holder's own booking summary approved the consent.
// A decision is only RECORDED here; Consent Sweep -> Finalize carries it out (one writer).
const rows = $('Read Pending Consent').all().map(i => (i && i.json) || {});
const trig = $('Slack Trigger').first().json || {};
const sender = String(trig.user || '');
const senderJson = ($('Get Sender').first().json) || {};
let hist = []; try { hist = $('Consent History').all().map(i => (i && i.json) || {}); } catch (e) { hist = []; }
""" + CODEFN + "\n" + WHENFN + r"""
const U = s => String(s || '').toUpperCase();
const mine = rows.filter(r => U(r['Status']) === 'PENDING' && String(r['Approver'] || '') === sender && r['Request ID']);
const norm = s => String(s || '').toLowerCase().replace(/:\+1:|:thumbsup:|\u{1F44D}/gu, ' yes ').replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
const raw = String(trig.text || '');
const inText = U(raw).match(/\b[A-Z2-9]{4}\b/g) || [];
let bound = mine.find(r => inText.indexOf(consentCode(r['Request ID'])) !== -1) || null;
let text = norm(raw);
if (bound) text = text.replace(new RegExp('\\b' + consentCode(bound['Request ID']).toLowerCase() + '\\b', 'g'), ' ').replace(/\b(request|ref)\b/g, ' ').replace(/\s+/g, ' ').trim();
if (!bound) {
  const lastBot = hist.find(m => m && (m.bot_id || m.subtype === 'bot_message'));
  const mm = lastBot && String(lastBot.text || '').match(/\(request ([A-Z2-9]{4})\)/);
  if (mm) bound = mine.find(r => consentCode(r['Request ID']) === mm[1]) || null;
}
const APPROVE = new Set(['yes','y','yep','yup','yeah','ok','okay','k','sure','go','go ahead','yes go ahead','ok go ahead','yes please',
  'please do','approve','approved','confirm','confirmed','yes ok','ok sure','sure go ahead','yes sure','sure thing','go for it',
  'yes go for it','fine','thats fine','yes thats fine','yes you can','they can','yes they can','allowed','yes allowed']);
const REJECT = new Set(['no','n','nope','no thanks','no thank you','deny','denied','reject','rejected','decline','declined','not ok',
  'not okay','sorry no','no sorry','i need it','they cant','no they cant','no i need it']);
const LOOKS = /\b(yes|yeah|yep|ok|okay|sure|no|nope|not|but|only|after|before|until|unless|actually|maybe|problem|worries|approve|decline|reject|go)\b/;
function classify(t) { if (!t) return 'none'; if (APPROVE.has(t)) return 'approve'; if (REJECT.has(t)) return 'reject';
  return (t.split(' ').length <= 14 && LOOKS.test(t)) ? 'ambiguous' : 'none'; }
const c = classify(text);
let branch = 'normal', decision = '', reply = '', matched = {}, consentContext = '';
const ctx = r => { const who = r['Approver Name'] || 'this booker', title = r['Incumbent Title'] || 'their booking', rm = r['Room/Booth'] || 'a room', reqName = r['Requester Name'] || 'a higher-priority booking';
  return 'CONSENT CONTEXT: You earlier asked ' + who + ' to move "' + title + '" out of ' + rm + ' to free it for ' + reqName + ', which outranks it. They are replying now. If they give a new time or room, move "' + title + '" there via the normal Move flow - present the move summary and confirm as usual. Do NOT book ' + reqName + ' yourself; that happens automatically once "' + title + '" moves and frees the room. If they decline, tell ' + reqName + ' it stays taken.'; };
if (trig.bot_id) { branch = 'ignore'; }
else if (bound) {
  matched = bound;
  const code = consentCode(bound['Request ID']), room = bound['Room/Booth'] || 'the booth', who = bound['Requester Name'] || 'them',
        when = whenPhrase(bound['Req Start'], bound['Req End']);
  if (U(bound['Kind']) === 'MBOOTH') {
    if (c === 'approve') { branch = 'decide'; decision = 'APPROVED'; reply = "Thanks! I'll book " + room + ' for ' + who + ' (' + when + ') and let them know.'; }
    else if (c === 'reject') { branch = 'decide'; decision = 'REJECTED'; reply = 'Okay, ' + room + ' stays yours on ' + when + ". I'll let " + who + ' know.'; }
    else if (c === 'ambiguous') { branch = 'clarify'; reply = 'Just to check: can ' + who + ' use ' + room + ' on ' + when + '? Please reply yes or no. (request ' + code + ')'; }
  } else {
    if (c === 'reject') { branch = 'decide'; decision = 'REJECTED'; reply = 'Okay, "' + (bound['Incumbent Title'] || 'your booking') + "\" stays where it is. I'll let " + who + ' know.'; }
    else { branch = 'consent-help'; consentContext = ctx(bound); }
  }
} else {
  // Not tied to one request: a bare "yes" belongs to whatever Jessie last asked, so it is NOT taken as consent.
  const pre = mine.filter(r => U(r['Kind']) !== 'MBOOTH');
  if (pre.length) { branch = 'consent-help'; consentContext = pre.map(ctx).join('\n'); }
}
return [{ json: Object.assign({}, senderJson, { _consentBranch: branch, _consentDecision: decision, _consentReply: reply,
  _consentContext: consentContext, _matched: matched, _consentClass: c }) }];"""

CONSENT_CHECK = r"""// Consent Check (main v176): does the sender have a PENDING consent request to answer? Only then is Slack history
// read, to see whether Jessie's last message in this DM was that request's prompt.
const sender = String(($('Slack Trigger').first().json || {}).user || '');
const any = $input.all().some(i => { const r = (i && i.json) || {}; return String(r['Status'] || '').toUpperCase() === 'PENDING' && String(r['Approver'] || '') === sender; });
return [{ json: { needHistory: any ? 'yes' : 'no' } }];"""

DECISION_ROW = r"""const m = $('Consent Router').first().json;
return [{ json: { 'Request ID': (m._matched || {})['Request ID'] || '', 'Decision': m._consentDecision, 'Decision At': new Date().toISOString() } }];"""
DECISION_REPLY = r"""// The decision is on the row; Consent Sweep carries it out within a minute.
const w = $input.first().json || {};
const m = $('Consent Router').first().json;
return [{ json: { output: w.error ? "Sorry, I couldn't record that just now. Please reply again in a minute." : m._consentReply } }];"""
CLARIFY_REPLY = r"""return [{ json: { output: $('Consent Router').first().json._consentReply } }];"""

def build_main(w):
    N = {n["name"]: n for n in w["nodes"]}
    w["name"] = "Project Jessie — v176 (consent replies)"
    tmpl_if = N["MBooth Book?"]; tmpl_sheet = None
    for n in w["nodes"]:
        if n["name"] == "Mark Rejected": tmpl_sheet = n
    x0, y0 = N["Read Pending Consent"]["position"]
    drop = ["MBooth Book?", "Call Finalize MBOOTH", "Consent Reject?", "Reject Row", "Mark Rejected", "Notify Requester", "Reply Incumbent"]
    w["nodes"] = [n for n in w["nodes"] if n["name"] not in drop]
    for d in drop: w["connections"].pop(d, None)
    N["Consent Router"]["parameters"]["jsCode"] = ROUTER
    hist = clone(N["Get Recent Messages"], "Consent History", [x0 + 224, y0 - 144]); hist["parameters"]["limit"] = 5; hist["executeOnce"] = True
    rec = clone(tmpl_sheet, "Record Decision", [x0 + 1120, y0 - 144]); rec["onError"] = "continueRegularOutput"
    new = [code("Consent Check", CONSENT_CHECK, [x0 + 112, y0 + 96]),
           ifeq(tmpl_if, "Consent History?", "={{ $json.needHistory }}", "yes", [x0 + 176, y0]),
           hist,
           ifeq(tmpl_if, "Consent Decide?", "={{ $json._consentBranch }}", "decide", [x0 + 672, y0]),
           code("Decision Row", DECISION_ROW, [x0 + 896, y0 - 144]), rec,
           code("Decision Reply", DECISION_REPLY, [x0 + 1344, y0 - 144]),
           ifeq(tmpl_if, "Consent Clarify?", "={{ $json._consentBranch }}", "clarify", [x0 + 896, y0 + 96]),
           code("Clarify Reply", CLARIFY_REPLY, [x0 + 1120, y0 + 16])]
    w["nodes"].extend(new)
    N["Consent Router"]["position"] = [x0 + 448, y0]
    C = w["connections"]
    C["Read Pending Consent"] = {"main": [[{"node": "Consent Check", "type": "main", "index": 0}]]}
    link(C, "Consent Check", "Consent History?")
    link(C, "Consent History?", "Consent History", 0); link(C, "Consent History?", "Consent Router", 1)
    link(C, "Consent History", "Consent Router")
    C["Consent Router"] = {"main": [[{"node": "Consent Decide?", "type": "main", "index": 0}]]}
    link(C, "Consent Decide?", "Decision Row", 0); link(C, "Consent Decide?", "Consent Clarify?", 1)
    link(C, "Decision Row", "Record Decision"); link(C, "Record Decision", "Decision Reply"); link(C, "Decision Reply", "Send Reply")
    link(C, "Consent Clarify?", "Clarify Reply", 0); link(C, "Consent Clarify?", "Read Reference Cache", 1)
    link(C, "Clarify Reply", "Send Reply")
    return w

# ---------------------------------------------------------------- Open Consent Request: request code in the DMs
def build_open(w):
    w["name"] = "Jessie — Open Consent Request — v11"
    n = node(w, "Build Messages"); c = n["parameters"]["jsCode"]
    marker = "if(isMB){"
    c = sub1(c, marker, CODEFN + "\n// v11: the request code lets the holder's yes / no be tied to THIS request (main Consent Router).\n"
                        "const _code = consentCode(R['Request ID']);\n" + marker, "open code")
    c = sub1(c, "OK to let them use it this once? Reply here with yes or no.`;",
             "OK to let them use it this once? Reply here with yes or no. (request ${_code})`;", "open mb dm")
    i = c.index("} else {", c.index("if(isMB){"))
    j = c.index("incumbentDM = `", i); k = c.index("`;", j)
    c = c[:k] + " (request ${_code})" + c[k:]
    n["parameters"]["jsCode"] = c
    return w

# ---------------------------------------------------------------- Finalize Consent: the one writer
PLAN = r"""// Finalize Plan (v10, review 29 Sep). Re-reads the row by Request ID and decides from ITS state, never from what
// the caller passed. Only Consent Sweep calls this, one row at a time. Stages persist progress so a run that dies
// half-way is finished (or safely unwound) by the next sweep:
//   '' -> HOLD_SNAPSHOT (hold copied to the row) -> HOLD_DELETED -> PLACING -> PLACED -> Status DONE
""" + WHENFN + r"""
const IN = $('When Executed by Another Workflow').first().json || {};
const id = String(IN.request_id || '').trim();
const U = s => String(s || '').toUpperCase().trim();
const rows = $('Read Rows').all().map(i => (i && i.json) || {}).filter(r => String(r['Request ID'] || '').trim() === id && id);
const out = o => [{ json: Object.assign({ requestId: id }, o) }];
if (!id) return out({ route: 'outcome', outcome: 'skip', reason: 'NO_REQUEST_ID' });
if (rows.length !== 1) return out({ route: 'outcome', outcome: 'skip', reason: rows.length ? 'DUPLICATE_ROWS' : 'NOT_FOUND' });
const row = rows[0];
if (U(row['Status']) !== 'PENDING') return out({ route: 'outcome', outcome: 'skip', reason: 'ALREADY_' + U(row['Status']) });
const kind = U(row['Kind']) || 'PREEMPT', stage = U(row['Stage']), decision = U(row['Decision']);
const dl = Date.parse(row['Deadline'] || ''), due = isFinite(dl) && Date.now() >= dl;
const holdId = String(row['Incumbent Event Id'] || '').trim();
const via = decision === 'APPROVED' ? 'mbooth-approve' : decision === 'INCUMBENT_MOVED' ? 'move-hook' : 'sweep-timeout';
const base = { kind, stage, via, holdId, room: row['Room/Booth'] || '', reqStart: row['Req Start'] || '', reqEnd: row['Req End'] || '',
  approver: row['Approver'] || '', approverName: row['Approver Name'] || 'the holder', requester: row['Requester'] || '',
  requesterName: row['Requester Name'] || 'the requester', incTitle: row['Incumbent Title'] || '', when: whenPhrase(row['Req Start'], row['Req End']),
  hadSnapshot: !!String(row['Hold Snapshot'] || '').trim() };
if (stage === 'RESTORE_FAILED') return out(Object.assign(base, { route: 'outcome', outcome: 'skip', reason: 'NEEDS_A_PERSON' }));
if (stage === 'PLACED') return out(Object.assign(base, { route: 'outcome', outcome: 'finish', placementId: row['Placement Event Id'] || '' }));
let route;
if (stage === 'HOLD_SNAPSHOT' || stage === 'HOLD_DELETED') route = 'hold';
else if (stage === 'PLACING') route = 'place';
else if (decision === 'REJECTED') return out(Object.assign(base, { route: 'outcome', outcome: 'reject' }));
else if (kind === 'MBOOTH') { if (decision !== 'APPROVED' && !due) return out(Object.assign(base, { route: 'outcome', outcome: 'skip', reason: 'NOT_DUE' })); route = holdId ? 'hold' : 'place'; }
else { if (decision === 'INCUMBENT_MOVED') route = 'place';
       else if (due) return out(Object.assign(base, { route: 'outcome', outcome: 'expire' }));   // PREEMPT timeout: nobody is moved
       else return out(Object.assign(base, { route: 'outcome', outcome: 'skip', reason: 'NOT_DUE' })); }
function safeParse(s) { if (s && typeof s === 'object') return s; try { return JSON.parse(s || ''); } catch (_) { return null; } }
const req = safeParse(row['Req Payload']);
if (!row['Req Start'] || !row['Req End'] || !row['Room/Booth'] || !req) return out(Object.assign(base, { route: 'outcome', outcome: 'fail', reason: 'MISSING_REQ_DETAILS' }));
const dateOf = iso => { try { return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(iso)); } catch (_) { return ''; } };
const placeTarget = req.kind === 'move' ? 'move' : 'book';
// The marker lets a retry recognise a placement that already went through (Book Session hands it back on a clash).
const mark = ' | consent: ' + id;
const placePayload = placeTarget === 'move'
  ? { title: req.title || '', event_id: req.event_id || '', booking_date: req.booking_date || dateOf(row['Req Start']), new_start_iso: req.new_start_iso || row['Req Start'],
      new_end_iso: req.new_end_iso || row['Req End'], new_rooms: req.new_rooms || row['Room/Booth'] || '', requester: req.requester || row['Requester'] || '',
      requester_name: req.requester_name || row['Requester Name'] || '' }
  : Object.assign({}, req, { rooms: req.rooms || row['Room/Booth'] || '', start_iso: req.start_iso || row['Req Start'], end_iso: req.end_iso || row['Req End'],
      description: String(req.description || '').indexOf('consent: ' + id) === -1 ? String(req.description || '') + mark : String(req.description || ''),
      // Exactly the approved hold may be ignored, and only because it is being released for this booking.
      exclude_event_id: kind === 'MBOOTH' ? holdId : '' });
return out(Object.assign(base, { route, placeTarget, placePayload,
  weDeleted: stage === 'HOLD_DELETED' || ((stage === 'HOLD_SNAPSHOT' || stage === 'PLACING') && base.hadSnapshot) }));"""

CHECK_HOLD = r"""// Check Hold: what is the approved hold's state right now? Only a confirmed instance in the requested booth and
// window is deleted; a hold that has changed is left alone and the request fails with nothing changed.
const P = $('Plan').first().json;
const g = $input.first().json || {};
const errTxt = g.error ? JSON.stringify(g.error) : '';
const gone = g.status === 'cancelled' || /\b(404|410)\b|not ?found|deleted|gone/i.test(errTxt);
if (!g.id && !gone) return [{ json: { next: 'outcome', outcome: 'retry', reason: 'HOLD_READ_FAILED' } }];
if (gone) return [{ json: { next: 'place', weDeleted: !!P.weDeleted, reason: P.weDeleted ? 'HOLD_ALREADY_DELETED_BY_US' : 'HOLD_ALREADY_GONE' } }];
const room = String(P.room || '').toLowerCase();
const inRoom = (g.attendees || []).some(a => String(a.displayName || '').toLowerCase().indexOf(room) !== -1) || String(g.location || '').toLowerCase().indexOf(room) !== -1 || String(g.summary || '').toLowerCase().indexOf(room) === 0;
const ms = v => { const s = String(v || ''); return /^\d{4}-\d{2}-\d{2}$/.test(s) ? Date.parse(s + 'T00:00:00+08:00') : Date.parse(s); };
const hs = ms(g.start && (g.start.dateTime || g.start.date)), he = ms(g.end && (g.end.dateTime || g.end.date));
const overlaps = hs < ms(P.reqEnd) && he > ms(P.reqStart);
if (!inRoom || !overlaps) return [{ json: { next: 'outcome', outcome: 'fail', reason: 'HOLD_CHANGED' } }];
const snap = { id: g.id, recurringEventId: g.recurringEventId || '', summary: g.summary || '', start: g.start, end: g.end,
  location: g.location || '', description: g.description || '', attendees: (g.attendees || []).map(a => ({ email: a.email, resource: !!a.resource })), status: g.status };
return [{ json: { next: 'delete', snapshot: snap } }];"""
SNAP_ROW = r"""const P = $('Plan').first().json;
return [{ json: { 'Request ID': P.requestId, 'Stage': 'HOLD_SNAPSHOT', 'Hold Snapshot': JSON.stringify($('Check Hold').first().json.snapshot) } }];"""
CHECK_DELETE = r"""// Check Delete: re-read the hold after DELETE. Deleted -> place. Still there -> the delete failed and nothing changed
// (verified). Unreadable -> leave it for the next sweep, which re-reads the hold before doing anything.
const g = $input.first().json || {};
const errTxt = g.error ? JSON.stringify(g.error) : '';
if (g.status === 'cancelled' || /\b(404|410)\b|not ?found|deleted|gone/i.test(errTxt)) return [{ json: { next: 'place' } }];
if (g.id && g.status && g.status !== 'cancelled') return [{ json: { next: 'outcome', outcome: 'fail', reason: 'DELETE_FAILED' } }];
return [{ json: { next: 'outcome', outcome: 'retry', reason: 'DELETE_UNVERIFIED' } }];"""
STAGE_ROW = lambda st: ("return [{ json: { 'Request ID': $('Plan').first().json.requestId, 'Stage': '" + st + "' } }];")
CHECK_PLACED = r"""// Check Placed: did the requester's booking go in? CREATED / MOVED, or Book Session reports a clash with OUR earlier
// placement (the consent marker) - a retry after a run that died after booking. A call that errored is uncertain:
// left at PLACING for the next sweep, whose attempt either finds our booking or fails cleanly.
const P = $('Plan').first().json;
const r = $input.first().json || {};
const ran = n => { try { $(n).first(); return true; } catch (e) { return false; } };
const weDeleted = !!P.weDeleted || ran('Check Delete') || (ran('Check Hold') && !!$('Check Hold').first().json.weDeleted);
const st = String(r.status || '').toUpperCase();
if (st === 'CREATED' || st === 'MOVED' || r.consent_placed_id) return [{ json: { next: 'placed', weDeleted, placementId: r.event_id || r.new_event_id || r.consent_placed_id || '' } }];
if (r.error || !st) return [{ json: { next: 'outcome', outcome: 'retry', weDeleted, reason: 'PLACEMENT_UNCERTAIN' } }];
return [{ json: { next: weDeleted ? 'restore' : 'outcome', outcome: 'fail', weDeleted, reason: 'PLACE_FAILED:' + (r.reason || st) } }];"""
PLACED_ROW = r"""return [{ json: { 'Request ID': $('Plan').first().json.requestId, 'Stage': 'PLACED', 'Placement Event Id': $('Check Placed').first().json.placementId || '' } }];"""
OUTCOME = r"""// Outcome: the one place a request's final state and messages are decided. Nothing reports success, or "nothing
// changed", unless that is what the calendar showed. A timeout says it went ahead under the timeout rule.
const P = $('Plan').first().json;
const ran = n => { try { $(n).first(); return true; } catch (e) { return false; } };
const j = n => ran(n) ? ($(n).first().json || {}) : null;
const now = new Date().toISOString();
const mb = P.kind === 'MBOOTH', to = P.via === 'sweep-timeout';
const APPROVALS = 'C0C34UMFXGD';
let fin = null, msgs = [];
const dm = (to_, text) => { if (to_) msgs.push({ to: to_, text }); };
const done = () => {
  fin = { 'Status': 'DONE', 'Resolved Via': P.via, 'Decided At': now, 'Stage': 'PLACED' };
  if (mb && to) {
    dm(P.requester, 'Done - ' + P.room + ' is yours for ' + P.when + '. ' + P.approverName + " didn't reply by the deadline, so it went ahead under the M-booth sharing rule.");
    dm(P.approver, 'No reply came in by the deadline, so under the M-booth sharing rule ' + P.requesterName + ' now has ' + P.room + ' for ' + P.when + ' and your booking for that time was released.');
  } else if (mb) {
    dm(P.requester, 'Done - ' + P.room + ' is yours for ' + P.when + '. ' + P.approverName + " OK'd sharing the booth.");
    dm(P.approver, "You've offered your " + P.room + ' booth (' + P.when + ') to ' + P.requesterName + '. Thanks for sharing!');
  } else {
    dm(P.requester, 'Done - ' + P.room + ' is yours for ' + P.when + '. ' + P.approverName + ' moved their session to make way.');
    dm(P.approver, 'Heads up - your "' + P.incTitle + '" was moved to make room for a higher-priority session in ' + P.room + ", as you OK'd. Thanks!");
  }
};
const failNothing = reason => { fin = { 'Status': 'FAILED', 'Resolved Via': reason, 'Decided At': now };
  dm(P.requester, "I couldn't get " + (P.room || 'that room') + ' for you just now (' + P.when + '). Nothing was changed - please try another time or room.'); };
if (P.route === 'outcome') {
  if (P.outcome === 'reject') { fin = { 'Status': 'REJECTED', 'Resolved Via': 'reply-no', 'Decided At': now };
    dm(P.requester, mb ? (P.approverName + ' would rather keep ' + P.room + ' on ' + P.when + ', so it stays theirs. Want another booth or time?')
                       : (P.approverName + " can't move their session, so " + P.room + ' stays taken for ' + P.when + '. Want another time or room?')); }
  else if (P.outcome === 'expire') fin = { 'Status': 'EXPIRED', 'Resolved Via': 'sweep-expired', 'Decided At': now };
  else if (P.outcome === 'finish') done();
  else if (P.outcome === 'fail') failNothing(P.reason);
} else if (ran('Check Placed')) {
  const cp = j('Check Placed');
  if (cp.next === 'placed') done();
  else if (cp.next === 'restore') {
    const rr = j('Recheck Restore') || {};
    if (rr.status === 'confirmed') {
      fin = { 'Status': 'FAILED', 'Resolved Via': cp.reason, 'Decided At': now, 'Stage': 'RESTORED' };
      dm(P.requester, "I couldn't book " + P.room + ' for you just now (' + P.when + '), so ' + P.approverName + "'s booking is back as it was. Please try another time or booth.");
      dm(P.approver, "That didn't go through, so your " + P.room + ' booking for ' + P.when + ' is back as it was.');
    } else {
      fin = { 'Status': 'NEEDS_ATTENTION', 'Resolved Via': cp.reason + '; RESTORE_FAILED', 'Decided At': now, 'Stage': 'RESTORE_FAILED' };
      dm(P.requester, 'Something went wrong booking ' + P.room + ' for you (' + P.when + ') and I could not confirm ' + P.approverName + "'s booking is back. The team has been alerted and will sort it out.");
      dm(P.approver, 'Something went wrong while sharing your ' + P.room + ' booth for ' + P.when + '. The team has been alerted to check your booking.');
      msgs.push({ to: APPROVALS, text: '[CONSENT NEEDS ATTENTION] ' + P.requestId + ': the hold ' + P.holdId + ' was deleted, the booking failed (' + cp.reason + ') and restoring the hold failed. Its details are in the Hold Snapshot column.' });
    }
  } else if (cp.outcome === 'fail') failNothing(cp.reason);
} else {
  const cd = j('Check Delete'), ch = j('Check Hold');
  const x = cd || ch || {};
  if (x.outcome === 'fail') failNothing(x.reason);
}
return [{ json: { fin, msgs } }];"""
OUTCOME_ROW = r"""const o = $('Outcome').first().json;
if (!o.fin) return [];      // retry / not due: the row stays as it is for the next sweep
return [{ json: Object.assign({ 'Request ID': $('Plan').first().json.requestId }, o.fin) }];"""
OUTCOME_MSGS = r"""// Messages go out only once the outcome is on the row; if the write failed the next sweep redoes the outcome.
const w = $input.first().json || {};
if (w.error) return [];
return ($('Outcome').first().json.msgs || []).map(m => ({ json: m }));"""
RETURN = r"""const o = (() => { try { return $('Outcome').first().json; } catch (e) { return {}; } })();
return [{ json: { request_id: $('Plan').first().json.requestId, status: (o.fin || {}).Status || 'UNCHANGED' } }];"""

def build_finalize(w):
    N = {n["name"]: n for n in w["nodes"]}
    w["name"] = "Jessie — Finalize Consent — v10"
    trig = N["When Executed by Another Workflow"]
    trig["parameters"] = {"workflowInputs": {"values": [{"name": "request_id"}]}}
    sweep_read = None
    t_http = N["Cancel Hold"]; t_sheet = N["Mark Done"]; t_slack = N["Notify Incumbent"]
    t_if = N["Place Kind?"]; book = N["Book Requester"]; move = N["Move Requester"]
    keep = {"When Executed by Another Workflow", "Place Kind?", "Book Requester", "Move Requester"}
    notes = [n for n in w["nodes"] if n["type"].endswith("stickyNote")]
    w["nodes"] = [n for n in w["nodes"] if n["name"] in keep] + notes
    book["onError"] = "continueRegularOutput"; move["onError"] = "continueRegularOutput"
    bv = book["parameters"]["workflowInputs"]["value"]
    bv["exclude_event_id"] = "={{ $('Plan').first().json.placePayload.exclude_event_id }}"
    return w, dict(t_http=t_http, t_sheet=t_sheet, t_slack=t_slack, t_if=t_if, trig=trig, book=book, move=move)

def finish_finalize(w, T, t_read):
    url = "=https://www.googleapis.com/calendar/v3/calendars/{{ encodeURIComponent('c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com') }}/events/{{ encodeURIComponent($('Plan').first().json.holdId) }}"
    def http(name, method, pos, body=None):
        n = clone(T["t_http"], name, pos); p = {"url": url, "authentication": "predefinedCredentialType", "nodeCredentialType": "googleCalendarOAuth2Api", "options": {}}
        if method != "GET": p["method"] = method
        if body: p.update({"sendBody": True, "specifyBody": "json", "jsonBody": body})
        n["parameters"] = p; n["onError"] = "continueRegularOutput"; n["alwaysOutputData"] = True; return n
    def sheet(name, pos, onerr=None):
        n = clone(T["t_sheet"], name, pos)
        if onerr: n["onError"] = onerr
        else: n.pop("onError", None)
        return n
    X = 0; Y = 0
    P = lambda cx, cy: [cx * 224, cy * 176]
    read = clone(t_read, "Read Rows", P(1, 0)); read["alwaysOutputData"] = True; read.pop("onError", None)
    T["trig"]["position"] = P(0, 0)
    nodes = [read, code("Plan", PLAN, P(2, 0)),
             ifeq(T["t_if"], "Hold?", "={{ $json.route }}", "hold", P(3, 0)),
             ifeq(T["t_if"], "Place?", "={{ $('Plan').first().json.route }}", "place", P(4, 1)),
             http("Get Hold", "GET", P(4, -1)), code("Check Hold", CHECK_HOLD, P(5, -1)),
             ifeq(T["t_if"], "Delete Hold?", "={{ $json.next }}", "delete", P(6, -1)),
             ifeq(T["t_if"], "Place After Check?", "={{ $('Check Hold').first().json.next }}", "place", P(7, 0)),
             code("Snapshot Row", SNAP_ROW, P(7, -2)), sheet("Write Snapshot", P(8, -2)),
             http("Delete Hold", "DELETE", P(9, -2)), http("Recheck Hold", "GET", P(10, -2)),
             code("Check Delete", CHECK_DELETE, P(11, -2)),
             ifeq(T["t_if"], "Deleted?", "={{ $json.next }}", "place", P(12, -2)),
             code("Deleted Row", STAGE_ROW("HOLD_DELETED"), P(13, -2)), sheet("Write Deleted", P(14, -2), "continueRegularOutput"),
             code("Placing Row", STAGE_ROW("PLACING"), P(15, 0)), sheet("Write Placing", P(16, 0), "continueRegularOutput"),
             code("Check Placed", CHECK_PLACED, P(19, 0)),
             ifeq(T["t_if"], "Placed?", "={{ $json.next }}", "placed", P(20, 0)),
             code("Placed Row", PLACED_ROW, P(21, -1)), sheet("Write Placed", P(22, -1), "continueRegularOutput"),
             ifeq(T["t_if"], "Restore?", "={{ $('Check Placed').first().json.next }}", "restore", P(21, 1)),
             http("Restore Hold", "PATCH", P(22, 1), "={{ JSON.stringify({ status: 'confirmed' }) }}"),
             http("Recheck Restore", "GET", P(23, 1)),
             code("Outcome", OUTCOME, P(24, 0)), code("Outcome Row", OUTCOME_ROW, P(25, 0)),
             sheet("Write Outcome", P(26, 0), "continueRegularOutput"), code("Outcome Messages", OUTCOME_MSGS, P(27, 0))]
    msg = clone(T["t_slack"], "Send Message", P(28, 0))
    msg["parameters"] = {"select": "channel", "channelId": {"__rl": True, "mode": "id", "value": "={{ $json.to }}"},
                         "text": "={{ $json.text }}", "otherOptions": {"includeLinkToWorkflow": False}}
    msg["onError"] = "continueRegularOutput"
    ret = code("Return", RETURN, P(29, 0)); ret["executeOnce"] = True
    nodes += [msg, ret]
    T["t_if"]["name"] = "Place Kind?"; T["t_if"]["position"] = P(17, 0)
    T["move"]["position"] = P(18, -1); T["book"]["position"] = P(18, 1)
    w["nodes"].extend(nodes)
    C = {}
    L = lambda a, b, br=0: link(C, a, b, br)
    L("When Executed by Another Workflow", "Read Rows"); L("Read Rows", "Plan"); L("Plan", "Hold?")
    L("Hold?", "Get Hold", 0); L("Hold?", "Place?", 1)
    L("Place?", "Placing Row", 0); L("Place?", "Outcome", 1)
    L("Get Hold", "Check Hold"); L("Check Hold", "Delete Hold?")
    L("Delete Hold?", "Snapshot Row", 0); L("Delete Hold?", "Place After Check?", 1)
    L("Place After Check?", "Placing Row", 0); L("Place After Check?", "Outcome", 1)
    L("Snapshot Row", "Write Snapshot"); L("Write Snapshot", "Delete Hold"); L("Delete Hold", "Recheck Hold"); L("Recheck Hold", "Check Delete")
    L("Check Delete", "Deleted?"); L("Deleted?", "Deleted Row", 0); L("Deleted?", "Outcome", 1)
    L("Deleted Row", "Write Deleted"); L("Write Deleted", "Placing Row")
    L("Placing Row", "Write Placing"); L("Write Placing", "Place Kind?")
    L("Place Kind?", "Move Requester", 0); L("Place Kind?", "Book Requester", 1)
    L("Move Requester", "Check Placed"); L("Book Requester", "Check Placed")
    L("Check Placed", "Placed?"); L("Placed?", "Placed Row", 0); L("Placed?", "Restore?", 1)
    L("Placed Row", "Write Placed"); L("Write Placed", "Outcome")
    L("Restore?", "Restore Hold", 0); L("Restore?", "Outcome", 1)
    L("Restore Hold", "Recheck Restore"); L("Recheck Restore", "Outcome")
    L("Outcome", "Outcome Row"); L("Outcome Row", "Write Outcome"); L("Write Outcome", "Outcome Messages")
    L("Outcome Messages", "Send Message"); L("Send Message", "Return")
    w["connections"] = C
    for n in w["nodes"]:
        if n["type"].endswith("stickyNote"):
            n["parameters"]["content"] = ("## Finalize Consent v10\nCalled only by Consent Sweep, one Request ID at a time. Re-reads the row; "
              "Stage records progress (HOLD_SNAPSHOT, HOLD_DELETED, PLACING, PLACED) so the next sweep finishes or unwinds a run "
              "that died. The hold is copied to the row before it is deleted, the booking is checked, and a failed booking restores "
              "the hold; if that fails the row is NEEDS_ATTENTION and #approvals is told.")
    return w

# ---------------------------------------------------------------- Consent Sweep
SWEEP = r"""// Consent Sweep (v2, review 29 Sep): picks the ONE oldest consent request that needs work - a recorded decision
// (APPROVED / REJECTED / INCUMBENT_MOVED), a deadline that has passed, or a run left half-way (Stage) - and hands it
// to Finalize, which re-reads the row and decides. One row per minute keeps each run far shorter than the gap
// between runs, so two finalizations do not overlap. MBOOTH timeout still books; PREEMPT timeout still just expires.
const now = Date.now(), U = s => String(s || '').toUpperCase().trim();
const due = $input.all().map(i => (i && i.json) || {}).filter(r => {
  if (!r['Request ID'] || U(r['Status']) !== 'PENDING') return false;
  const st = U(r['Stage']);
  if (st === 'RESTORE_FAILED') return false;
  if (st || U(r['Decision'])) return true;
  const dl = Date.parse(r['Deadline'] || ''); return isFinite(dl) && now >= dl;
}).sort((a, b) => String(a['Request ID']).localeCompare(String(b['Request ID'])));
return due.length ? [{ json: { request_id: due[0]['Request ID'] } }] : [];"""

def build_sweep(w):
    N = {n["name"]: n for n in w["nodes"]}
    w["name"] = "Jessie — Consent Sweep — v2"
    N["Every 10 min"]["name"] = "Every Minute"
    N["Every 10 min"]["parameters"] = {"rule": {"interval": [{"field": "minutes", "minutesInterval": 1}]}}
    N["Sweep Decide"]["parameters"]["jsCode"] = SWEEP
    pr = N["Sweep Book"]; pr["name"] = "Process Row"; pr["onError"] = "continueRegularOutput"
    pr["parameters"]["workflowInputs"]["value"] = {"request_id": "={{ $json.request_id }}"}
    pr["parameters"]["mode"] = "each"
    w["nodes"] = [n for n in w["nodes"] if n["name"] not in ("Sweep Route?", "Mark Expired")]
    C = {}
    link(C, "Every Minute", "Read Pending Rows"); link(C, "Read Pending Rows", "Sweep Decide"); link(C, "Sweep Decide", "Process Row")
    w["connections"] = C
    return w, N["Read Pending Rows"]

# ---------------------------------------------------------------- Book Session v57
def build_book(w):
    w["name"] = "Jessie — Book Session — v57 (v56 fixed)"
    n = node(w, "Check Conflicts"); c = n["parameters"]["jsCode"]
    c = sub1(c, """  // A consented placement (room_override) may use a booth despite its standing hold; the hold is
  // transparent+recurring. Skip it here so the sanctioned booking is not blocked by the very hold the
  // holder just approved. A normal booking (no override) still sees the hold and triggers M-Booth consent.
  if (REQ.room_override && ev.recurringEventId) continue;
""", """  // v57 (review 29 Sep): room_override no longer skips every recurring event. A consented placement names the
  // exact approved hold in exclude_event_id (above); any OTHER booking or hold in the room still blocks it.
""", "book recurring skip")
    n["parameters"]["jsCode"] = c
    n = node(w, "Decide Preempt"); c = n["parameters"]["jsCode"]
    anchor = "const REQ = $('When Executed by Another Workflow').first().json || {};\n"
    c = sub1(c, anchor, anchor + "// v57: a consent placement (its description carries \"consent: <request>\") never opens another consent request.\n"
             "if (/\\bconsent:\\s*\\S+/.test(String(REQ.description || ''))) return [{ json: Object.assign({}, cc, { offer:false, preemptReason:'CONSENT_PLACEMENT' }) }];\n",
             "book decide preempt")
    n["parameters"]["jsCode"] = c
    n = node(w, "Return Rejection"); c = n["parameters"]["jsCode"]
    c = sub1(c, "const v = $input.first().json || {};\n",
             "const v = $input.first().json || {};\n"
             "// v57: a consent placement that clashes with ITS OWN earlier booking (a retry after a run that died after\n"
             "// booking) says so, so Finalize can finish instead of failing.\n"
             "const _mk = (String((($('When Executed by Another Workflow').first().json) || {}).description || '').match(/consent:\\s*([A-Za-z0-9-]+)/) || [])[1];\n"
             "const _own = _mk && Array.isArray(v.conflicts) ? v.conflicts.find(c => String(c.description || '').indexOf('consent: ' + _mk) !== -1) : null;\n",
             "book return rejection")
    c = sub1(c, "  human: v.human ||", "  consent_placed_id: _own ? (_own.id || 'placed') : '',\n  human: v.human ||", "book rr field")
    n["parameters"]["jsCode"] = c
    return w

# ---------------------------------------------------------------- Move Booking v25: record, don't finalize
MOVED_ROW = r"""// v25 (review 29 Sep): the move freed a room a consent request was waiting for. Record that on the row; Consent
// Sweep -> Finalize places the requester (one writer). The move itself already succeeded.
return [{ json: { 'Request ID': ($json.matched || {})['Request ID'] || '', 'Decision': 'INCUMBENT_MOVED', 'Decision At': new Date().toISOString() } }];"""
def build_move(w, t_sheet):
    w["name"] = "Jessie — Move Booking — v25 (v24 fixed)"
    cf = node(w, "Call Finalize"); pos = cf["position"]
    w["nodes"] = [n for n in w["nodes"] if n["name"] != "Call Finalize"]
    rec = clone(t_sheet, "Record Incumbent Moved", [pos[0] + 176, pos[1]]); rec["onError"] = "continueRegularOutput"
    w["nodes"] += [code("Incumbent Moved Row", MOVED_ROW, pos), rec]
    C = w["connections"]; out = C.pop("Call Finalize")
    for br in C["Place If Consent?"]["main"]:
        for t in br:
            if t["node"] == "Call Finalize": t["node"] = "Incumbent Moved Row"
    link(C, "Incumbent Moved Row", "Record Incumbent Moved")
    C["Record Incumbent Moved"] = out
    return w

def main(src, dst):
    W = {k: load(src, k) for k in ("main", "open", "finalize", "sweep", "book", "move")}
    t_sheet = copy.deepcopy(node(W["finalize"], "Mark Done"))
    sweep, t_read = build_sweep(W["sweep"])
    fin, T = build_finalize(W["finalize"])
    fin = finish_finalize(fin, T, t_read)
    outs = {"project-jessie-v176.json": build_main(W["main"]), "open-consent-request-v11.json": build_open(W["open"]),
            "finalize-consent-v10.json": fin, "consent-sweep-v2.json": sweep, "book-session-v57.json": build_book(W["book"]),
            "move-booking-v25.json": build_move(W["move"], t_sheet)}
    for f, w in outs.items():
        json.dump(w, open(os.path.join(dst, f), "w"), indent=2, ensure_ascii=False); print("wrote", f, len(w["nodes"]), "nodes")

if __name__ == "__main__":
    main(*sys.argv[1:3])
