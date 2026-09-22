// Move-Booking tail hook — the deterministic match that turns "the incumbent just moved" into
// "place the requester". After a successful move, we look for a PENDING consent request whose
// incumbent booking is exactly the one that just moved, matched on the booking's ORIGINAL event id
// (the pending row's `Incumbent Event Id`). A precise id match — no room/slot overlap fuzziness.
// If found, that move just vacated the contested room, so the requester gets placed (via Finalize,
// place-only). Pure, offline-tested. Draft. See docs/design/consent-engine.md.
//
// FAIL-SAFE: the move has already succeeded by the time this runs; if the lookup errors or matches
// nothing, the move stands and the requester is simply not placed here (the sweep is the backstop).

function findConsentForMove(movedOriginalId, pendingRows) {
  const id = String(movedOriginalId || '').trim();
  if (!id) return null;
  for (const r of (pendingRows || [])) {
    if (!r) continue;
    if (String(r['Status'] || r.status || '').toUpperCase() !== 'PENDING') continue;
    const incId = String(r['Incumbent Event Id'] || r.incumbentEventId || '').trim();
    if (incId && incId === id) return r;
  }
  return null;
}

module.exports = { findConsentForMove };
