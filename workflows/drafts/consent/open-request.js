// Open Consent Request — the deterministic builders for the sub-workflow that, when a higher-
// priority booking wants an occupied room, writes a PENDING row to the Consent Requests sheet,
// DMs the incumbent, and posts an audit line to #jessie-approvals. Pure functions, offline-tested.
// Draft — see docs/design/consent-engine.md. Reuses computeDeadline from ./logic.
const { computeDeadline } = require('./logic');

// The Consent Requests sheet header, in order. buildRow emits an object keyed by these names so the
// Google Sheets append node (autoMapInputData) drops each value in the right column. Keep in sync
// with the tab created 2026-09-21.
const COLUMNS = [
  'Request ID', 'Status', 'Kind', 'Requester', 'Requester Name', 'Approver', 'Approver Name',
  'Room/Booth', 'Req Start', 'Req End', 'Incumbent Event Id', 'Incumbent Title',
  'Incumbent New Start', 'Incumbent New End', 'Req Priority', 'Inc Priority', 'Deadline',
  'Requester DM', 'Approver DM', 'Log Thread TS', 'Resolved Via', 'Attested By', 'Decided At',
  'Req Payload',
];

function requestId(now, requester) {
  // sortable + unique-enough: compact ISO to the second + the requester's Slack id
  const stamp = new Date(now).toISOString().replace(/[-:T.]/g, '').slice(0, 14);
  return stamp + '-' + String(requester || 'unknown');
}

// c: the preemption context assembled by Book/Move at the ROOM_OCCUPIED point.
//   { requester, requesterName, approver, approverName, room, reqStart, reqEnd,
//     incumbentEventId, incumbentTitle, reqType, reqPriority, incPriority,
//     requesterDM, approverDM }
// cfg: deadline window/lead (placeholders until Tel's rules).
function buildRow(c, now, cfg) {
  const id = requestId(now, c.requester);
  const deadline = computeDeadline(now, c.reqStart, cfg);
  const row = {
    'Request ID': id,
    'Status': 'PENDING',
    'Kind': 'PREEMPT',
    'Requester': c.requester || '',
    'Requester Name': c.requesterName || '',
    'Approver': c.approver || '',
    'Approver Name': c.approverName || '',
    'Room/Booth': c.room || '',
    'Req Start': c.reqStart || '',
    'Req End': c.reqEnd || '',
    'Incumbent Event Id': c.incumbentEventId || '',
    'Incumbent Title': c.incumbentTitle || '',
    'Incumbent New Start': '',   // agreed later, in the DM
    'Incumbent New End': '',
    'Req Priority': c.reqPriority == null ? '' : c.reqPriority,
    'Inc Priority': c.incPriority == null ? '' : c.incPriority,
    'Deadline': deadline,
    'Requester DM': c.requesterDM || '',
    'Approver DM': c.approverDM || '',
    'Log Thread TS': '',          // DM-routed, so correlation ts is optional
    'Resolved Via': '',
    'Attested By': '',
    'Decided At': '',
    // the requester's original Book Session inputs, so Finalize can place them after freeing the room
    'Req Payload': c.reqPayload == null ? '' : (typeof c.reqPayload === 'string' ? c.reqPayload : JSON.stringify(c.reqPayload)),
  };
  return { id, deadline, row };
}

// The DM to the incumbent's booker (the approver). Plain, warm, explicit ask.
function incumbentDM(c) {
  const when = c.reqStart ? whenPhrase(c.reqStart, c.reqEnd) : 'the requested time';
  return `Hi ${c.approverName || 'there'} — ${c.requesterName || 'someone'} needs ${c.room} on `
    + `${when} for a higher-priority ${c.reqType || 'session'}, which would mean moving your `
    + `"${c.incumbentTitle}". Are you OK to move it? If yes, just tell me what time works for your `
    + `session and I'll sort it out. Reply here with yes or no.`;
}

// What Jessie tells the requester after opening the request (relayed by the caller).
function requesterReply(c) {
  const when = c.reqStart ? whenPhrase(c.reqStart, c.reqEnd) : 'that time';
  return `${c.room} is held by "${c.incumbentTitle}" (${c.approverName}) at ${when}. Your `
    + `${c.reqType || 'session'} outranks it, so I've asked ${c.approverName} to move — I'll confirm `
    + `once they reply. If you've already cleared it with them, reply "cleared with ${c.approverName}".`;
}

// The audit line posted to #jessie-approvals (view-only feed).
function approvalsLog(c, id, deadline) {
  return `[PREEMPT] ${id} — PENDING\n`
    + `${c.requesterName} wants ${c.room} (${whenPhrase(c.reqStart, c.reqEnd)}) for ${c.reqType} `
    + `(rank ${c.reqPriority}) over "${c.incumbentTitle}" / ${c.approverName} (rank ${c.incPriority}).\n`
    + `Asked ${c.approverName} by DM. Deadline ${deadline}.`;
}

function whenPhrase(startIso, endIso) {
  try {
    const opt = { timeZone: 'Asia/Manila', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' };
    const s = new Date(startIso).toLocaleString('en-US', opt);
    const e = endIso ? new Date(endIso).toLocaleTimeString('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' }) : '';
    return e ? `${s}–${e}` : s;
  } catch (_) { return String(startIso || ''); }
}

module.exports = { COLUMNS, requestId, buildRow, incumbentDM, requesterReply, approvalsLog, whenPhrase };
