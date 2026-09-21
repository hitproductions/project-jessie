// Consent engine — the deterministic core logic, as pure functions so they unit-test offline
// before anything is wired into n8n. Draft — not deployed. See docs/design/consent-engine.md.
//
// This is the shared engine behind both callers (PREEMPT cross-dept room, MBOOTH shared booth).
// It supersedes the per-caller logic in workflows/drafts/mbooth/ (that router keyed on a Slack
// channel; this one keys on a pending row, because correspondence is now via DM).
//
// Nothing here reads Slack/Sheets directly; the real nodes pass those in as plain arguments so the
// decisions are testable in isolation.

// ── 1. Router: is this inbound DM a consent reply, or a normal message? ───────
// Runs on the every-message path, so it is deterministic and FAIL-OPEN: anything not positively
// identified as a consent reply is 'normal' and flows down today's pipeline unchanged. The only
// state it needs is whether the sender is the Approver on a PENDING row — supplied by a Google
// Sheets read of the Consent Requests tab that rides the existing parallel read fan-out.
//
//   msg:            { user, text, bot_id }
//   pendingForUser: the PENDING Consent Requests row where this sender is the Approver, or null
function classifyInbound(msg, pendingForUser) {
  if (!msg || msg.bot_id) return { branch: 'ignore', why: 'own bot / empty message' };
  if (!pendingForUser) return { branch: 'normal', why: 'no pending request awaits this sender' };
  if (pendingForUser.status !== 'PENDING') return { branch: 'normal', why: 'request already ' + pendingForUser.status };
  return { branch: 'consent', why: 'sender is the approver of a pending request' };
}

// ── 2. Consent gate: deterministic yes / no from the approver's reply ─────────
// Same spirit as the confirmation gate — an explicit word, never model-judged. Unclear stays
// PENDING (the sweep will expire it, or the approver can reply again clearly).
const YES = ['yes', 'y', 'yes.', 'yep', 'yup', 'ok', 'okay', 'sure', 'go', 'approve', 'approved', 'confirm', 'confirmed'];
const NO  = ['no', 'n', 'no.', 'nope', 'deny', 'denied', 'reject', 'rejected', 'decline', 'declined'];
function resolveConsent(text) {
  const t = String(text == null ? '' : text).trim().toLowerCase().replace(/[^\w ]/g, '').trim();
  if (!t) return 'unclear';
  const first = t.split(/\s+/)[0];
  if (YES.indexOf(t) !== -1 || YES.indexOf(first) !== -1) return 'approve';
  if (NO.indexOf(t) !== -1 || NO.indexOf(first) !== -1) return 'reject';
  return 'unclear';
}

// ── 3. Attestation parser: the requester's "cleared with <name>" fast path ────
// Deterministic and conservative — a fixed phrase, NOT free-text interpretation. The requester must
// use "cleared with <name>" / "confirmed with <name>" (the exact phrasing Jessie prompts for). We
// return the claimed name so the finalizer can log WHO was attested with; we do not fuzzy-match it.
function parseAttestation(text) {
  const t = String(text == null ? '' : text).trim();
  const m = t.match(/\b(?:cleared|confirmed|checked|okayed|okd)\s+(?:it\s+|this\s+)?with\s+([A-Za-z][A-Za-z .'\-]{0,60})/i);
  if (!m) return { attested: false, name: null };
  const name = m[1].trim().replace(/[.\s]+$/, '');
  if (!name) return { attested: false, name: null };
  return { attested: true, name: name };
}

// ── 4. Deadline: earlier of (now + window) and (start − lead), floored at now ─
// Window/lead are placeholders pending Tel's real rules. Shared by both callers; the sweep expires
// PENDING rows past their Deadline.
function computeDeadline(now, start, cfg) {
  const nowMs = new Date(now).getTime();
  const startMs = new Date(start).getTime();
  const windowMs = (cfg && cfg.maxWindowH ? cfg.maxWindowH : 24) * 3600 * 1000;
  const leadMs = (cfg && cfg.minLeadMin ? cfg.minLeadMin : 60) * 60 * 1000;
  const byWindow = nowMs + windowMs;
  const byLead = startMs - leadMs;
  const deadline = Math.max(nowMs, Math.min(byWindow, byLead));
  return new Date(deadline).toISOString();
}

module.exports = { classifyInbound, resolveConsent, parseAttestation, computeDeadline };
