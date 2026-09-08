# v121 — safe-subset prompt (what's in, what's held)

Companion note for `system-prompt-v121-safe-subset.md`. That file is the **paste-ready**
System Message; this file is just the changelog — do **not** paste this into n8n.

Built from the live v120 prompt (byte-identical to what's published now) by adding only
the parts of Tel's update that are safe without any n8n tool work. Verified: a diff of
v120 → v121 shows *only* the two additions below and nothing else changed.

## Included (safe as prompt-only)

1. **`# Booking authority`** — added as guidance, with one edit (see below). Every rule in
   it is either pure guidance or *restrictive* (it asks Jessie to loop in the right person
   / flag / confirm), so it fails safe even though the tools don't fully enforce it yet.
2. **`## Client type — External or Personal`** — added verbatim from Tel's version. Note it
   tells Jessie to pass `bookingType` to Book Session; Book Session has no input for that
   yet, so the value is currently inert (dropped, not stored). No user-facing harm — the
   booking still completes; the value simply won't persist until `bookingType` is wired.

## Held for the tool work (NOT in this file)

3. **`## Recurring bookings`** — held. It takes one confirmation and fires N Book Session
   calls, but the confirm-gate checks per booking, so occurrences after the first can fail
   → a half-booked series. Unverified; ship only once the gate is confirmed to authorize a
   whole series.
4. **Cancel + Reschedule authority reworks** — held. They tell dept heads / client-booking
   authorities they may change others' bookings, but the tools are still owner-match only,
   so those people get walked to a confirm and then refused. The Cancel and Reschedule
   sections here are left at their **v120 wording**, which matches the tools.

## The one edit inside the Booking authority section

The *"Changing someone else's booking"* bullet was **trimmed** to match today's tools
(owner-match only), so the prompt doesn't over-promise. Everything else in the section is
Tel's wording, verbatim.

- **Tel's original:** "…Cancelling or moving a booking that belongs to someone else takes
  the owner, the owner's department head, or — for a client session — a client-booking
  authority. You do not adjudicate this yourself: Move Booking and Cancel Booking read the
  owner off the event and decide…"
- **Trimmed to:** "…For a booking that belongs to someone else, you do not adjudicate this
  yourself — Move Booking and Cancel Booking read the owner off the event and decide.
  Today they allow the owner only and refuse everyone else; you may name the owner while
  showing the booking, but the tool's call is final either way."

When the Cancel/Move authority upgrade ships, this bullet reverts to Tel's fuller wording
and sections 3–4 above come in with it.

**Small caveat, flagged not fixed:** the section's opening line still reads "Book Session,
Move Booking and Cancel Booking each enforce these themselves." That's aspirational for the
not-yet-built parts (celeb / on-behalf / dept-head), but it's safe here because every
remaining rule in the section is restrictive guidance that fails safe. Left as Tel wrote it.

## To apply

Paste `system-prompt-v121-safe-subset.md` into the `Jessie AI Agent` node's System Message
in **expression mode** (n8n re-adds the leading `=`). Test on **canary** first. Do not
paste the M-Room approval section — that ships with its sub-workflows, separately.
