# QA checklist

*Added 2026-09-29, from that night's QA. The lesson behind it: bugs hid in steps nobody finished (Prepare Booking's
"yes" was never tested until 2 of 4 failed live) and in wordings nobody typed (bug 18 took three builds because the
AI wrote series dates three ways).*

## 1. Before every import: `./scripts/test-all`

Pulls every live workflow, fetches two recordings, runs every offline check (gate, 462 node checks, `$fromAI`, dates,
consent, the sims, ids, surviving fixes). Reads only. Git-ignored output in `diagnostics/test-all/`.

- To test a **candidate** instead: `./scripts/test-nodes MAIN BOOK CANCEL FIND MOVE` and `./scripts/test-gate <main>`.
- **Prompt or tool-description change?** Also read it against the rest of the prompt for contradictions. Tests do not
  catch these; the v180 review found six (fixed in v181).

## 2. After every import: live smoke test (~15 min)

Run by Claude through the Slack connector, in Tara's DM with Jessie. `qa-watch` reads each run. 2027 dates only;
titles start `QATEST`. **Every flow goes through to the result, never just the summary.**

| # | Say | Expect |
|---|---|---|
| 1 | Book a studio, all details given | Summary with `_check_` + "Book it? Reply yes or no." |
| 2 | `yes` | "Booked." · **no AI call** · event on the calendar |
| 3 | `yes` again | "That's already booked - nothing else was changed." · no AI |
| 4 | Move it to another time the same day | Summary + "Move it?" → `yes` → "Moved …" · event moved, one copy |
| 5 | Cancel it | Card with `_check_` → `yes` → "Cancelled …" · **no AI** · event gone |
| 6 | Book, then `yes but make it 3pm` | Nothing booked; a new summary |
| 7 | Book, then `no` | Nothing booked |
| 8 | A 4-date series, then `yes` | "Booked 4 sessions" on the **first** yes · 4 events · weekday labels right (bug 19) |
| 9 | Cancel a seeded event with someone else's `ref:` | Refused (NOT_YOURS) · event untouched |

Then **delete every `QATEST` 2027 event** and check none is left.

## 3. Log, don't fix

During a round, bugs are logged, not fixed. One line each:

`#N · what was said · expected · what Jessie did · execution id · time`

Fixing starts after the round, with Tara choosing which.

## 4. Measure

From the executions (`./scripts/health`, `n8n execs`), not by feel. Compare the same kinds of turns as the last round:

- reply time (median per kind of turn: request → summary, yes → result, series)
- AI calls per turn (the direct yes paths must be 0)
- messages needed to finish a booking; repeated questions or summaries; failed yeses

Baseline (29 Sep, v180): median turn 7–9 s · yes to a booking or cancel 4–9 s · 5-date series 32–38 s.

## 5. The scenario bank

Every logged bug becomes a scenario with its **exact wording**, run before launch and after any big change. From
29 Sep: "Friday next week" · "every Tuesday in November" · dates with no year ("Dec 7") · Taglish · a repeated yes ·
a conditional yes · "make it 3pm instead" (bug 12) · "this week" (bug 10) · a vocal booth request (bug 2).

## 6. Not automated

- **A second person:** a coordinator acting for their department, consent requests. Needs another account.
- **Real staff wording.** Before 12 Oct, 2–3 coordinators and engineers book for real for a few days; someone reads
  their executions daily; each surprise goes into the scenario bank.
