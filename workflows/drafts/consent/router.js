// Consent-reply router — the deterministic logic on main's every-message path. Decides what to do
// with a message from someone who has a PENDING consent request awaiting them (as the Approver).
// Pure, offline-tested. Draft. FAIL-OPEN: anything unclear is a 'normal' message and flows down the
// existing pipeline untouched. See docs/design/consent-engine.md.
//
// Implementation of the agreed flow (#1, instant): the incumbent moves their own booking via the
// NORMAL move flow (they pick the slot, gate-confirmed) — so the router does NOT intercept the move
// itself. It only: (a) catches an explicit "no" (decline) → REJECTED + tell the requester; (b) when
// the incumbent is engaging, injects a context note so the agent helps them move their booking. The
// requester is then placed by the Move-Booking tail hook the moment that move frees the room.
const { resolveConsent } = require('./logic');

// row = the PENDING Consent Requests row where this sender is the Approver (or null).
function routeConsent(msg, row) {
  if (!msg || msg.bot_id) return { branch: 'ignore', why: 'own bot / empty' };
  if (!row) return { branch: 'normal', why: 'no pending request awaits this sender' };
  if (String(row.Status || row.status || '').toUpperCase() !== 'PENDING') return { branch: 'normal', why: 'request already resolved' };
  if (resolveConsent(msg.text) === 'reject') return { branch: 'reject', why: 'incumbent declined' };
  // Any other message from the incumbent = they are engaging (likely giving a new time). Let the
  // agent handle the move normally, but inject the consent context so it knows what to do.
  return { branch: 'consent-help', why: 'incumbent engaging; agent moves their booking normally' };
}

// On an incumbent "no": mark the row REJECTED (sticky) and tell the requester (case (a)).
function rejectRow(row, now) {
  return {
    'Request ID': row['Request ID'] || row.request_id || '',
    'Status': 'REJECTED',
    'Resolved Via': 'reply-no',
    'Decided At': now || new Date().toISOString(),
  };
}
function notifyRequesterRejected(row) {
  const who = row['Approver Name'] || 'the current holder';
  const room = row['Room/Booth'] || 'that room';
  return `${who} kept their booking, so ${room} stays taken for that time. Want to try another time or room?`;
}
// A short reply to the incumbent acknowledging their decline.
function replyIncumbentDeclined(row) {
  return `No problem — your "${row['Incumbent Title'] || 'session'}" stays where it is. Thanks for letting me know.`;
}

// The context note injected into the agent turn when the incumbent is engaging (branch consent-help),
// so the agent moves the incumbent's booking via the normal Move flow. The Move tail hook then places
// the requester once the move frees the room — the agent does NOT place the requester.
function incumbentContext(row) {
  const who = row['Approver Name'] || 'this booker';
  const title = row['Incumbent Title'] || 'their booking';
  const room = row['Room/Booth'] || 'a room';
  const reqName = row['Requester Name'] || 'a higher-priority booking';
  return `CONSENT CONTEXT: You earlier asked ${who} to move "${title}" out of ${room} to free it for `
    + `${reqName}, which outranks it. They are replying now. If they give a new time or room, move `
    + `"${title}" there via the normal Move flow — present the move summary and confirm as usual. Do `
    + `NOT book ${reqName} yourself; that happens automatically once "${title}" moves and frees the `
    + `room. If they decline, tell ${reqName} it stays taken.`;
}

module.exports = { routeConsent, rejectRow, notifyRequesterRejected, replyIncumbentDeclined, incumbentContext };
