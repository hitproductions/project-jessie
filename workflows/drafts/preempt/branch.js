// Preemption branch — the logic Book/Move run at the ROOM_OCCUPIED point to decide whether to offer
// the consent path instead of a bare refusal, and to assemble the Open Consent Request context.
// Pure functions, offline-tested. Draft — see docs/design/consent-engine.md. Reuses decidePreempt.
const { decidePreempt } = require('./logic');

// Session type is stamped on every event's description (like Dept:/Type:) so a FUTURE incumbent's
// type — and thus its Preemption Rank — is readable. Events booked before this stamp carry no SType
// and are therefore never preemptible (decidePreempt returns INCUMBENT_RANK_UNKNOWN -> safe refusal).
function stypeStamp(sessionType) {
  return sessionType ? ('SType: ' + String(sessionType).trim()) : '';
}
function parseSType(desc) {
  const m = String(desc || '').match(/SType:\s*([^\n|]+)/i);
  return m ? m[1].trim() : null;
}
// The booker id ("ref: Uxxxx") already written on events; the incumbent booker is the approver.
function parseRef(desc) {
  const m = String(desc || '').match(/ref:\s*([A-Z0-9]+)/i);
  return m ? m[1].trim() : null;
}

// Called at a ROOM_OCCUPIED conflict. Returns either {offer:false, reason} (fall through to the
// normal refusal) or {offer:true, open} where `open` is the context for Open Consent Request.
//   ctx: { requesterAuthorized, requesterType, requester, requesterName, room, reqStart, reqEnd,
//          reqPayload, incumbentEventId, incumbentTitle, incumbentDescription, rankMap }
function preemptAtConflict(ctx) {
  const incType = parseSType(ctx.incumbentDescription);
  const approver = parseRef(ctx.incumbentDescription);
  const d = decidePreempt(ctx.requesterType, incType, ctx.rankMap, { authorized: ctx.requesterAuthorized });
  if (!d.preempt) return { offer: false, reason: d.reason, incType: incType, approver: approver };
  if (!approver) return { offer: false, reason: 'NO_INCUMBENT_BOOKER', incType: incType, approver: null };
  const open = {
    requester: ctx.requester, requesterName: ctx.requesterName,
    approver: approver, approverName: '',           // resolved from Bookers by the workflow
    room: ctx.room, reqStart: ctx.reqStart, reqEnd: ctx.reqEnd,
    incumbentEventId: ctx.incumbentEventId, incumbentTitle: ctx.incumbentTitle,
    reqType: ctx.requesterType, reqPriority: d.rq, incPriority: d.inc,
    reqPayload: ctx.reqPayload,
  };
  return { offer: true, reason: 'OUTRANKS', incType: incType, approver: approver, open: open };
}

module.exports = { stypeStamp, parseSType, parseRef, preemptAtConflict };
