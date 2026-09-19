// M-Booth shared-use approval — the three pieces of deterministic logic that carry the
// risk, written as pure functions so they unit-test offline before anything is wired into
// a workflow. Draft — not deployed. See docs/design/mbooth-approval.md.
//
// In the real nodes these read the Slack Trigger, the Airtable pending row, and $now; here
// they take those as plain arguments so the decisions can be tested in isolation.

// ── 1. Router (main workflow, top of the path) ───────────────────────────────
// The one component on the every-message path. Kept deterministic and fail-open: a message
// is an approval reply ONLY if it arrives in the dedicated approvals channel AND matches a
// PENDING row AND comes from that row's approver. Everything else is a normal message and
// flows down the existing pipeline untouched.
const APPROVALS_CHANNEL = 'C_MBOOTH_APPROVALS';   // placeholder — real channel id once created

function route(msg, pending) {
  // msg: { channel, thread_ts, user, text, bot_id }
  // pending: the matching PENDING approval row for msg.thread_ts, or null
  if (msg && msg.bot_id) return { branch: 'ignore', why: 'own bot message' };
  if (!msg || msg.channel !== APPROVALS_CHANNEL) return { branch: 'normal', why: 'not the approvals channel' };
  if (!pending) return { branch: 'ignore', why: 'no pending request for this thread' };
  if (pending.status !== 'PENDING') return { branch: 'ignore', why: 'request already ' + pending.status };
  if (String(msg.user) !== String(pending.approver)) return { branch: 'ignore', why: 'not the approver' };
  return { branch: 'consent', why: 'approver replying to a pending request' };
}

// ── 2. Consent gate (approval branch only) ───────────────────────────────────
// Deterministic yes/no, same spirit as the confirmation gate: an explicit word, nothing
// model-judged. Anything unclear is left PENDING (the sweep will expire it, or the approver
// can reply again clearly).
const YES = ['yes', 'y', 'approve', 'approved', 'ok', 'okay', 'sure', 'go', 'confirmed', 'yes.'];
const NO  = ['no', 'n', 'reject', 'rejected', 'deny', 'denied', 'no.'];
function resolveConsent(text) {
  const t = String(text == null ? '' : text).trim().toLowerCase().replace(/[!,.]+$/, '');
  if (YES.indexOf(t) !== -1) return 'approve';
  if (NO.indexOf(t) !== -1) return 'reject';
  return 'unclear';
}

// ── 3. Deadline / window math (request execution) ────────────────────────────
// Pure function of the clock. The exact windows are Tel's to confirm; these are placeholders
// so the mechanism is testable now. Deadline = the earlier of (now + maxWindow) and
// (requestedStart - minLead); never before now. A request whose slot is already inside the
// minimum lead time gets deadline === now (nothing to wait for — treat as too-late).
function computeDeadline(nowISO, requestedStartISO, cfg) {
  const c = cfg || {};
  const maxWindowH = c.maxWindowH == null ? 24 : c.maxWindowH;   // placeholder
  const minLeadMin = c.minLeadMin == null ? 60 : c.minLeadMin;   // placeholder
  const now = new Date(nowISO).getTime();
  const start = new Date(requestedStartISO).getTime();
  const byWindow = now + maxWindowH * 3600 * 1000;
  const byLead = start - minLeadMin * 60 * 1000;
  const deadline = Math.max(now, Math.min(byWindow, byLead));
  return new Date(deadline).toISOString();
}

module.exports = { route, resolveConsent, computeDeadline, APPROVALS_CHANNEL };
