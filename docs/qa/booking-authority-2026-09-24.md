# QA runsheet — Booking authority + notifications (24 Sept 2026)

Feature under test: an authorized **coordinator** may move/cancel a booking that isn't theirs
(within their department), and on any such change Jessie **DMs the booker and the assigned
engineer**. Testers: **Trish** (Tricia Rumbaoa, Finance), **Camy** (Camy Caridad, Sales & Accounts),
**Jess** (Jess Barbosa, Marketing).

## Before the run (setup)

- **Dates are year-shifted to 2027.** When you say "next Friday", Jessie books 2027 — that's
  expected. Real bookings are real; QA runs on 2027 on purpose.
- **Notification routing is in dev mode.** The three testers are on the allowlist, so they receive
  their *own* DMs for real. Anyone **not** allowlisted (e.g. a real engineer named in a title)
  gets their notice rerouted to Howard with a `[DEV]` prefix — that's expected, not a bug.
- **Monday prerequisite (Tel):** give **Jess** a `Dept Head` (or the new coordinator tag) in
  **Marketing** in Bookers. Without it, no tester can exercise the *authorized-change* path — see
  "Why only Jess" below.
- Howard is a temporary test coordinator for **Audio Post** only (hard-coded for the weekend); use
  him to drive changes on Audio Post bookings if needed.

## Why only Jess can perform an authorized change

Authority is matched against the **booking's department**, which is the *session's* producing
department (Audio Post, Music, Localization, Video Post, Marketing) — never the booker's own
department. Of the three testers, only **Jess is in a producing department (Marketing)**, so only she
can be a real coordinator. **Trish (Finance)** and **Camy (S&A)** are support departments that never
own studio bookings, so they can only be the *notified party* or the *(correctly) refused* party.
Camy's `Client Booking` tag does not change this today. (See `docs/design/booking-authority.md`.)

## Scenarios

### 1. Authorized change + notification — Jess (the full path)
1. Have someone else (another tester, or Howard) book a **Marketing** session; note its title.
2. **Jess** DMs Jessie: "move the `<that booking>` on `<date>` to `<another room>`" (or "cancel …").
3. Jessie shows the booking, notes it was booked by someone else, and asks to confirm. Jess says **yes**.
4. **Expect:** the change goes through (Jess is a Marketing coordinator), and the **booker** gets a
   DM ("your booking … was moved/cancelled by Jess Barbosa"). If the booker is an allowlisted tester,
   they get it for real; otherwise it lands with Howard as `[DEV]`.

### 2. Correct refusal — Trish and Camy (the guard from the unauthorized side)
1. **Trish** (and separately **Camy**) DM Jessie to cancel or move a booking they **don't own** —
   e.g. the Marketing one from scenario 1, or any studio booking.
2. **Expect:** Jessie refuses — *"… was booked by `<name>`, and you do not have authority to
   cancel/move it."* Nothing changes on the calendar. (Camy is refused too — her S&A Client-Booking
   tag doesn't match a studio booking's department.)

### 3. Notified as the booker — all three
1. Each tester books a session **they own** (Jess: Marketing; for Trish/Camy use an **Audio Post**
   session so Howard can drive the change).
2. A coordinator moves/cancels it — **Jess's** own booking by another Marketing coordinator, or
   Trish/Camy's Audio Post booking by **Howard**.
3. **Expect:** the tester (the booker) receives a real DM telling them who changed their booking.

### 4. Engineer notice — simulated to Howard in dev (by design)
During dev/QA the **engineer** notice always routes to Howard as `[DEV] would notify <name>…`, even
for an allowlisted tester — the ALLOW list applies to the **booker only**, so a tester is DM'd for
real only for bookings *they made*, not ones made *for* them where they're just the engineer. So
when a booking with a tester's initials as engineer is changed, expect the engineer line to appear
in **Howard's** DM as `[DEV]`, not the tester's. (At launch, `DEV_REDIRECT=''` restores real engineer
DMs.)

### 5. No notification on a self-change — control case
1. A tester moves/cancels their **own** booking.
2. **Expect:** the change happens, but **no** notification DM is sent (owners aren't pinged about
   their own actions).

## What to record per scenario
- Did the change go through / get refused as expected?
- Did the right people get a DM, with the right wording (booker vs engineer, correct actor + room)?
- Anyone who should *not* have been pinged?

## Known limitation to note, not a bug
S&A/BD "Client Booking" coordinators (incl. Camy) can't act on studio bookings under the current
within-department rule — this is the open Phase-2 decision, tracked in the design doc.
