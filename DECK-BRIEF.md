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
  their own booking "was made by someone else, not you". A sub-workflow now shapes the
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
  in a live conversation, not only in tests". Still true, and it can now be
  strengthened rather than qualified: **every guard has refused something live**,
  `NOT_YOURS` included, as of 2026-08-30. It was proved with a seeded calendar
  event carrying a foreign `ref:` — no second person needed, and no real booking
  put at risk — and it held through two escalations: a claim of authority over
  the other person's bookings, then a claim that the session was really the
  requester's. That is a better line for the room than the old caveat: the guard
  was argued with and did not move.

  Drop the "needs a second person" ask entirely — it is no longer true.
- Slide 6 flags "Which rooms get offered" in red. Half of that — offering a
  conference room unprompted — is now handled in the data. The general case still
  belongs on the slide; consider narrowing the wording rather than removing it.

### 6. Optional, if there is room: what testing actually caught

The 2026-08-30 QA run went through every group (A–X). Two findings are worth a
slide between them, because both are about *how you know* rather than about
booking:

- **She could claim a booking she never made.** Once in 120 runs she answered an
  approved booking with "Booked." without calling the tool at all — copying the
  phrasing from an almost identical exchange two turns earlier. Nothing reached
  the calendar. Every guard built until then stopped a *wrong* booking being made;
  none of them stopped one being *claimed*. Fixed: a reply may not say "Booked"
  unless the booking tool reported success on that turn.
- **A broken safety net fails silently.** When `Guard Probe` — the node that
  rewrites replies on the way out — started timing out, replies still went to
  Slack, just with none of its corrections applied. Nothing looked wrong from the
  outside for five turns. What caught it was reading per-node execution status,
  not reading the replies.

If the deck has a "what we learned" beat, that second one is the honest version:
the interesting failures are the ones that leave no trace in the output.

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

---

## Addendum — add one slide on where the turn time goes

Added 2026-08-30 after measuring the live build. This is new material, not a
correction, and it is the strongest number in the deck.

**Where it goes:** immediately after the existing timing slide
(`<!-- TIMING -->`, the one titled "How Long A Booking Takes"). That slide gives
totals; this one explains them. Its footer is a bare `02`, so adding a slide
there does **not** break any `1 / 4`-style counter.

**Use the classes already on the timing slide** — `.ttable`, `.tnote`, `.tag`,
`.brand`, `.foot`. Do not invent a new visual pattern for this.

### The finding

A turn takes a median of 12.5 seconds. The single largest piece of that is not
the model — it is a process starting up.

```
Jessie AI Agent      3.52s     wraps the model and every tool call
Gate Context         3.45s     ← the first Code node in the execution
Google Gemini        2.36s
Airtable lookups   ~1.10s      each
Slack round trips  ~0.40s      each
Room Table           0.07s     ← a later Code node
```

n8n runs Code nodes in a separate task-runner process. The first Code node in an
execution waits for that process to start; every later one costs ~0.07s. It is
bimodal — either ~3.5s or ~0.07s — and across 14 consecutive turns, ten paid it.

`Gate Context` is the first Code node and always will be, because something has
to be first. It cannot be reordered away. It is paid on every message, including
ones that do nothing — a bare "hi" costs it.

**That is about 28% of every turn, and more than everything outside the model put
together.**

### Why the obvious fix does not work

Measured across 29 executions, the runner shuts down after **12–13 seconds idle**
— the longest gap that stayed warm was 12s, the shortest that went cold was 13s.
Keeping it warm with a scheduled workflow would mean firing a Code node every ten
seconds forever: roughly 8,600 executions a day, filling the execution log and
the database, to save 3.5s a turn. Not worth it.

### The ask — this belongs with the other owner items

It is a server configuration change, not a workflow change. Two questions for
whoever runs the n8n server, neither of which requires changing anything to
answer:

1. What n8n version is this instance running? (Visible in the n8n UI, bottom-left.)
2. Are any `N8N_RUNNERS_*` environment variables set?

If the runner's idle-shutdown timeout can be raised, or Code can run in the main
process as older n8n versions did, the turn drops from ~12.5s to about **9s**.
It is one environment variable and it is reversible.

### Accuracy rules for this slide

- Say **"about 28% of a turn"** and **"ten of fourteen turns paid it"**. Do not
  say every turn — roughly 70% do, and the deck's credibility rests on that kind
  of precision.
- Do not name a specific environment variable. The variable of that shape exists,
  but the exact name depends on the installed version and nobody has read the
  config yet. "Check the task-runner settings" is the honest phrasing.
- Do not promise the 9s. Say it is what the measurement implies if the setting
  can be changed.
- This finding was briefly withdrawn as a mismeasurement earlier the same day and
  then reinstated when measured properly. If anyone in the room saw the earlier
  version, the correction is worth stating plainly rather than glossed.
