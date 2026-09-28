# Jessie hallucination test, round 2: what changed and what it shows

*Runs on 28 September 2026, the day after the first test ([27 Sep report](eval-report-2026-09-27.md)).
Internal: it contains staff and client names.* Everything below is **live** as of 28 Sep, 18:40 PHT
(main v168, Book Session v55).

## The short version

- Every issue from the 27 Sep test, the follow-up discussion and the runs in between is **fixed and live**,
  confirmed with real Gemini before and after the import and with live test bookings. Nothing on the list is left open. The table in
  [Issue by issue](#issue-by-issue) has each one with its before and after numbers.
- **Invented and garbled names are closed at the source.** The prompt was asking Gemini for an engineer's full
  name, role and initials it often did not have, so given "Drey" it made up a surname. The prompt now asks for the
  name exactly as typed (the typed name 27 of 27 times, from 0 of 2), and code reads the engineer, arranger,
  project, client and times from the requester's own message and fills the rest from Airtable. No invented name
  has ever been booked, in either round.
- **Code now writes the summary the requester approves** (Prepare Booking, live since 16:28 PHT). The calendar title
  is in every summary (27 Sep: 23 of 97), in one fixed format, and a "yes" books exactly what was shown.
- **New clients work end to end.** A live test booking with a made-up client wrote its first row to the New
  Clients sheet, with the title and the booking as shown.
- **The padded-time bug is gone:** 0 "every room free" answers, from 79 of 199 checks.
- **Speed is back to normal:** a median of 10.6–10.7 s per turn, after one intermediate build ran at 14.4 s.

## What changed since 27 Sep

| When (PHT) | What went live | What it does |
|---|---|---|
| 10:58 | main v161, Book Session v49 | Clients optional; new clients allowed and logged; client room preferences dropped |
| 11:33 | main v162 + every sub-workflow | The four decisions from the 27 Sep report; the padded-time fix everywhere a time reaches the calendar |
| 13:58–15:20 | Book Session v51–v53, Room Availability v10, Move v21, Find v5 | The Prepare Booking engine; client checks; Studio E's calendar id; real free alternatives when a room is taken |
| **16:28** | **main v166, Book Session v54, Move v22** | **Prepare Booking on for everyone**; the arranger always asked; in-house arrangers; no self-consent |
| 17:52 | main v167, Book Session v55 | Names and details from the requester's words; complete free-room lists; one combined client question; "10am-12nn"; "last Monday" |
| 18:25 | main v168 | After a "no", the refused summary is no longer re-sent |

## How we tested

The same method as 27 Sep: the **eval twin**, a copy of live Jessie with only the Slack parts swapped. Every
message goes through the real Gemini model, the real sub-workflows and the real Airtable and calendar data. The
script never says "yes", so nothing can be booked.

Two things were added:

1. **`--main <file>`** runs a candidate build through the twin before it is imported. That caught three problems
   in intermediate builds (speed, Localization titles, a missing date question) and one regression tonight before
   they reached anyone.
2. **A live test booking by hand**, because the twin cannot say yes. It proves the yes → booked path, the
   calendar title and the New Clients row.

The scenario set grew from 49 to **84**: new-client cases (NC-1..9), the prompt-trim retest checklist (TC-1..10),
Music and arranger cases, and tonight's corrections, time shifts, "Did you mean…?" answers and time formats.

| Run | Build | Conversations | Purpose |
|---|---|---|---|
| 27 Sep | main v160 (live) | 245 | The first test |
| 28 Sep 12:02 | main v162 (live) | 162 | After the padded-time fix and the four decisions |
| 28 Sep 14:38 | main v163 (candidate) | 162 | First Prepare Booking build |
| 28 Sep 16:02 | main v165 (candidate) | 207 | The build that became v166 |
| 28 Sep evening | main v167 / v168 (candidates), several runs | 54 + 27 + 50 + 72 + 20 + 9 | Names from the requester's words; the fixes below |
| 28 Sep, after each import | live | 6 + 6 + 2 | Every called sub-workflow answering; roles, M booths, past date, combined question |
| 28 Sep 18:16 | live, by hand | 1 summary + "no" | ROLETEST: title, 10:00–12:00 from "10am-12nn", Engineer Daryl Reyes (Post Engineer) from "Drey" |
| 28 Sep 17:14 | live, by hand | 1 booking + cancel | The yes path and the New Clients row |

## Issue by issue

**Status:** *Live* = live before tonight's imports. *v167* / *v168* = live since 17:52 / 18:25 PHT, 28 Sep.

### From the 27 Sep test

| Issue | 27 Sep | Now | How it was fixed | Status |
|---|---|---|---|---|
| Room Availability said "every room free" when a time was padded | 79 of 199 checks | **0** (64 padded checks, all correct) | Clean the time before the calendar query, and fail closed on a calendar error, in every workflow | Live |
| The summary looked different almost every time; the title often missing | Title in 23 of 97 | **Title in every summary**; 113 of 116 written by code | Prepare Booking: code renders the summary, a check code binds the yes to it | Live |
| The prompt's own example leaked ("Dhang", "Studio 8, her usual room") | "Dhang" 3×, wrong room 10× | **0** in 206 | Client room preferences dropped; real names in examples replaced with placeholders that can never reach Slack | Live |
| "List exactly these and no others." pasted into replies | 2 of 5 | **0** | Guard Probe strips it and the tool's newer wording | Live |
| "last-resort" with a hyphen got past the filter | Seen | **Removed** | Guard Probe matches both spellings | Live |
| A client's Airtable role glued onto the name ("Sasa Abella (Producer)") | 4 of 5 | **0** (client 45 of 45) | Notes stripped from the client line; the summary prints the Airtable name | Live |
| Free rooms left out of a "which studios" answer | 4 of 5 | **2 of 2** complete | Guard Probe adds any free room the reply left out | v167 |
| (a) "for <someone not on staff>" not read as the client | Asked "Who is the client?" 20 of 20 | Read as the client | Decided in code (Booked For) | Live |
| (b) A client not in Airtable was a coin flip | 3 of 5 ask, 2 of 5 go ahead | Accepted and logged, **only if the requester typed it** | `CLIENT_UNVERIFIED` refuses a client Gemini made up | Live |
| (c) "Minimum duration" wording on short sessions | 2 of 5 | Heads-up line only, never a question | Guard Probe writes the line | Live |
| (d) "studios" vs "rooms" | Unclear | Studios drop the conference rooms and the lobby, keep the M booths | Decided in code from the requester's words | Live |
| (e) Celebrity recording asks "Music or Audio Post?" | 3 of 5 | Kept as is | Decision: no change | — |
| E1: no date named, and no date question | 5 of 5 | Asked | Prepare Booking refuses with no date; Guard Probe adds the question | Live |

### Raised in the discussions

| Concern | Before | Now | How it was fixed | Status |
|---|---|---|---|---|
| **Invented staff names** ("Daryl Javier", "Drey …") | Refused, never booked, but a wasted turn | **Typed as given, 27 of 27** (old wording: invented 2 of 2) | The prompt and tool inputs no longer ask for a full name, role or initials; code reads the engineer and arranger from the requester's words and fills the rest from Bookers | v167 |
| Garbled copies of a name or project ("REASON1" → "REazon1", "Tara Inf") | Seen 3× in 60 turns (30 Aug) | Put back to what was typed | Project, client and times read from the requester's words; the model's value is used only if every word of it was typed | v167 |
| Invented clients | Possible | Refused unless typed | `CLIENT_UNVERIFIED` | Live |
| Hidden Airtable fields reaching replies (a client's technical requirements) | Seen | **Gone** | Hidden-in-a-view is not hidden from the API; the fields were deleted, and Jessie reads 5 Clients fields | Live |
| Clients should not be required | Required | Optional: always asked; title `PROJECT / initials` with none | main v161 | Live |
| New clients should be bookable and reviewed | Refused | **Booked as typed, logged to New Clients (For Review)** | Book Session → the Jessie Log sheet. Proven by the live test booking | Live |
| A misspelt or short client name | Booked as typed | Short form → the full name; several matches → a numbered list; a near miss → "Did you mean …?" once | Prepare Booking | Live |
| External or Personal never asked | Assumed | Asked once, or taken from the record or the requester's words | Prepare Booking | Live |
| An arranger never asked on Music sessions | Skipped | Always asked; "no arranger" accepted | Book Session v54 | Live |

### Found during today's runs

| Issue | Found in | Now | Status |
|---|---|---|---|
| Summary turns 4.5 s slower (v163) | v163 run | Back to 10.6 s (redundant lookups removed) | Live |
| Localization titles picked up the client (v163) | v163 run | Always `Project Code / initials` | Live |
| A refusal pasted its instructions into the reply ("Confirm the engineer with the requester…") | v165 run | Stripped, and the refusal rewritten to be relayed as is | v167 |
| No client: External/Personal and the client asked one turn apart | v165 run | Asked together | v167 (Book Session v55) |
| "no client, it's client work" read as a client called "work" | v167 run | "client work", "client project" and the like are not names; a message saying "no client" names none | v167, fixed the same evening |
| "last Monday" answered "Let's get that booked" (it was read as a missing date) | v167 run | "That date is in the past — Monday, September 27 has already passed" (live) | v167 (Book Session v55) |
| "10am-12nn" booked as 10–11 ("12nn" not read as an end time) | v167 run | 10:00 AM – 12:00 PM, 3 of 3 and live | v167 |
| After a "no", the refused summary sent again | Live test | "No problem - nothing was booked. What would you like to change?" (3 of 3) | v168 |

## Invented names in detail

**Why it happened.** Four places asked Gemini for something the requester's message often did not contain:

- the tool's engineer input: "full name and role, e.g. Tara Lim (Post Engineer)";
- the tool's description input: "Engineer: Tara Lim (Post Engineer)";
- the prompt's description format: "Engineer: [Full Name] ([Role])";
- the title's engineer initials.

Given only "Drey", the only way to comply was to make up a surname. On the twin with that wording, "Drey" came
back as "Andre Cabuay" and "Andrei (Drei) Ramos", 2 of 2. With "exactly as the requester named them", the typed
name, **27 of 27**.

**Then made deterministic,** as "booked for" already was. Booked For reads the requester's own messages for the
engineer and arranger ("engineer Drey", "the engineer is Tara", "engineered by RG", "Drey is engineering") and
matches them against Bookers. The booking tools use that answer whenever the model's name starts with a word
nobody typed. A name that is unknown or shared (two people with "LS") is passed exactly as typed, so Jessie asks
about what the requester wrote, never about an invented name. Book Session v55 fills in the full name, initials
and role from Bookers.

The same approach covers the project, the client and the time range. It respects:

- corrections: "change the engineer to Tara";
- shifts: "make it an hour later";
- Jessie's own offers once answered: "Did you mean Daryl Reyes?" → "yes, that's him".

| | 27 Sep | v165 | v167 |
|---|---|---|---|
| Invented engineer booked | 0 | 0 | 0 |
| Invented engineer name *written* by the model | Not measured | 3 of 207 conversations | **0** (engineer 48 of 48, typed as given 27 of 27) |
| Project correct | 46 of 47 | 42 of 42 | 53 of 53 |
| Client correct | 40 of 44 | 45 of 45 | 39 of 39 |

**One dependency:** Jessie can now only recognise a nickname that is listed in that person's Bookers `Info`
("Goes by …"). A nickname people use that is missing there is asked about, not guessed.

## New clients in detail

| Decision | Enforced where | Tested |
|---|---|---|
| A client is always asked for but not required; the title is `PROJECT / initials` without one | Prepare Booking + Guard Probe | Eval NC-1..3 |
| A new client is booked as typed, for every department | Book Session | Eval NC-4..9 |
| Only a name the requester typed, never one Gemini made up | `CLIENT_UNVERIFIED` | Eval |
| "for <someone not on staff>" is the client | Booked For | Offline + eval |
| A near miss asks "Did you mean …?" once; several matches give a numbered list | Prepare Booking | Offline + eval NC-8, DYM-2 |
| External or Personal asked once | Prepare Booking | Eval NC-2 |
| **The new client is logged to the New Clients tab (For Review) for Tel to add to Airtable** | Book Session → Jessie Log sheet | **Live test booking, 28 Sep 09:15** |
| In-house arrangers can be both booked-for and the client | Book Session v54 + main v166 | Offline + eval ARR-1/2 |

**The live test booking,** end to end on main v166 / Book Session v54:

- **Request:** "Book Studio 8 on Monday, November 15 from 2pm to 4pm, VO recording, project NEWCLIENTTEST, client
  Zeta Test Media, engineer Drey, client work".
- **Summary (rendered by code):** `NEWCLIENTTEST / Zeta Test Media / DR`, 15 Nov 2027, 2:00–4:00 PM, Studio 8,
  Engineer Daryl Reyes, External, "not in the client list yet – it will be added for review", and the check code.
- **At the yes:** Book Session booked the checked summary itself. The New Clients tab got its first row (client,
  For Review, booker, project, session type, room, title, event id), and the Log tab got BOOKED and then
  CANCELLED rows.
- **Health:** every node green across the 12 turns.

## Speed

| Run | Median per turn | 90th percentile |
|---|---|---|
| 27 Sep, main v160 | 9.9 s | 11.8 s |
| 28 Sep, main v162 | 9.6 s | 11.4 s |
| 28 Sep, main v163 (first Prepare Booking build) | 14.4 s | 17.7 s |
| 28 Sep, main v165 | 10.6 s | 13.3 s |
| 28 Sep, main v167 | 10.7 s | 11.6 s |

v163's extra 4.5 s came from the model doing its own four lookups before calling Prepare Booking, which then
repeated them; v164 and later removed that. One slow slice in the evening (median 15.6 s) was Airtable, whose
lookups briefly took 2–7 s instead of about 1 s; Gemini's timing was unchanged.

## Still open, and why it is acceptable

- **Recurring-series and move summaries are still written by the model.** The guards still check what is booked;
  prepared summaries for both are on the after-launch list.
- **Free-text slips:** an invented reason for a room choice, or re-asking for a date already given. They are in the
  reply text, not the booking details, and cannot produce a wrong booking.
- **Past dates during QA:** the past-date check compares with the real today (2026), so on year-shifted 2027 test
  dates only the wording ("last Monday", "yesterday") triggers it. At launch, with the shift at zero, it applies
  to every past date as before.
- **Scorer mismatches, not Jessie:** internal-room titles use " - "; "Wednesday next week" is read as the following
  week; a session type's "usual rooms" are not a client preference; the three-studio rule for one client came from
  a Clients field that was deleted; QA-M3 and QA-M1 expectations predate the arranger question and the room ranking.
- **Data (PENDING 53):** duplicate and mistyped names in Clients, and nicknames missing from Bookers `Info`.

## Next steps

1. The weekly New Clients reminder to Tel.
2. Prepared summaries for recurring series and moves (after launch).
3. Re-run this eval after any change to the prompt or a guard. The full set takes about 35 minutes unattended:
   `./scripts/eval-run` (or `--main <file>` for a candidate).

## Appendix: running it again

```bash
./scripts/eval-run                                  # live main, every scenario, 5 repeats
./scripts/eval-run --repeat 2                       # quicker
./scripts/eval-run --main workflows/<file>.json     # a candidate main, before importing it
./scripts/eval-run --only ENG,NC,DYM --repeat 3     # a few scenario groups
```

Raw results go to `eval/results/` (git-ignored, because they hold real names and schedule data). The twin is
switched off except while a run is in progress. The script refuses any scenario that contains a "yes".
