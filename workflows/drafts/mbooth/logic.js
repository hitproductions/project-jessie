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
// normal Book Session. Holder Slack ids are PLACEHOLDERS pending Tel's confirmation (historically
// M2→Peemo, M6→Nicole, M7→BD; confirm which are active + real ids). The functions take the map so the
// live node can inject the confirmed one without a code change.
const BOOTH_HOLDERS = {
  M2: { holder: 'UPEEMO_PLACEHOLDER', name: 'Peemo' },
  M6: { holder: 'UNICOLE_PLACEHOLDER', name: 'Nicole' },
  M7: { holder: 'UBD_PLACEHOLDER', name: 'BD' },
};
function normBooth(room) { return String(room == null ? '' : room).trim().toUpperCase(); }
function isSharedBooth(room, map) { return Object.prototype.hasOwnProperty.call(map || BOOTH_HOLDERS, normBooth(room)); }
function holderOf(room, map) { const m = (map || BOOTH_HOLDERS)[normBooth(room)]; return m || null; }

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
  BOOTH_HOLDERS, normBooth, isSharedBooth, holderOf, overlaps, holdCoversSlot,
  computeDeadline, sweepAction,
};
