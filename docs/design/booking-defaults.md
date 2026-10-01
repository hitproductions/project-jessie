# Booking types and booker defaults

*Drafted 1 Oct 2026 (PENDING 69, 70). Goal: fewer questions and shorter replies - Jessie works out what she can from who
is booking and what they typed, and asks only what is left, in a few words.*

## 1. The four booking types (replace External / Personal)

| Type | What it is |
|---|---|
| **Advertising** | Client work done by Audio Post, Music, and Sales & Accounts |
| **Entertainment** | Client work done by Localization; sometimes Music (artist recording, localization music) and Audio Post (films, non-advertising post-production) |
| **Internal** | Hit Productions' own purposes - no external client (meetings, Digicon, conventions, maintenance, internal events) |
| **Personal** | Not Hit Productions work - an employee's own session (e.g. an arranger's personal music project) |

Every booking still records its type on the calendar event (`Type: Advertising`) and in the Log sheet. The summary card
no longer shows it.

## 2. Airtable changes (Tel)

| Table | Change | Why |
|---|---|---|
| **Clients** | `Client Type` options -> **Advertising, Entertainment, Internal, Personal**; recode every client (External -> Advertising or Entertainment by the kind of work; in-house arrangers -> Personal; Hit's own projects -> Internal). More than one value is allowed when a client really does both | The client's record is the strongest signal after the requester's own words |
| **Clients** | Keep `Booker Type` filled (e.g. *Advertising Producer*) | A producer named as the client defaults the booking to Advertising |
| **Booking Defaults** (new, ~13 rows, one per department) | Columns: `Department`, `Default Type`, `Also Possible` (multi), `Expects Client` (yes/no), `Engineer` (*self* / *ask* / *music engineer + arranger* / *none*), `Usual Rooms` (optional) - filled from section 3 | Defaults live in Airtable, so changing one is an edit, not a workflow import |
| **Bookers** | Optional per-person overrides: `Default Type`, `Usual Room` (e.g. Dilan -> Studio E) | For the people who do not follow their department |
| **Bookers** | Clean up `Department` for people in several departments (e.g. Audio Post + Localization): either keep both and add `Primary Department`, or trust the role | Several departments = several defaults; Jessie then asks |

## 3. Defaults by department (to fill the Booking Defaults table)

| Department / role | Default type | Also possible | Engineer | Client | Usual rooms |
|---|---|---|---|---|---|
| Audio Post (Post Engineer) | Advertising | Internal (Digicon, meetings), Entertainment (films, non-advertising post-production) | self, unless they name one | usually yes | studios |
| Music - Arranger | Advertising | Personal, Internal | ask: "Who's engineering?" (a music engineer); arranger = self | usually yes - **no client: ask "Client work or your own project?"** (arrangers book their own sessions without saying so) | studios |
| Music - Music Engineer | Advertising | Entertainment (localization, artist recording) | self; ask for the arranger | usually yes | studios |
| Localization | Entertainment - **always, including people also in Audio Post: the session (a Localization session type / project code) decides** | - | self (Loc Engineer) | project code | studios / booths |
| Sales & Accounts | Advertising | Internal | ask (they book for Post / Music) | usually yes | studios, conference rooms, M booths for clients |
| Marketing, Business Development | Internal | - | none | no | conference rooms (Dilan: Studio E) |
| Video Post | Internal | Advertising? | none | no | conference rooms, Studio E |
| People & Culture | Internal | - | none | no | conference rooms, Lobby |
| IT | Internal | Entertainment | none | no | Lobby (events), studios (maintenance) |
| Management | Internal | - | none | no | conference rooms |
| Finance | Internal | - | none | no | conference rooms |

## 4. How Jessie decides (the flowchart)

**Booking type** - the first rule that gives an answer wins:
1. **What the requester typed** - "personal", "my own" -> Personal; "internal", "Hit project", "Digicon", "meeting" ->
   Internal; "TVC", "ad", "commercial" -> Advertising; "dubbing", "series", "film" -> Entertainment.
2. **The client's record** - its `Client Type` (one value). A named producer (`Booker Type` *... Producer*) -> Advertising.
3. **The client is staff** (in Bookers) -> Personal.
4. **A conference room or the Lobby, no client** -> Internal (no question).
5. **The requester's defaults** - their own override, else their department's row. Someone in two departments: the
   session decides (a Localization session type or project code -> Entertainment; otherwise their other department).
   A Music requester with no client -> step 6 ("Client work or your own project?").
6. **Ask one short question** with only that row's plausible types: "Advertising or internal?"

**Engineer:**
1. Named by the requester ("engineer Drey", "with Drey").
2. **"me", "myself", "I'll engineer"** -> the requester (bug: one booking ignored this - PENDING 71).
3. No engineer named and the requester is an engineer, booking for themselves -> the requester (live since Book Session v71).
4. The requester is an arranger -> they are the arranger; ask "Who's engineering?"
5. Anyone else booking a studio -> "Who's engineering?"
6. Conference rooms, Lobby, M booths -> no engineer.

**Client:** asked only when the department row says `Expects Client`, and never for Internal or Personal.

**One message for everything missing** - e.g. "Who's the client, and who's engineering?" - never a chain of questions.

## 5. Fixed replies (code-written, short)

| Situation | Jessie says |
|---|---|
| Summary | **TITLE** / Date / Time / Room, then "Book it? Reply yes or no." |
| Missing client | "Who's the client?" (or "...or is there none?" only for departments where none is common) |
| Missing engineer | "Who's engineering?" |
| Type not decidable | "Advertising or internal?" (only the plausible ones) |
| Missing time | "What time?" |
| Room picked for them | "I picked Studio 7 - OK?" |
| Unusual length | "Heads up: 9 hours is long for VO Recording. Book it anyway?" |
| Booked / Cancelled / Moved | "Booked." / "Cancelled." / 'Moved to 3:00 PM – 5:00 PM.' |

## 6. The `_check xxxxxxxx_` code

It is a fingerprint of the booking details on the summary. At the "yes", Jessie reads her own last message back,
recomputes the fingerprint and books only if it matches - that is what stops a booking going in with details the
requester never saw (the model once booked different details than the summary it showed). **It can leave the chat:**
once the full booking is stored (section 7), the fingerprint is computed from the four visible lines plus the
requester's Slack id, at preparation and again at the yes, so nothing needs to be printed. Same for cancel cards.

## 7. Workflow changes

- **Book Session:** the booking-type step in Check Conflicts follows section 4 (reads the Booking Defaults rows and the
  requester's department); NEED_BOOKING_TYPE and the client / engineer questions become the short fixed replies;
  Render Summary shows the four lines and stores the full field set (reference-cache data table, keyed by the
  fingerprint); the `Type:` segment takes the new values; New Clients sheet rows carry the new type.
- **Main:** Prepared Booking looks the stored booking up by the fingerprint at the yes (and refuses, re-preparing, if
  it is missing); Booked For reads "me / myself / I'll engineer" and the type words; Guard Probe stops adding lines to a
  prepared summary; the prompt's External / Personal lines go; Get Booker hands on department and role.
- **Refresh Reference Cache:** reads Booking Defaults into the cache (and main's Check Reference Cache requires it).
- **Book Series:** passes the new type; series summaries move to the same short card (PENDING 59).
- **Cancel Booking / Prepared Cancel:** the same fingerprint without a printed code.
- **Unchanged:** the confirmation gate, every guard, the calendar event's full description.

## 8. Order

1. **Thu 1 Oct:** Move Direct (68), the Slack end-to-end run, PENDING 44, the "me" engineer fix (71). Tel: Clients
   `Client Type` recode, Booking Defaults table.
2. **Fri 2 Oct (DIGICON demo):** the four types with section 4's rules, the short summary without the printed code,
   the fixed replies.
3. **After the demo:** per-person overrides, usual rooms, series cards in the short format.
