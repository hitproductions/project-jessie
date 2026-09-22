# Calendar account switch — howard@ → calendar@

**Goal:** stop every Jessie booking being stamped *"Created by: Howard Luistro"*, and stop
the "New event" invite emails landing in Howard's inbox. Both come from **one** thing: the
Google account n8n signs in as when it writes to the calendar. Switch that account and both
symptoms go away — no workflow edits, no re-import.

**Who runs this:** Howard (the OAuth reconnect step needs the `calendar@` password, so it
can't be scripted or done by Claude). Google Workspace admin help needed for the
prerequisites.

**Time:** ~10 min once the prerequisites are done. Rollback is ~1 min.

---

## What is actually changing (and what is not)

The whole Google identity lives in **one n8n credential**:

- `googleCalendarOAuth2Api` · id **`6D1r3kaq6KaFdL0a`** · name **"Google Calendar account"**

Every calendar node in all 7 workflows binds this same credential id — `Create Event`,
`Delete Event`, and the raw `httpRequest` calls (`Get Events In Window`, `List Day Events`,
`Create Replacement`, `Delete Original`, …). Re-authenticating this **one** credential
switches all of them at once. Because the credential *id* never changes, **no workflow file
changes and `verify-ids` stays green.**

**Do NOT touch:**

- **The calendar** — "KDC Bookings" (`c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com`)
  and the room resources stay exactly as they are. We are changing *who writes to it*, not
  *what we write to*.
- **n8n workflow ownership** — the workflows live in Howard's Personal n8n project, and the
  n8n API key in `.env` must stay tied to that account (CLAUDE.md gotcha 15). That is an
  n8n-account fact; it never appears on a booking. Leave it.
- **The booker** — the event `ref:` and the "Booked by:" line come from the Slack requester
  and are already correct. Only the Google-level *creator* is wrong.

---

## Prerequisites (do these FIRST — all on the Google side)

These are the real work. The reconnect in n8n will silently fail or half-work if any of
these is missing, so confirm all four before touching n8n.

1. **`calendar@hitproductions.net` is a real, sign-in-able Google Workspace account.**
   A plain alias or a group won't do — OAuth needs an account that can log in and grant
   consent. (Unlicensed is usually fine as long as it can sign in and use Calendar.)

2. **`calendar@` has "Make changes to events" on KDC Bookings.**
   Open the KDC Bookings calendar → Settings → *Share with specific people* → add
   `calendar@` with permission **"Make changes to events"** (write). "See all event details"
   is not enough — bookings will fail to create.

3. **`calendar@` can book the room resources.**
   Same Workspace domain resources (Studio 1–8 / A–F / M1–8 / Salin / Katha / Likha / Lobby)
   are normally auto-bookable by any domain user. If your Workspace restricts resource
   booking, grant `calendar@` access. If a booking later comes back with the room *not*
   showing as reserved, this is the cause.

4. **The OAuth consent screen allows `calendar@`.**
   The n8n Google Calendar credential is backed by a Google Cloud OAuth client. If that
   client's consent screen is **External + Testing**, add `calendar@` as a **test user**
   (Google Cloud Console → APIs & Services → OAuth consent screen → Test users). If it's
   **Internal** to the Workspace, nothing to do. Skip this and the reconnect throws
   "access_denied" / "app not verified".

> If you're not sure who set up the Google Cloud OAuth client, that's Genzo/IT — the client
> id/secret sit inside the n8n credential and on the Google Cloud project. You do **not** need
> to change the client; you only need `calendar@` allowed to authorize it.

---

## The switch (n8n UI)

Do this at a quiet moment — no one mid-booking — because there's a few-second window where
the credential is re-authing.

1. **Pull first** (proves the live state before you start; CLAUDE.md ground rule):

   ```bash
   ./scripts/verify-ids
   ./scripts/health
   ```

   Both should be green. If `health` already shows a failure, stop and fix that first —
   don't switch on top of a broken state.

2. In n8n → **Credentials** → open **"Google Calendar account"** (`6D1r3kaq6KaFdL0a`).

3. Click **Reconnect** (or "Connect my account" / the account button). A Google sign-in
   popup opens.

4. **Sign in as `calendar@hitproductions.net`** and grant the Calendar permissions.
   → *This is the step only you can do — it needs the `calendar@` password.*

5. Back in n8n, the credential should show **"Account connected"**. **Save.**

That's it — every workflow now writes as `calendar@`. You do **not** need to edit or
re-import any workflow, and you do **not** need the "toggle Active off/on" dance (that's only
for tool *schema* changes, gotcha in CLAUDE.md — a credential re-auth isn't one).

---

## Smoke test (run every step — don't skip)

The point of this section: a reconnect can *look* connected in n8n and still fail at write
time if a prerequisite is missing. Prove it end to end.

### 1. Nothing broke structurally

```bash
./scripts/verify-ids        # 7 workflow ids + bot id still point at the live app
./scripts/test-nodes --live # 124 checks + 27 gate scenarios against what's deployed
```

Both green. (These read what n8n has *stored* — they won't catch an auth problem, but they
confirm the switch didn't disturb anything.)

### 2. Real booking, end to end — the actual proof

Book a throwaway session through Jessie in Slack, on a **year-shifted 2027 QA date** (never a
real live date):

> `book studio 8 tomorrow 2-4pm, SMOKETEST calendar-switch` → then `yes` at the confirm.

Watch for:

- Jessie replies **"Booked."** with a clean confirmation (no error).
- The invite email for it lands in **`calendar@`'s inbox**, *not* Howard's.

### 3. Confirm the attribution flipped

Open the new event in Google Calendar and check the bottom line:

- ✅ **"Created by: [calendar@ display name]"** — the whole point.
- ✅ The room shows as **reserved** (resource booking worked → prerequisite 3 is good).

### 4. Confirm n8n actually ran it clean

```bash
./scripts/health           # per-node executionStatus + timing from the last real turns
```

- `Create Event` (and the calendar `httpRequest` nodes) → **green**, sub-second.
- Nothing red. `health` exits non-zero if any node failed.

> A pull proves what's *stored*; `health` proves what *ran*. After an auth change, `health`
> is the one that matters — CLAUDE.md gotcha 12 ("a failing Code node fails open").

### 5. Test a cancel too (exercises Delete + the httpRequest path)

Cancel the SMOKETEST booking through Jessie (`cancel my smoketest booking` → `yes`). Confirm
it disappears from the calendar and `health` stays green. This proves the delete path and the
raw `httpRequest` calendar calls re-authed too, not just `Create Event`.

### 6. Clean up

Delete the SMOKETEST event if the cancel didn't already remove it. Done.

---

## Rollback (if anything in the smoke test fails)

Re-open the same credential in n8n → **Reconnect** → sign in as **`howard@hitproductions.net`**
→ Save. You're back to the previous state in under a minute; nothing else was touched, so
there's nothing else to undo. Then fix the failed prerequisite and try again.

---

## Caveats — set expectations

- **Past events keep Howard's name.** Google does not allow changing the *creator* of an
  existing event. Only bookings created **after** the switch show `calendar@`. The old 2027
  QA junk stays as-is — ignore it or delete the noise events by hand; there's no bulk fix.
- **Invite emails move to `calendar@`.** After the switch, the "New event" notifications go
  to `calendar@`'s inbox. You'll probably want to mute event notifications on that mailbox so
  it doesn't just recreate the same flood somewhere else.
- **This is identity/config, not a workflow change**, so the 23 Sep dev freeze doesn't gate
  it. Still, run it when you can do the smoke test immediately after, so a permission gap
  surfaces on the spot rather than mid-launch.

---

## Not changed by this (on purpose)

- Google **Sheets** credentials (`Google Sheets account`, `Google Sheets - Jessie Log`) — the
  Jessie/Posty logs. Sheet writes don't put a user-facing name on a booking, so they're out
  of scope here. Switch them separately later if you want the logs owned by `calendar@` too.
- The **Gemini** LLM credential — not identity-facing.
