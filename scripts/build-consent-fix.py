#!/usr/bin/env python3
"""Consent engine rebuild (29 Sep review), from fresh pulls.

  scripts/build-consent-fix.py <pull-dir> <out-dir>

pull-dir: main.json, open.json, finalize.json, sweep.json, book.json, move.json (fresh `n8n pull`s).
Writes project-jessie-v176, open-consent-request-v11, finalize-consent-v10, consent-sweep-v2, book-session-v57,
move-booking-v25.

Simpler design (Tara, 29 Sep): standing M-booth holds are "Show as available", so a consented booking goes in
ALONGSIDE the hold - nothing is deleted, so nothing has to be restored. main and Move record the decision on the row,
then call Finalize; Finalize re-reads the row, books (ignoring only that exact hold), and writes the outcome only if
the row is still PENDING. A second run (approval and timeout together, or a retry) recognises the first run's booking
by its consent marker instead of booking twice. Consent Sweep (every 10 min) sends each due row separately: timeouts,
and recorded decisions whose Finalize call did not finish. No lock is claimed.

New Consent Requests columns (setup): Decision, Decision At, Placement Event Id.
Setup on the calendar: the standing M-booth holds that block their booth (M1 - Rico, M4 - Tel, M4 - Japs, M8 - ANA)
set to "Show as available", as M6 - Marketing and M2 - Peemo already are.
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
// A decision is recorded on the row, then Finalize carries it out (Consent Sweep retries if that call does not finish).
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
DECISION_REPLY = r"""// Only reached when the decision could not be written; Finalize (called after a good write) does the messaging.
return [{ json: { output: "Sorry, I couldn't record that just now. Please reply again in a minute." } }];"""

def call_finalize(t_exec, pos, rid):
    n = clone(t_exec, "Call Finalize", pos)
    n["parameters"]["workflowInputs"]["value"] = {"request_id": rid}
    n["parameters"].pop("mode", None); n["onError"] = "continueRegularOutput"
    return n
CLARIFY_REPLY = r"""return [{ json: { output: $('Consent Router').first().json._consentReply } }];"""

def build_main(w, t_exec):
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
           ifeq(tmpl_if, "Decision Recorded?", "={{ $json.error ? 'no' : 'yes' }}", "yes", [x0 + 1344, y0 - 144]),
           call_finalize(t_exec, [x0 + 1568, y0 - 240], "={{ $('Decision Row').first().json['Request ID'] }}"),
           code("Decision Reply", DECISION_REPLY, [x0 + 1568, y0 - 48]),
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
    link(C, "Decision Row", "Record Decision"); link(C, "Record Decision", "Decision Recorded?")
    link(C, "Decision Recorded?", "Call Finalize", 0); link(C, "Decision Recorded?", "Decision Reply", 1); link(C, "Decision Reply", "Send Reply")
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

# ---------------------------------------------------------------- Finalize Consent: re-read, book, report
PLAN = r"""// Finalize Plan (v10, review 29 Sep). Re-reads the row by Request ID and decides from ITS state, never from what
// the caller passed. Nothing is deleted any more: a standing M-booth hold is "Show as available", so the requester
// is booked alongside it, and only that exact hold is ignored by the clash check (exclude_event_id).
""" + WHENFN + r"""
const IN = $('When Executed by Another Workflow').first().json || {};
const id = String(IN.request_id || '').trim();
const U = s => String(s || '').toUpperCase().trim();
const rows = $('Read Rows').all().map(i => (i && i.json) || {}).filter(r => id && String(r['Request ID'] || '').trim() === id);
const out = o => [{ json: Object.assign({ requestId: id }, o) }];
if (!id) return out({ act: 'skip', reason: 'NO_REQUEST_ID' });
if (rows.length !== 1) return out({ act: 'skip', reason: rows.length ? 'DUPLICATE_ROWS' : 'NOT_FOUND' });
const row = rows[0];
if (U(row['Status']) !== 'PENDING') return out({ act: 'skip', reason: 'ALREADY_' + U(row['Status']) });
const kind = U(row['Kind']) || 'PREEMPT', decision = U(row['Decision']);
const dl = Date.parse(row['Deadline'] || ''), due = isFinite(dl) && Date.now() >= dl;
const holdId = String(row['Incumbent Event Id'] || '').trim();
const via = decision === 'APPROVED' ? 'mbooth-approve' : decision === 'INCUMBENT_MOVED' ? 'move-hook' : decision === 'REJECTED' ? 'reply-no' : 'sweep-timeout';
const base = { kind, via, holdId, room: row['Room/Booth'] || '', approver: row['Approver'] || '', approverName: row['Approver Name'] || 'the holder',
  requester: row['Requester'] || '', requesterName: row['Requester Name'] || 'the requester', incTitle: row['Incumbent Title'] || '',
  when: whenPhrase(row['Req Start'], row['Req End']) };
let act;
if (decision === 'REJECTED') act = 'reject';
else if (kind === 'MBOOTH') act = (decision === 'APPROVED' || due) ? 'place' : 'skip';       // MBOOTH timeout still books
else act = decision === 'INCUMBENT_MOVED' ? 'place' : due ? 'expire' : 'skip';              // PREEMPT timeout: nobody moved
if (act !== 'place') return out(Object.assign(base, { act, reason: act === 'skip' ? 'NOT_DUE' : '' }));
function safeParse(s) { if (s && typeof s === 'object') return s; try { return JSON.parse(s || ''); } catch (_) { return null; } }
const req = safeParse(row['Req Payload']);
if (!row['Req Start'] || !row['Req End'] || !row['Room/Booth'] || !req) return out(Object.assign(base, { act: 'fail', reason: 'MISSING_REQ_DETAILS' }));
const dateOf = iso => { try { return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(iso)); } catch (_) { return ''; } };
const placeTarget = req.kind === 'move' ? 'move' : 'book';
// The marker lets a second run recognise a booking the first already made (Book Session hands it back on a clash).
const mark = ' | consent: ' + id;
const placePayload = placeTarget === 'move'
  ? { title: req.title || '', event_id: req.event_id || '', booking_date: req.booking_date || dateOf(row['Req Start']), new_start_iso: req.new_start_iso || row['Req Start'],
      new_end_iso: req.new_end_iso || row['Req End'], new_rooms: req.new_rooms || row['Room/Booth'] || '', requester: req.requester || row['Requester'] || '',
      requester_name: req.requester_name || row['Requester Name'] || '' }
  : Object.assign({}, req, { rooms: req.rooms || row['Room/Booth'] || '', start_iso: req.start_iso || row['Req Start'], end_iso: req.end_iso || row['Req End'],
      description: String(req.description || '').indexOf('consent: ' + id) === -1 ? String(req.description || '') + mark : String(req.description || ''),
      exclude_event_id: kind === 'MBOOTH' ? holdId : '' });
return out(Object.assign(base, { act, placeTarget, placePayload }));"""

CHECK_PLACED = r"""// Check Placed: CREATED / MOVED, or a clash with THIS request's own earlier booking (the consent marker - another
// run got there first) counts as placed. A booking the booth declined, or created at the wrong time, is ours and
// is removed so the calendar is left as it was. A call that errored is uncertain and is left for the next sweep.
const r = $input.first().json || {};
const st = String(r.status || '').toUpperCase();
if (st === 'CREATED' || st === 'MOVED') return [{ json: { next: 'placed', placementId: r.event_id || r.new_event_id || '' } }];
if (r.consent_placed_id) return [{ json: { next: 'placed', placementId: r.consent_placed_id, already: true } }];
if (r.error || !st) return [{ json: { next: 'outcome', outcome: 'retry', reason: 'PLACEMENT_UNCERTAIN' } }];
if (r.event_id) return [{ json: { next: 'remove', ownEventId: r.event_id, reason: 'PLACE_FAILED:' + st } }];
return [{ json: { next: 'outcome', outcome: 'fail', reason: 'PLACE_FAILED:' + (r.reason || st) } }];"""

OUTCOME = r"""// Outcome: the final state and the messages. A timeout says it went ahead under the timeout rule; "nothing changed"
// is only said when it is true.
const P = $('Plan').first().json;
const ran = n => { try { $(n).first(); return true; } catch (e) { return false; } };
const j = n => ran(n) ? ($(n).first().json || {}) : null;
const now = new Date().toISOString(), mb = P.kind === 'MBOOTH', to = P.via === 'sweep-timeout';
const APPROVALS = 'C0C34UMFXGD';
let fin = null; const msgs = [];
const dm = (t, text) => { if (t) msgs.push({ to: t, text }); };
const failNothing = reason => { fin = { 'Status': 'FAILED', 'Resolved Via': reason, 'Decided At': now };
  dm(P.requester, "I couldn't get " + (P.room || 'that room') + ' for you just now (' + P.when + '). Nothing was changed - please try another time or room.'); };
if (P.act === 'reject') {
  fin = { 'Status': 'REJECTED', 'Resolved Via': 'reply-no', 'Decided At': now };
  dm(P.requester, mb ? (P.approverName + ' would rather keep ' + P.room + ' on ' + P.when + ', so it stays theirs. Want another booth or time?')
                     : (P.approverName + " can't move their session, so " + P.room + ' stays taken for ' + P.when + '. Want another time or room?'));
  dm(P.approver, mb ? ('Okay, ' + P.room + ' stays yours on ' + P.when + '. I let ' + P.requesterName + ' know.') : ('Okay, "' + P.incTitle + '" stays where it is. I let ' + P.requesterName + ' know.'));
} else if (P.act === 'expire') fin = { 'Status': 'EXPIRED', 'Resolved Via': 'sweep-expired', 'Decided At': now };
else if (P.act === 'fail') failNothing(P.reason);
else if (ran('Check Placed')) {
  const cp = j('Check Placed');
  if (cp.next === 'placed') {
    fin = { 'Status': 'DONE', 'Resolved Via': P.via, 'Decided At': now, 'Placement Event Id': cp.placementId || '' };
    if (mb && to) {
      dm(P.requester, 'Done - ' + P.room + ' is yours for ' + P.when + '. ' + P.approverName + " didn't reply by the deadline, so it went ahead under the M-booth sharing rule.");
      dm(P.approver, 'No reply came in by the deadline, so under the M-booth sharing rule ' + P.requesterName + ' has ' + P.room + ' for ' + P.when + '.');
    } else if (mb) {
      dm(P.requester, 'Done - ' + P.room + ' is yours for ' + P.when + '. ' + P.approverName + " OK'd sharing the booth.");
      dm(P.approver, "You've offered your " + P.room + ' booth (' + P.when + ') to ' + P.requesterName + '. Thanks for sharing!');
    } else {
      dm(P.requester, 'Done - ' + P.room + ' is yours for ' + P.when + '. ' + P.approverName + ' moved their session to make way.');
      dm(P.approver, 'Heads up - your "' + P.incTitle + '" was moved to make room for a higher-priority session in ' + P.room + ", as you OK'd. Thanks!");
    }
  } else if (cp.next === 'remove') {
    const g = j('Recheck Own') || {};
    const errTxt = g.error ? JSON.stringify(g.error) : '';
    if (g.status === 'cancelled' || /\b(404|410)\b|not ?found|deleted|gone/i.test(errTxt)) failNothing(cp.reason);
    else { fin = { 'Status': 'NEEDS_ATTENTION', 'Resolved Via': cp.reason + '; OWN_EVENT_LEFT', 'Decided At': now };
      dm(P.requester, "I couldn't get " + P.room + ' for you (' + P.when + ') and a half-made booking may still show on the calendar. The team has been alerted to clear it.');
      msgs.push({ to: APPROVALS, text: '[CONSENT NEEDS ATTENTION] ' + P.requestId + ': the booking for ' + P.room + ' (' + P.when + ') failed (' + cp.reason + ') and its own event ' + cp.ownEventId + ' could not be removed. The holder\'s booking was not touched.' }); }
  } else if (cp.outcome === 'fail') failNothing(cp.reason);
}
return [{ json: { fin, msgs } }];"""
RECHECK_ROW = r"""// Write only if the row is still PENDING: a parallel run (approval and timeout at once) may have finished it.
const id = $('Plan').first().json.requestId;
const cur = $('Recheck Row').all().map(i => i.json || {}).find(r => String(r['Request ID'] || '').trim() === id) || {};
const o = $('Outcome').first().json;
if (!o.fin || String(cur['Status'] || '').toUpperCase() !== 'PENDING') return [];
return [{ json: Object.assign({ 'Request ID': id }, o.fin) }];"""
OUTCOME_MSGS = r"""// Messages go out only once the outcome is on the row; if the write failed, the next sweep redoes it.
const w = $input.first().json || {};
if (w.error) return [];
return ($('Outcome').first().json.msgs || []).map(m => ({ json: m }));"""
RETURN = r"""const o = (() => { try { return $('Outcome').first().json; } catch (e) { return {}; } })();
return [{ json: { request_id: $('Plan').first().json.requestId, status: (o.fin || {}).Status || 'UNCHANGED' } }];"""

def build_finalize(w, t_read):
    N = {n["name"]: n for n in w["nodes"]}
    w["name"] = "Jessie — Finalize Consent — v10"
    trig = N["When Executed by Another Workflow"]
    trig["parameters"] = {"workflowInputs": {"values": [{"name": "request_id"}]}}
    t_http, t_sheet, t_slack, t_if = N["Cancel Hold"], N["Mark Done"], N["Notify Incumbent"], N["Place Kind?"]
    book, move = N["Book Requester"], N["Move Requester"]
    notes = [n for n in w["nodes"] if n["type"].endswith("stickyNote")]
    for n in notes:
        n["parameters"]["content"] = ("## Finalize Consent v10\nRe-reads the row by Request ID, books the requester (a standing hold is "
          "\"Show as available\" and only that exact hold is ignored), and records the outcome only if the row is still PENDING. "
          "Nothing is deleted except this request's own declined booking. Called by main (a recorded yes / no), Move (incumbent moved) "
          "and Consent Sweep (timeouts and retries).")
    book["onError"] = "continueRegularOutput"; move["onError"] = "continueRegularOutput"
    book["parameters"]["workflowInputs"]["value"]["exclude_event_id"] = "={{ $('Plan').first().json.placePayload.exclude_event_id }}"
    P = lambda cx, cy: [cx * 224, cy * 176]
    read = clone(t_read, "Read Rows", P(1, 0)); read["alwaysOutputData"] = True; read.pop("onError", None)
    reread = clone(t_read, "Recheck Row", P(9, 0)); reread["alwaysOutputData"] = True; reread["onError"] = "continueRegularOutput"; reread["executeOnce"] = True
    url = ("=https://www.googleapis.com/calendar/v3/calendars/{{ encodeURIComponent('c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com') }}"
           "/events/{{ encodeURIComponent($('Check Placed').first().json.ownEventId) }}")
    def http(name, method, pos):
        n = clone(t_http, name, pos); p = {"url": url, "authentication": "predefinedCredentialType", "nodeCredentialType": "googleCalendarOAuth2Api", "options": {}}
        if method != "GET": p["method"] = method
        n["parameters"] = p; n["onError"] = "continueRegularOutput"; n["alwaysOutputData"] = True; return n
    write = clone(t_sheet, "Write Outcome", P(11, 0)); write["onError"] = "continueRegularOutput"
    msg = clone(t_slack, "Send Message", P(13, 0))
    msg["parameters"] = {"select": "channel", "channelId": {"__rl": True, "mode": "id", "value": "={{ $json.to }}"},
                         "text": "={{ $json.text }}", "otherOptions": {"includeLinkToWorkflow": False}}
    msg["onError"] = "continueRegularOutput"
    ret = code("Return", RETURN, P(14, 0)); ret["executeOnce"] = True
    t_if["position"] = P(4, 0); move["position"] = P(5, -1); book["position"] = P(5, 1); trig["position"] = P(0, 0)
    w["nodes"] = [trig, t_if, book, move] + notes + [read, code("Plan", PLAN, P(2, 0)),
        ifeq(t_if, "Place?", "={{ $json.act }}", "place", P(3, 0)),
        code("Check Placed", CHECK_PLACED, P(6, 0)),
        ifeq(t_if, "Remove Own?", "={{ $json.next }}", "remove", P(7, 0)),
        http("Remove Own Booking", "DELETE", P(7, -1)), http("Recheck Own", "GET", P(8, -1)),
        code("Outcome", OUTCOME, P(8, 0)), reread, code("Outcome Row", RECHECK_ROW, P(10, 0)), write,
        code("Outcome Messages", OUTCOME_MSGS, P(12, 0)), msg, ret]
    C = {}
    L = lambda a, b, br=0: link(C, a, b, br)
    L("When Executed by Another Workflow", "Read Rows"); L("Read Rows", "Plan"); L("Plan", "Place?")
    L("Place?", "Place Kind?", 0); L("Place?", "Outcome", 1)
    L("Place Kind?", "Move Requester", 0); L("Place Kind?", "Book Requester", 1)
    L("Move Requester", "Check Placed"); L("Book Requester", "Check Placed")
    L("Check Placed", "Remove Own?"); L("Remove Own?", "Remove Own Booking", 0); L("Remove Own?", "Outcome", 1)
    L("Remove Own Booking", "Recheck Own"); L("Recheck Own", "Outcome")
    L("Outcome", "Recheck Row"); L("Recheck Row", "Outcome Row"); L("Outcome Row", "Write Outcome")
    L("Write Outcome", "Outcome Messages"); L("Outcome Messages", "Send Message"); L("Send Message", "Return")
    w["connections"] = C
    return w

# ---------------------------------------------------------------- Consent Sweep
SWEEP = r"""// Consent Sweep (v2, review 29 Sep): every consent request that needs work goes to Finalize SEPARATELY (one
// sub-run per row, in turn) - a deadline that has passed, or a recorded decision whose Finalize call did not finish.
// Finalize re-reads each row and decides. MBOOTH timeout still books; PREEMPT timeout still just expires.
const now = Date.now(), U = s => String(s || '').toUpperCase().trim();
return $input.all().map(i => (i && i.json) || {}).filter(r => {
  if (!r['Request ID'] || U(r['Status']) !== 'PENDING') return false;
  if (U(r['Decision'])) { const at = Date.parse(r['Decision At'] || ''); return !isFinite(at) || now - at > 2 * 60 * 1000; }   // give main / Move's own call time first
  const dl = Date.parse(r['Deadline'] || ''); return isFinite(dl) && now >= dl;
}).sort((a, b) => String(a['Request ID']).localeCompare(String(b['Request ID']))).map(r => ({ json: { request_id: r['Request ID'] } }));"""

def build_sweep(w):
    N = {n["name"]: n for n in w["nodes"]}
    w["name"] = "Jessie — Consent Sweep — v2"
    N["Sweep Decide"]["parameters"]["jsCode"] = SWEEP
    pr = N["Sweep Book"]; pr["name"] = "Process Row"; pr["onError"] = "continueRegularOutput"
    pr["parameters"]["workflowInputs"]["value"] = {"request_id": "={{ $json.request_id }}"}
    pr["parameters"]["mode"] = "each"
    w["nodes"] = [n for n in w["nodes"] if n["name"] not in ("Sweep Route?", "Mark Expired")]
    C = {}
    link(C, "Every 10 min", "Read Pending Rows"); link(C, "Read Pending Rows", "Sweep Decide"); link(C, "Sweep Decide", "Process Row")
    w["connections"] = C
    return w, N["Read Pending Rows"], pr

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
MOVED_ROW = r"""// v25 (review 29 Sep): the move freed a room a consent request was waiting for. Record that on the row, then Finalize
// places the requester; if that call does not finish, Consent Sweep retries from the recorded decision.
return [{ json: { 'Request ID': ($json.matched || {})['Request ID'] || '', 'Decision': 'INCUMBENT_MOVED', 'Decision At': new Date().toISOString() } }];"""
def build_move(w, t_sheet, t_exec):
    w["name"] = "Jessie — Move Booking — v25 (v24 fixed)"
    cf = node(w, "Call Finalize"); pos = cf["position"]
    w["nodes"] = [n for n in w["nodes"] if n["name"] != "Call Finalize"]
    rec = clone(t_sheet, "Record Incumbent Moved", [pos[0] + 176, pos[1]]); rec["onError"] = "continueRegularOutput"
    w["nodes"] += [code("Incumbent Moved Row", MOVED_ROW, pos), rec,
                   call_finalize(t_exec, [pos[0] + 352, pos[1]], "={{ $('Incumbent Moved Row').first().json['Request ID'] }}")]
    C = w["connections"]; out = C.pop("Call Finalize")
    for br in C["Place If Consent?"]["main"]:
        for t in br:
            if t["node"] == "Call Finalize": t["node"] = "Incumbent Moved Row"
    link(C, "Incumbent Moved Row", "Record Incumbent Moved"); link(C, "Record Incumbent Moved", "Call Finalize")
    C["Call Finalize"] = out
    return w

def main(src, dst):
    W = {k: load(src, k) for k in ("main", "open", "finalize", "sweep", "book", "move")}
    t_sheet = copy.deepcopy(node(W["finalize"], "Mark Done"))
    sweep, t_read, t_exec = build_sweep(W["sweep"])
    fin = build_finalize(W["finalize"], t_read)
    outs = {"project-jessie-v176.json": build_main(W["main"], t_exec), "open-consent-request-v11.json": build_open(W["open"]),
            "finalize-consent-v10.json": fin, "consent-sweep-v2.json": sweep, "book-session-v57.json": build_book(W["book"]),
            "move-booking-v25.json": build_move(W["move"], t_sheet, t_exec)}
    for f, w in outs.items():
        json.dump(w, open(os.path.join(dst, f), "w"), indent=2, ensure_ascii=False); print("wrote", f, len(w["nodes"]), "nodes")

if __name__ == "__main__":
    main(*sys.argv[1:3])
