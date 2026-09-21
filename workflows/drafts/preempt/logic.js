// Cross-department priority preemption — the deterministic pieces that decide WHETHER a
// higher-priority booking may displace an occupied room, written as pure functions so they
// unit-test offline before anything is wired into a workflow. Draft — not deployed.
// See docs/design/consent-engine.md.
//
// Priority is DATA, never model judgment: each session type carries a `Preemption Rank`
// (integer, higher outranks) on the Airtable Session Types table. Only a STRICT outrank
// opens preemption; equal or lower stays a hard ROOM_OCCUPIED refusal, exactly as today.

// ── 1. Rank lookup ───────────────────────────────────────────────────────────
// Build a { normalizedTypeName -> rank } map from the Session Types rows. A missing or
// blank rank is 0 (lowest: never preempts, always preemptible). Names are normalized so a
// stray case/space difference between the calendar title's type and Airtable can't misread.
function normType(s) {
  return String(s == null ? '' : s).trim().toLowerCase().replace(/\s+/g, ' ');
}

function buildRankMap(sessionTypeRows) {
  const map = {};
  for (const r of (sessionTypeRows || [])) {
    const name = normType(r.type);
    if (!name) continue;
    const n = Number(r.rank);
    map[name] = Number.isFinite(n) ? n : 0;
  }
  return map;
}

// Returns the integer rank, or undefined if the type isn't in the map at all. The caller
// must distinguish "present but 0" (a real lowest-priority type) from "unknown" (a type we
// can't read) — treating an unreadable type as 0 would let it be silently preempted.
function rankOf(rankMap, type) {
  const n = rankMap[normType(type)];
  return Number.isFinite(n) ? n : undefined;
}

// ── 2. The preemption decision ───────────────────────────────────────────────
// Given the requester's session type and the incumbent booking's session type, decide
// whether preemption is even on the table. This gates ONLY whether the consent flow may be
// offered — it never books anything, and it never overrides the occupied check on its own.
// Consent (attestation or the incumbent's yes) is still required downstream.
//
//   requesterType : the new booking's session type
//   incumbentType : the type of the booking currently holding the room
//   rankMap       : from buildRankMap()
//   opts.authorized : is the requester an authorized actor (coordinator / HAIST Dev)? Only
//                     an authorized requester may ever preempt; a Standard user cannot.
function decidePreempt(requesterType, incumbentType, rankMap, opts) {
  const authorized = !!(opts && opts.authorized);
  const rqRaw = rankOf(rankMap, requesterType);
  const incRaw = rankOf(rankMap, incumbentType);
  // A requester type we can't read is treated as lowest (0) — it just can't outrank.
  // An incumbent type we can't read must NOT be silently preemptible, so we refuse.
  const rq = rqRaw === undefined ? 0 : rqRaw;
  const inc = incRaw;

  if (!authorized) {
    return { preempt: false, reason: 'NOT_AUTHORIZED', rq, inc: inc === undefined ? null : inc };
  }
  if (inc === undefined) {
    return { preempt: false, reason: 'INCUMBENT_RANK_UNKNOWN', rq, inc: null };
  }
  if (rq > inc) {
    return { preempt: true, reason: 'OUTRANKS', rq, inc };
  }
  return { preempt: false, reason: rq === inc ? 'EQUAL_RANK' : 'LOWER_RANK', rq, inc };
}

module.exports = { normType, buildRankMap, rankOf, decidePreempt };
