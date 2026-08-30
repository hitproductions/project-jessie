# Brief — update the Jessie deck for the HAIST biweekly

Self-contained. Everything needed to make these edits is in this file; nothing
has to be recovered from a previous conversation.

## What this is

`jessie-deck-2026-09-01_8.html` — a single-file HTML deck presented on **Tuesday
1 September 2026** at the HAIST biweekly. Currently in `~/Downloads/`.

One file, no build step, no dependencies. Open it in a browser and press `→`.
Each slide is a `<section class="slide">` inside `#track`. The stage is a fixed
1600×900 that scales to fit the window, so **a slide cannot grow** — content that
overflows is clipped, not scrolled. Adding rows to a full slide breaks it
silently. Check every slide you touch at a narrow window before finishing.

## House rules

- **Do not restyle anything.** The CSS is a deliberate house system — black,
  `#EF4123` red, Avenir Next, hard corners (`border-radius:0` is enforced
  globally). Reuse the existing classes; do not add new visual patterns.
- **Do not add slides unless asked.** Several footers carry manual counters
  (`1 / 4`, `2 / 4`). Adding a slide to a section means renumbering that whole
  section by hand.
- **Do not soften the findings.** The deck is honest about what still fails and
  that is the point of it. Keep the flagged (red) rows flagged.
- **Every claim must be checkable.** If a number or behaviour cannot be verified
  against the source below, leave it out rather than guessing.

## The source of truth

The build lives in `~/Documents/Claude/jessie/`. Three files there are current as
of 2026-08-30 and outrank anything in the deck:

- `DETERMINISM.md` — what the workflow enforces vs what the model still decides
- `PENDING.md` — the numbered items needing a change outside n8n
- `CLAUDE.md` — how the build works, and the launch checklist

If this brief and those files disagree, those files win.

## The edits

### 1. The confirmation card is out of date — slide 3

The markers changed from `(y/n)` to `(yes/no)` on all three actions.

- Heading `<h3>y / n confirmations</h3>` → `<h3>yes / no confirmations</h3>`
- `<p>Every summary now ends <code>Confirm to book. (y/n)</code>.</p>` → mention
  all three: `Confirm to book. (yes/no)`, `Confirm to cancel. (yes/no)`,
  `Confirm to move. (yes/no)`
- The `.tok` lists stay as they are — `y`, `yes`, `ok`, `sige`, `oo`, `opo`, `go`,
  👍 all still confirm, and `n`, `no`, `hindi`, `wait`, `not yet` all still
  decline. Only what Jessie *asks for* changed.
- The `.ver` line becomes: `v81 · (yes/no) as of v99 · before v81, any reply at
  all counted as approval — including "no"`

This is the slide the kicker calls "worth reading twice", so it is the one that
most needs to be right.

### 2. Same wording on slide 5

`<div class="drow"><b>What counts as approval</b><span>A literal y/n match on the
whole message</span></div>` → "A literal match on the whole message against a
fixed yes/no set".

### 3. Five things are missing from "What's Deterministic Now" — slide 5

All are true of the live build and all replaced a prompt rule that had failed.
The grid is two columns of seven; adding five means rebalancing or dropping the
weakest existing rows. **Pick at most two or three** — the slide is already full,
and the first is the strongest:

- **Who booked a session** — the raw Google event used to go to the model, and it
  read `creator`, which is always the n8n service account. It told the requester
  their own booking "was made by Howard, not you". A sub-workflow now shapes the
  day's events to id, title, time, room, booked-by and engineer; `creator` never
  reaches her.
- **The weekday beside a date** — recomputed from the date on the way out. She
  printed the wrong day three times, twice inside a booking summary.
- **The confirmation marker** — normalised on the way out. She wrote "Confirm to
  cancel both." and the gate refused the cancellation.
- **Internal vocabulary** — "priority room" and "last resort" are rewritten out of
  replies. The prompt rule forbidding them was ignored in five replies.
- **Conference rooms** — the injected room list now marks them "ask which before
  booking" instead of relying on a rule paragraphs away.

If only one fits, use the first.

### 4. The Airtable count is wrong — slide 7

`<h2>Five Edits In Airtable</h2>` → seven. Two new items, both from QA on
2026-08-30, both in `PENDING.md` as items 6 and 7:

- **A client's `Technical Requirements` points at a field Jessie cannot read.**
  The text ends "room preference already noted in Preferred Room", but
  `Preferred Rooms` is withheld from her because it returns record ids. She
  completed the dangling reference and claimed a room had been chosen to suit
  the client. Fix either end — add the lookup from item 5, or remove the clause.
- **Four session types list identical Priority and Last Resort rooms.** Event and
  VO Recording name the same rooms twice, so "last resort" means nothing.

**This slide is already full at five rows.** Seven will overflow. Either split it
across two slides — and renumber the `1 / 4` … `4 / 4` footers in that section —
or shorten the existing rows. Do not just add two `.trow`s and hope.

### 5. Two softenings — slide 5 footer and slide 6

- Slide 5 footer currently reads "ROOM_OCCUPIED and NO_REFERENCE have now refused
  in a live conversation, not only in tests". Still true. Worth adding that
  **`NOT_YOURS` has not** — refusing to cancel a booking someone else made needs
  a second person to have booked something, which is a concrete ask for the room.
- Slide 6 flags "Which rooms get offered" in red. Half of that — offering a
  conference room unprompted — is now handled in the data. The general case still
  belongs on the slide; consider narrowing the wording rather than removing it.

## What is still correct — do not touch

Verified against the live build on 2026-08-30:

- The `reset` card, including "clears at midnight Manila time" and the version
  history `v55 · reversed in v79 · v84`
- The 👀 card and `v57`; a turn is 10–15 seconds
- Numbered choices and `v67`
- The whole timing table — seven bookings measured end to end on the live build
- All three non-Airtable items: `reactions:write`, the calendar `ref:` decision,
  the n8n version check
- The External/Personal decision slide
- The title, the date, and the agenda

## How to check you are done

1. Search the file for `(y/n)` — there should be none left.
2. Search for `Five Edits` — should be gone.
3. Open the deck, arrow through every slide at a small window, and confirm no
   slide clips. The Airtable slide is the one at risk.
4. Confirm the section footers still count correctly (`1 / 4`, `2 / 4`, …).
