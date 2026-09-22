// Decide Preempt — the exact assembly the Book/Move `Decide Preempt` Code node inlines: at a
// single-conflict ROOM_OCCUPIED, gather the requester (from the booking's own description), the
// incumbent (from the enriched conflict), and the rank map (from reference_data), then run the
// offline-tested preemptAtConflict. Pure, offline-tested. Draft — see docs/design/consent-engine.md.
const { preemptAtConflict } = require('./branch');

function parseBookedBy(desc) { const m = String(desc || '').match(/Booked by:\s*([^|\n]+)/i); return m ? m[1].trim() : ''; }
function parseRefId(desc) { const m = String(desc || '').match(/ref:\s*([A-Z0-9]+)/i); return m ? m[1].trim() : ''; }

// Authorized to preempt = the same set as the Rule-1 move exception (verified live in Resolve Booking).
function isAuthorized(authority) { return /(dept head|client booking|haist dev)/i.test(String(authority || '')); }

// rankMap from reference_data.preemptionRanks — a { "<session type>": rank } object that main's Room
// Table injects. Keys normalized to match decidePreempt's lookup (lowercased, single-spaced).
function ranksFromRef(referenceData) {
  let ref = {};
  try { ref = (referenceData && typeof referenceData === 'object') ? referenceData : JSON.parse(referenceData || '{}'); } catch (_) { ref = {}; }
  const raw = ref.preemptionRanks || {};
  const map = {};
  for (const k in raw) { const n = Number(raw[k]); if (Number.isFinite(n)) map[String(k).trim().toLowerCase().replace(/\s+/g, ' ')] = n; }
  return map;
}

// cc = Check Conflicts output (its conflicts[0] now carries id/description/summary/room).
// REQ = the Book Session inputs. Returns preemptAtConflict's result: {offer, reason, open?}.
function decide(cc, REQ) {
  // Eligibility: only a single-room ROOM_OCCUPIED can be preempted. Every other rejection
  // (MISSING_DETAILS, ROOM_UNSUITABLE, multi-room clash, …) falls straight through to the
  // normal refusal. Folded in here so the branch needs only one IF downstream.
  const eligible = cc && cc.reason === 'ROOM_OCCUPIED' && Array.isArray(cc.conflicts) && cc.conflicts.length === 1;
  // Not preemptible → pass the ORIGINAL Check Conflicts rejection through unchanged (its verdict/
  // reason/human/conflicts) so Return Rejection relays the right message: NOT_CONFIRMED → "present the
  // summary", an occupied-but-not-preemptible room → "that room's taken", etc. Before this, every
  // non-offer collapsed to a bare NOT_ELIGIBLE and Return Rejection said only "the booking failed".
  if (!eligible) return Object.assign({}, cc, { offer: false, preemptReason: 'NOT_ELIGIBLE' });
  const inc = (cc && cc.conflicts && cc.conflicts[0]) || {};
  const reqPayload = JSON.stringify({
    summary: REQ.summary, start_iso: REQ.start_iso, end_iso: REQ.end_iso,
    rooms: inc.room || REQ.rooms, description: REQ.description, session_type: REQ.session_type,
    client: REQ.client, department: REQ.department, engineer: REQ.engineer,
    bookingType: REQ.bookingType, all_day: REQ.all_day,
    // reference_data (Room Table injection) must ride along so Finalize can replay the
    // requester's Book Session server-side; without it Book rejects NO_REFERENCE_DATA.
    reference_data: REQ.reference_data,
  });
  const r = preemptAtConflict({
    requesterAuthorized: isAuthorized(REQ.authority),
    requesterType: REQ.session_type,
    requester: parseRefId(REQ.description),
    requesterName: parseBookedBy(REQ.description),
    room: inc.room || REQ.rooms,
    reqStart: REQ.start_iso, reqEnd: REQ.end_iso,
    reqPayload: reqPayload,
    incumbentEventId: inc.id, incumbentTitle: inc.summary,
    incumbentDescription: inc.description,
    rankMap: ranksFromRef(REQ.reference_data),
  });
  // A ROOM_OCCUPIED that can't be preempted (not authorized, incumbent rank unknown, equal/lower
  // rank, no incumbent booker) is still just "that room is taken" — pass the ROOM_OCCUPIED rejection
  // through so the user gets the real message, not a bare "booking failed".
  if (!r.offer) return Object.assign({}, cc, { offer: false, preemptReason: r.reason });
  return r;
}

module.exports = { parseBookedBy, parseRefId, isAuthorized, ranksFromRef, decide };
