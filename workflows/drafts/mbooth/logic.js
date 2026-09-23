// M-Booth shared-use approval — the deterministic logic that carries the risk, as pure functions
// so they unit-test offline before anything is wired. Draft — see docs/design/mbooth-approval.md.
// M-Booth is the MBOOTH caller of the shared consent engine (docs/design/consent-engine.md).
//
// In the real nodes these read the Slack Trigger, the Consent Requests row, and $now; here they take
// those as plain arguments so the decisions can be tested in isolation. All clock math is Asia/Manila
// (UTC+8, no DST) — the studio timezone; the old draft said "PST", which was an error.

// ── 1. Consent gate (approval branch only) ───────────────────────────────────
// Deterministic yes/no, same spirit as the confirmation gate: an explicit word, nothing model-judged.
// Anything unclear is left PENDING (the sweep expires-or-books it per policy, or the holder replies
// again clearly). Reused from the shared engine; kept here so M-Booth tests are self-contained.
const YES = ['yes', 'y', 'approve', 'approved', 'ok', 'okay', 'sure', 'go', 'confirmed', 'yes.'];
const NO  = ['no', 'n', 'reject', 'rejected', 'deny', 'denied', 'no.'];
function resolveConsent(text) {
  const t = String(text == null ? '' : text).trim().toLowerCase().replace(/[!,.]+$/, '');
  if (YES.indexOf(t) !== -1) return 'approve';
  if (NO.indexOf(t) !== -1) return 'reject';
  return 'unclear';
}

// ── 2. Shared-use booth set + holder map ─────────────────────────────────────
// The three booths that carry a standing recurring hold and are NOT first-come. Everything else uses
// normal Book Session. GENERALIZED 2026-09-23 (Howard, approach A): NO hard-coded booth list. Any room
// named M<n> is an M-booth; any RECURRING event on it is a standing hold; the holder is read off the
// hold's own `ref:<slack id>` tag (the same convention Jessie stamps on bookings). So new/other booths
// need no code change — just a `ref:` on their recurring hold. An untagged hold can't be routed to a
// holder, so it falls through to the normal refuse until someone tags it.
function isMBooth(room) { return /^M\d+$/i.test(String(room == null ? '' : room).trim()); }
function parseHoldName(summary) { const m = String(summary || '').match(/^\s*M\d+\s*-\s*(.+?)\s*$/i); return m ? m[1].trim() : ''; }

// Does a standing-hold event cover the requested slot? The workflow supplies the booth's events (from
// List Events); a hold is an event flagged as the standing hold (title keyword or an all-day/recurring
// marker the caller decides). Pure overlap test: [start,end) intersects [holdStart,holdEnd).
function overlaps(aStart, aEnd, bStart, bEnd) {
  const as = new Date(aStart).getTime(), ae = new Date(aEnd).getTime();
  const bs = new Date(bStart).getTime(), be = new Date(bEnd).getTime();
  return as < be && bs < ae;
}
function holdCoversSlot(holdEvents, startISO, endISO) {
  for (const h of (holdEvents || [])) {
    if (!h) continue;
    if (overlaps(startISO, endISO, h.start, h.end)) return true;
  }
  return false;
}

// ── 2b. Identify the standing hold, and decide the M-Booth branch ────────────
// A conflict is a standing hold when it is a RECURRING event on the booth — Howard's rule "any recurring
// booking for an M-booth applies" (transparency-agnostic: M1/M4 holds are Busy, M2/M6 are Free, all are
// holds). A one-off booking is not a hold; it is an ordinary first-come clash. The holder is read off the
// hold's `ref:` tag; the display name off its "M<n> - <name>" title.
function parseRefId(desc) { const m = String(desc || '').match(/ref:\s*([A-Z0-9]+)/i); return m ? m[1].trim() : ''; }
function isStandingHold(c) { return !!(c && c.recurring); }

// Decide the M-Booth branch at a ROOM_OCCUPIED. cc = enriched Check Conflicts output (each conflict
// carries {room, summary, id, description, transparent, recurring}). Returns one of:
//   none               → not an M-booth / not a recurring hold → fall through to normal preempt/refuse
//   book_as_holder     → the requester IS the hold's owner → (currently falls through; own-booth booking TODO)
//   room_taken         → a real (non-recurring) booking also overlaps → ordinary first-come clash, refuse
//   unidentified_holder→ recurring hold but no `ref:` tag → can't ask anyone → fall through to refuse
//   open_mbooth        → open a consent request to the booth holder (from the hold's `ref:`)
function decideMBooth(cc, REQ) {
  const room = String((REQ && REQ.rooms) || '').trim();
  if (!isMBooth(room)) return { action: 'none', why: 'not an M-booth' };
  if (!cc || cc.reason !== 'ROOM_OCCUPIED' || !Array.isArray(cc.conflicts) || !cc.conflicts.length) {
    return { action: 'none', why: 'no room conflict' };
  }
  const holds = cc.conflicts.filter(isStandingHold);
  const nonHolds = cc.conflicts.filter(c => !isStandingHold(c));
  if (!holds.length) return { action: 'none', why: 'conflict is not a recurring hold' };
  if (nonHolds.length) return { action: 'room_taken', why: 'a real (non-recurring) booking also overlaps' };
  // Capture the hold's event-instance id + title too: on consent Finalize CANCELS this hold instance
  // (M-booth only, releasing the room resource) BEFORE booking the requester — a clean transfer.
  let holder = '', holdName = '', holdEventId = '', holdTitle = '';
  for (const h of holds) { const r = parseRefId(h.description); if (r) { holder = r; holdName = parseHoldName(h.summary); holdEventId = h.id || ''; holdTitle = h.summary || ''; break; } }
  if (!holder) return { action: 'unidentified_holder', why: 'recurring hold has no ref: tag' };
  const requester = parseRefId(REQ && REQ.description);
  if (requester && requester === holder) return { action: 'book_as_holder', why: 'requester is the hold owner' };
  return { action: 'open_mbooth', approver: holder, approverName: holdName, booth: room,
    holdEventId: holdEventId, holdTitle: holdTitle, why: 'open consent to the booth holder (from the hold ref:)' };
}

// ── 3. Deadline tiers (request execution) — CONFIRMED by Howard 2026-09-22 ────
// How long the holder has to respond, by how far out the booking is (Asia/Manila calendar days):
//   • booking 2+ days away  → now + 24h
//   • booking is tomorrow    → 10:00 AM Manila on the booking day
//   • booking is same day    → now + 3h
// Always floored at now and capped at the session start (a deadline can't fall after the session
// begins). Config lets the live node override any tier without a code change.
const TZ = 8 * 3600 * 1000; // Asia/Manila = UTC+8, no DST
function manilaDayIndex(ms) { return Math.floor((ms + TZ) / 86400000); }
function computeDeadline(nowISO, startISO, cfg) {
  const c = cfg || {};
  const sameDayH = c.sameDayH == null ? 3 : c.sameDayH;          // same day → 3h (Howard)
  const farWindowH = c.farWindowH == null ? 24 : c.farWindowH;    // 2+ days → 24h
  const dayBeforeHour = c.dayBeforeHour == null ? 10 : c.dayBeforeHour; // tomorrow → 10:00 Manila
  const now = new Date(nowISO).getTime();
  const start = new Date(startISO).getTime();
  const daysAhead = manilaDayIndex(start) - manilaDayIndex(now);
  let deadline;
  if (daysAhead >= 2) {
    deadline = now + farWindowH * 3600 * 1000;
  } else if (daysAhead === 1) {
    const manilaMidnightUTC = manilaDayIndex(start) * 86400000 - TZ; // 00:00 Manila of booking day, in UTC ms
    deadline = manilaMidnightUTC + dayBeforeHour * 3600 * 1000;
  } else {
    deadline = now + sameDayH * 3600 * 1000; // same day (or already-today/past)
  }
  deadline = Math.max(now, Math.min(deadline, start)); // never before now, never past session start
  return new Date(deadline).toISOString();
}

// ── 4. Sweep action — what the scheduled sweep does with a row whose deadline passed ──
// CONFIRMED policy (Howard 2026-09-22): an MBOOTH request with no holder response by the deadline
// BOOKS ANYWAY (silence = the booth defaults to available; the shared hold is a courtesy, not a lock).
// A PREEMPT request must NEVER auto-act — silence just EXPIRES it (you can't move someone's booking
// without their yes). Only PENDING rows past their deadline are touched; everything else waits/skips.
function sweepAction(row, nowISO) {
  const status = String((row && row.Status) || '').toUpperCase();
  if (status !== 'PENDING') return { action: 'skip', why: 'status is ' + (status || 'empty') };
  const now = new Date(nowISO).getTime();
  const dl = (row && row.Deadline) ? new Date(row.Deadline).getTime() : NaN;
  if (!Number.isFinite(dl)) return { action: 'skip', why: 'no deadline' };
  if (now < dl) return { action: 'wait', why: 'before deadline' };
  const kind = String((row && row.Kind) || '').toUpperCase();
  if (kind === 'MBOOTH') return { action: 'book', why: 'MBOOTH timeout = book (holder did not respond)' };
  return { action: 'expire', why: kind + ' timeout = expire (no auto-action without consent)' };
}

module.exports = {
  resolveConsent,
  isMBooth, parseHoldName, overlaps, holdCoversSlot,
  parseRefId, isStandingHold, decideMBooth,
  computeDeadline, sweepAction,
};
