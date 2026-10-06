# Pending

Everything still open on Jessie, in one place: things blocked on Airtable, Slack, Google or the server,
known behaviour gaps, and pre-launch work. Each item says how it was found and what it breaks. First raised
2026-08-30; every item was checked against the live build when it was written.

**Item numbers are permanent**; other docs cite "PENDING 15". New items get the next number, and resolved
ones move to the bottom instead of being renumbered.

**Launch: 12 October 2026. Back-end polish ends 5 October.** Triage last updated 2026-10-06 (live: main v227, Book Series v6, Book Session v93, Room Availability v17, Cancel v22, Find v8, Move v25 - imported 6 Oct ~14:29 PHT, not yet tried in Slack; open from the 4 Oct run: 78-83; see `docs/eod/EOD-2026-10-04.md`). **Consent rebuild candidates (main v176, Book v57, Open v11, Finalize v10, Sweep v2, and a Move candidate in git at `060afd9`) predate today's builds: rebuild on live, never import as they are.**

---

## Triage: start here

### 🔴 Urgent: must be done before launch

| # | What | Blocked on / owner |
|---|---|---|
| 68 | **Move Direct: a yes to a move card moves once, in code, not through the model.** 30 Sep 17:18 (QASER, main v201): at the yes to the 9 Nov card the model called Move Booking twice in parallel - two replacements (one with the room declined), then "could not remove the original" (it was already removed by the first call). Bookings (Book Direct) and cancels (Cancel Direct) already skip the model at the yes; moves never did, so every series fix today worked around it | **LIVE 1 Oct ~11:04: main v202 (move direct + me fix)** - 11:07: the yes went to Move Booking once, directly (AMBIGUOUS_TITLE because of leftover test events - item 72). **Build first, before the 1 Oct Slack end-to-end run:** a Move Direct branch beside Cancel Direct - Booked For's approvedMove (v200) -> Move Booking once -> a code reply ('Moved ...' + the next series card). Cleanup: the extra 9 Nov 2027 QASER (Studio 8 declined, no location) |
| 33 | Launch switches: year shift, **three** `DEV_REDIRECT`s, drop `TEST_COORD` (the tag is live on Howard). **HAIST Dev stays** for now as an emergency backup (decided 28 Sep) | Howard, on 12 Oct |
| 15 | No external uptime monitor: an outage is noticed only when someone complains | Owner accounts (UptimeRobot) |
| 21 | Cloudflare answering Slack with 403 (the confirmed outage mechanism); 29 Sep: single deliveries also failing and arriving 61 s late on Slack's retry (OUTAGES, 15:41 and 16:16) | **Fix applied 1 Oct (~11:00 PHT):** a Cloudflare exemption (skip) rule for Jessie's and Posty's webhooks; both answered again at once. To do: copy the rule into OUTAGES, watch 09:25-09:35 PHT for a few days (30 Sep and 1 Oct both went silent at that minute), then mark resolved **11:18 the same day: two deliveries still arrived 66-97 s late (Slack's retry) - check Security -> Events for 03:18 UTC.** |
| 22 | Automatic backup off since 16 Sep; manual backups only | **Closed 29 Sep:** the GitHub Action was deleted (Tara); `./scripts/backup-live` by hand after imports |
| 42 | **Envoy studio tablets, read + write.** Tablet bookings are invisible to Jessie (double-book risk) | **Tel's to-do (28 Sep):** Tel reports it working; her confirmation marks it DONE in the sprint checklist |
| 43 | Studio E points at a dead calendar id: wrong availability, and its tablet never gets Jessie's bookings | **Applied 28 Sep 15:20 PHT** in Book Session v53, Room Availability v10, Move v21, Find v5 (main's disabled node goes with v165). IT still to confirm the old id is retired |

### 🟠 Soon: before the SOP is final (by 5 Oct); behaviour real users will hit

| # | What | Blocked on / owner |
|---|---|---|
| 78 | **Priority bump messages have blank names** (live 4 Oct 21:33-21:39, RED FLAG over "SMILE / Jem Lim / AEG"): "held by ... () at Oct 5", "I've asked  to move", "reply \"cleared with \"" - the incumbent's name is empty in the message and the instruction. The card should also ask "Send a request to take the booked schedule?" rather than "Book it?" | Consent engine (Book Session prepare + Open Consent Request) |
| 79 | **"cleared with <name>" circled** (same run): "cleared with eli / jeee / jess" each got a fresh card and the yes went back to PREEMPT_PENDING - the attest reply never resolved the request, and after three rounds the session type and client were asked again. The booking could not be made | main's consent reply router |
| 80 | **A priority request goes to the booker only** - decided 4 Oct: also to the booking's engineer; whoever answers first decides | Consent engine (Open Consent Request recipients) |
| 81 | **Studio F is a usual Celebrity Recording room** but the card said "Not a usual Celebrity Recording room" (4 Oct 21:33) | Airtable session-type ranking (Tel) - check Celebrity Recording's room list |
| 82 | **"anj" as a client** (4 Oct 21:26-21:36): passed as a new client "Anj" and later read as engineer; did not offer Angela dela Calzada (client) or Anj Villegas (staff, "goes by Anj"). A name that matches both a client and a staff alias should be asked ("Angela dela Calzada, the client, or Anj Villegas?") | Book Session client check + Booked For |
| 83 | **An M booth asks "What's the meeting title or what is M6 being booked for?"** (4 Oct 21:29) - an M booth hold is titled with the booker's first name ("M6 - Howard", v84), so nothing should be asked | Book Session (MISSING_DETAILS for an M booth) |
| 91 | **A taken date in a series should get an alternative, not only be left out** (asked 6 Oct after the taken-date test). Decided: (1) another usual room at the same time, else (2) the same room at the nearest free time that day within 8 AM - 10 PM, else (3) left out and said; single dates are changed before the yes ("skip the 15th", "use Studio F on the 15th", "make the 15th 7-10pm") with a new card | **LIVE 6 Oct ~16:16 PHT (Book Session v93, Book Series v6, main v227; before + after MATCH). Verified in Slack 16:20-16:22 (messages sent by Claude with Howard's go-ahead): "book studio 1 every monday and friday, 4 sessions starting oct 8, 10am-12pm, localization editing, project NET-BUGHAW, engineer jetrho" -> card with Fri 8 / 15 in Studio 1 and Mon 11 / 18 "· Studio 2 (Studio 1 is taken)" (NET-BUGHAW, Jo Anne Chua, holds Studio 1 9 AM-10 PM on Mondays); "use studio 6 on the 18th" -> new card, 18 Oct "· Studio 6" (the model passed `changes` right); yes -> "Booked 4 sessions"; calendar: 8 + 15 Studio 1, 11 Studio 2, 18 Studio 6, 10-12, Jetrho Ty. Not seen live: the time swap (no other room free) - offline only.** Built: Offline: sim-series-alternatives 27/27 (real VO Recording ranking: room swap, time swap, the nearest-slot rule, an unidentified event as busy, left out with the reason, the first date moved, skip / room / time changes, a chosen room that is taken, every date skipped, the yes booking each date in its own room and time, single bookings unchanged), sim-series-direct 37/37, test-nodes 603 ok. Not yet tried in Slack: the model passing `changes` |
| 90 | **A yes to a series card re-sent the card** (live 6 Oct 15:13, main v222: ASIM KILIG every Friday x3) - the second yes booked all three (8 / 15 / 22 Oct 2027, Studio 7, created 15:14:02-15:14:53, so ~75 s for three). Gate Context never recognised v204's short series card as approved | **LIVE 6 Oct ~15:39 PHT: main v226 + Book Series v5 (main before + after MATCH; Book Series before MATCH, after-import download still to file). Verified in Slack 15:40-15:41: the ASIM KILIG request -> code-written card (27 s) -> one yes -> "Booked 3 sessions" and exactly 3 events (8 / 15 / 22 Oct 2027, Studio 7, created 9 s apart). 15:47-15:49: a taken date - BLOCKER in Studio 7 on 15 Oct 4-5 PM, then the DINOS series -> card "Dates (2)" (8 / 22 Oct) + "Heads up: Studio 7 is taken on Friday, 15 October 2027 - that date left out." -> yes -> "Booked 2 sessions", calendar: DINOS on 8 and 22 Oct only, BLOCKER untouched. Still to try: a second yes during booking. Next (asked 6 Oct): offer an alternative for a taken date instead of only leaving it out - PENDING 91.** Built: Review (6 Oct): Expand Series taken off the agent and every mention of the old path removed; an in-progress lock so a second yes during booking cannot book the series twice; no empty "Engineer:"; one room per series. Prepare Series writes the card in code and stores the series; the yes is booked by Series Direct with exactly the card's dates - no model. Offline: sim-series-direct 37/37 (the full round trip on Book Session's real prepare code, M booth all-day and conference-room series, the lock), sim-series-yes 6/6, test-nodes 603 ok. Not yet tried in Slack: the Prepare Series tool (the model must call it - gotcha 23); a 16-date series prepares every date through Book Session (~1 min before the card). M booth dates with a standing hold are left out of a series card (no consent request from a series) Test events to cancel: ASIM KILIG x3 |
| 89 | **A "?" after "Booked." was answered "Please reply yes to confirm this booking, or no to cancel it."** (live 6 Oct 14:54, main v222): the booking had already been made at 14:53 - nothing was pending. Model-written; nothing wrong was booked | Guard Probe: drop a "reply yes to confirm" line when the last card was already booked this conversation (Book Direct ran), or answer a bare "?" with what was just done |
| 88 | **"10-12pm" questioned as "10 AM to 12 PM, or 10 PM to midnight?"** (live 6 Oct 14:46, main v222): after "post", Jessie said "The end time needs to be after the start time" - Booked For reads 10:00-12:00 correctly (offline, v221 and v222), and Book Session's times are corrected from it, but Room Availability's are not, so a model guess of 10 PM-12 PM there comes back as a bad window. Unconfirmed without the execution (14:46:17 turn) | **Built 6 Oct: main v223 (availability times) - candidate, NOT imported, next batch.** Room Availability's window takes Booked For's time range like Book Session's; whole-day checks untouched. Offline: sim-ra-time 7/7, test-nodes 603 ok |
| 87 | **A time in the project, and filler as the client** (live 6 Oct 14:35-14:37, main v221 / Book Session v91): "mixing session. project dinos 10-12pm" + "that will be all" to the client question -> card "DINOS 10-12PM / That Will Be All / HL" | **LIVE 6 Oct ~14:45 PHT (main v222 / Book Session v92, before + after MATCH); verified in Slack 14:45-14:47: card "DINOS / HL", "client? i don't know" and "ewan" asked again, "wala" = no client.** Built: A time or date ends the project; filler words are never a client (asked again). Offline: sim-time-and-filler 38/38, test-nodes 603 ok. Known gap (older): a client starting with "The" ("The Voice Kids") is not read from a bare answer - the model's value still passes |
| 86 | **A booking named without a date was found only if upcoming** (Slack 6 Oct 14:55: "when was proj sunny side up booked?" found the 19 Sep 2027 booking, 17 days back - the reply did not say it had passed; the past + upcoming question and a past cancel card not yet tried) (decided 6 Oct: e.g. cancelling one made the previous week by name) | **LIVE 6 Oct ~14:29 PHT (main v221 / Book Session v91 / Room Availability v17 / Cancel v22 / Find v8, hand imports, before + after MATCH).** Built: main v221 + Cancel Booking v22 + Find Booking v8 (name search includes past) ** Last 60 days and ahead; one match -> the card (past: a heads-up); a past and an upcoming booking with one name -> always said, coming up first. Offline: sim-name-search-past 31/31, test-nodes 603 ok. sim-cancel-by-title / sim-find-by-title assert v21 / v7 wording (pass on those builds). Move by name goes through Find Booking, so it gets the same list; Move Booking itself is unchanged |
| 85 | **Past sessions can be booked** (Slack 6 Oct 14:52-14:53: "december 30 2026" booked for 2026, not 2027 - PHONE CASE / Manny Perez / HL, Studio 7, a REAL calendar date to cancel; a past date not yet tried) (decided 6 Oct): a 2026 date was refused during QA (Gate Context's past-date notice told the model not to book it; Book Session and Room Availability refused PAST_DATE) | **LIVE 6 Oct ~14:29 PHT (main v221 / Book Session v91 / Room Availability v17 / Cancel v22 / Find v8, hand imports, before + after MATCH).** Built: main v220 + Book Session v91 + Room Availability v17 (past bookings allowed; include v219 / v90) ** A year is taken as written ("oct 1 2026" = 2026 during the year shift); yesterday / last Monday / N days ago resolve; the card says "Heads up: this date has already passed." Offline: sim-past-bookings 25/25, test-nodes 603 ok, test-gate 69/69. Not changed: Move Booking and Book Series do not refuse past dates themselves; a past series has not been tried |
| 84 | **The client was not asked with the first questions, and a refusal's instruction reached Slack** (live 6 Oct 13:32-13:33, main v217 / Book Session v88): "book studio 8 next thu 3-5pm" -> "What kind of session is this? What's the project?" (no client); after "post mixing" -> "Nothing was booked. If there is no client, leave it empty." (CLIENT_UNVERIFIED pasted by the model) | **LIVE 6 Oct ~14:29 PHT (main v221 / Book Session v91 / Room Availability v17 / Cancel v22 / Find v8, hand imports, before + after MATCH).** Built: main v219 + Book Session v90 (client until none; include v218 / v89) ** Decided 6 Oct: the client is asked until they name one or decline ("none", "no client", "nope", "n/a", "wala" ...), no cap. Offline: sim-ask-client-first 23/23 on v218/v89 (v217/v88 reproduce the live text), sim-client-until-none 44/44, test-nodes 603 ok, test-gate 69/69. Then a Slack check: the same three messages, then "john ableton" alone, then "none" on a fresh booking |
| 51 | **Padded timestamp reads as "every room free"** (eval 27 Sep): Room Availability 40% of checks; same shape in Book Session and Move Booking | **Fixed and verified live 28 Sep**: eval after import, 64 of 140 checks padded, all 64 returned the real busy rooms, 0 "all free" (was 61/61) |
| 53 | Clients table data: 7 duplicate names, 3 names with stray spaces, 3 non-client rows. Bookers (28 Sep, raised with Tel): Via Aceron's Info to list Loc Engineer; BP Valenzuela's Initials trailing space; Eddie Boy Vargas retiring - remove from Bookers when he leaves; any nicknames people use for engineers added to Info (v167 reads names from the requester's words against Info) | Airtable (Tel) |
| 52 | M2 and M6 had `Active / Bookable` unticked, so Jessie never listed or offered them | **Done 28 Sep:** Tel ticked both; live room list 25 → 27 at 11:35 PHT |
| 50 | Clients optional + new clients to a `New Clients` sheet; client room preferences dropped (main v161 / Book v49, LIVE 28 Sep) | **Done 28 Sep:** Tel deleted the hidden fields; Clients = Name, Importance, Notes, Booker Type, Client Type; live lookups confirmed |
| 46 | Speed cache (main v158) FAILED live — Ref Store hung writing static data; rolled back. Do not push v158 | Fix + prove on a test workflow |
| 54 | **Gemini invents staff names and corrupts copied details.** v165 eval: "Andrian \"Drey\" Sison", "Daryl Aquino" for "Drey"/"Daryl" (refused, a wasted turn, and the refusal leaked its instructions); earlier "REASON1" → "REazon1", "Tara Inf". Cause: four places asked the model for a full name, role and initials it did not have | **LIVE 28 Sep 17:52 PHT** (main v167 + Book Session v55; v168 10:39): the prompt asks for names as typed (27/27 in the eval twin, was 0/2); engineer, arranger, project, client and times are read from the requester's own words and win over the model's; v55 fills name, role and initials from Bookers |
| 47 | Date guard LIVE (main v159 / book v47): watch for DATE_MISMATCH refusals in QA | Everyone (report false refusals) |
| 34 | A1: free rooms sometimes left out of an availability answer | v165 eval: "which studios" dropped the M booths 3/3. **LIVE 28 Sep 17:52 PHT** (main v167 Guard Probe adds any free room the reply left out); live eval: M booths listed |
| 26 | Can claim "I've asked the current holder" without doing it | **LIVE 28 Sep 16:28 PHT** (main v166 Guard Probe: withdrawn unless Book Session / Move opened it that turn) |
| 71 | **"me" as the engineer ignored** (1 Oct 09:26, DASHING): "book studio 8 for me ... for anj" -> "angela" -> "Who is the engineer for this session?" (should have been the requester - an engineer); then "me" -> "No engineer was named, so you're down as the engineer" (it was named) | **Book Session half built in v73.** **Main half built in v202** (Booked For reads "me"); the Book Session half (default to the requester instead of asking; no note after "me") goes with Friday's Book Session build. Build with 68 on 1 Oct: v70's colleague-out-of-the-engineer-slot step defaults to the requester when they are an engineer, instead of asking; "me" / "myself" / "I'll engineer" / a bare "me" to the engineer question = the requester, and no note |
| 72 | **Two bookings with the same title on the same day can't be moved or cancelled by name** - AMBIGUOUS_TITLE (1 Oct 11:07: QASER at 10-12 and 3-5 on 2 Nov, the 3-5 one left from the 30 Sep test). Real case: a project with a morning and an afternoon session | Build: the card already shows the booking's current time ("Now: 10:00 AM - 12:00 PM") - pass it (Move Direct's approvedMove, Cancel's card) and let Move Booking / Cancel Booking pick the one starting then. Move Booking v26 + Cancel v21 + main |
| 73 | **[RESOLVED - LIVE 1 Oct ~14:51 / 14:53: main v207 + Book Session v75 (engineer question); verified in Slack 14:53-14:56: the series asked only "Who's the client?", then the short card with HL]** **A series asks "who's engineering?" of an engineer requester** (1 Oct 14:36, live E2E on v206): "book qaseries every monday in november 2027 2-4pm vo recording studio 8" -> "Who's the client, and who's engineering?". A single booking defaults the engineer to an engineer requester in code (Book Session v73 / main v203); the series path asks first, then the summary did put HL in. Harmless (one extra question, nothing wrong booked) | Book Series / Booked For: apply the same default on the series path, or have Guard Probe drop the engineer question when Booked For already named one. Small; after the demo |
| 74 | **Default rooms - parked, with Tel** (1 Oct): Bookers "Default Type" is each person's default room. LIVE in code since 1 Oct ~15:11 (Book Session v77 / main v208): no room named -> the default room of the person the booking is for, if free and a usual (Priority) room for the session type, card note "Your usual room."; else the usual pick. Only Dylan Diaz has one (Studio E). Not yet tried in Slack | Tel fills in Default Type for whoever has a usual room (the field name says "Type" but holds rooms - rename to "Default Room" if convenient; Jessie reads "Default Type", so a rename needs a one-line build). Then one Slack check (set a test default, wait 15 min for the cache) |
| 76 | **Booking Defaults table (Airtable, Tel, 1 Oct ~19:30)** - 12 rows by department / role: Default Type, Also possible, Engineer, Expects client, Usual rooms (free text, as in `docs/design/booking-defaults.md`). The Bookers "Default Type" field (per-person default room) was removed with it, so Book Session v77's default room reads nothing now (harmless - the usual pick applies). The rows agree with the type rules in code (Book Session v73 `__tyDept` / `__decideType`) | Decide: wire the table so Tel can change the type defaults from Airtable (Default Type / Also possible map cleanly) - Engineer and Usual rooms are prose ("self, unless they name one", "studios, conference rooms, M booths for clients") and would need fixed values first. Per-person default rooms (Dilan: Studio E) now sit in the Marketing row's note |
| 77 | **[RESOLVED - LIVE 2 Oct ~12:40 / 12:42: main v212 + Book Session v85; verified 12:40: "What kind of session is this? And what time?"]** **The model sometimes asks for details itself, so the "ask everything at once" rule does not run** (2 Oct 12:29, live on main v211 / Book Session v84): "book studio 7 in 2 days, project thank you, client sir vic" -> "What session type is this? (e.g. Celebrity Recording, Post Mixing, VO Recording, etc.)" - no "And what time?", because the model asked before calling Prepare Booking (Book Session v84 adds the missing date / time only to its own questions). The next answer still gave the right card | Guard Probe (like v164's day question): on a booking request whose words name no time, add "And what time?" to the model's question when it does not already ask for one. Small, main only |
| 75 | **Meeting-room bookings: title department and engineer line** (1 Oct, live E2E on main v208 / Book Session v77): "book likha ... for a meeting" was titled "LIKHA - Audio Post" at 14:19 and "LIKHA - Post" at 15:19 (the model writes the department segment), and the Internal event carries "Engineer: Howard Luistro (Post Engineer)" from the engineer default. Harmless for the demo: Type: Internal was right and nothing else differed | Write the internal-room title in code from the requester's Bookers Department (exact name); skip the engineer default (and the Engineer line) for a Meeting / Event or an internal room. After the demo |
| 69 | **Short, plain-language booking chat** (DIGICON video demo to Sir Vic, end of week - working in Slack): the summary shows only the title, Date, Time and Room; questions and notes brief, never "terms and conditions" | **LIVE 1 Oct ~11:52 / 11:56: main v203 + Book Session v73 (types + short summary).** **Cancel and series cards: main v204 + Cancel Booking v21 (short cancel + series cards), LIVE 1 Oct ~14:10 / 14:13** - no printed check code anywhere. **Decided 30 Sep: hide the rest always** (the engineer is in the title's initials; session type and booking type are for the system, not the booker) - every detail still gathered and written to the calendar event. **Scheduled Fri 2 Oct morning** with 70, after 68, 44 and the 1 Oct Slack run |
| 70 | **Booking type becomes four categories: Advertising, Entertainment, Internal, Personal** (was External / Personal), asked only when it cannot be worked out, in few words | **Built 1 Oct in Book Session v73 / main v203 (code defaults by department; the Booking Defaults table in Airtable is still to come).** **Decided 30 Sep:** in order - (1) what the requester said; (2) the client's record wins (a Hit convention VO can be Internal - department alone is not enough); (3) removed 1 Oct - a client who is staff is not always Personal; (4) no client -> "Is this a Hit project or your own?" (Internal / Personal); (5) a new client who is not staff -> department default (Audio Post, Music = Advertising; Localization = Entertainment), else "Advertising or entertainment?". Internal = Hit's own work, no client. **Tel recodes Clients `Client Type` to the four by Thu 1 Oct.** Build Fri 2 Oct with 69. **1 Oct: scope widened** - defaults by department and role (Booking Defaults table), fixed short replies; plan in `docs/design/booking-defaults.md` |
| 27 | Can open the same consent request twice | Build |
| 28 | Booking over your own booking asks *you* for consent | **LIVE 28 Sep 16:28 PHT** (Book Session v54, Move v22: SELF_BOOKING → "you already have it") |
| 23 | After "room taken", re-offers the same failed slot | **Built 28 Sep:** ROOM_OCCUPIED lists the usual rooms actually free in that window (Book Session v53, live) |
| 29 | Music sessions don't require an arranger | **LIVE 28 Sep 16:28 PHT** (Book Session v54): asked whenever a Music session's type lists an arranger; "no arranger" accepted |
| 30 | Celebrity sessions don't suggest a holding room | **LIVE 28 Sep 16:28 PHT:** prepared summary notes it from Room Requirements |
| 44 | Tells the requester "Booked" even when the room declines seconds later (clash she can't see) | Build |
| 35 | Timestamp junk-guard not yet in Move Booking / Expand Series | LIVE 28 Sep with 51 (Move v20, Expand v2) |
| 37 | Never run live: priority request timing out; same-day / next-day M-booth windows | Test now / watch at launch |
| 38, 16 | 2027 test events still on the calendar | **38 mostly done 29 Sep:** today's five cancelled through Jessie; BROWSE, NET-KUBA / JP, M4 - Howard, PROJ ORANGE, NOREGRESSION, CELEBTEST removed by Apps Script (14:35 PHT); the consent-test M1/M4 holds are gone. SMOKETEST stays. **Left: GUARDCHK (16)** |
| 55 | **Two cancels in one message show one card.** Both were prepared, only the last card reached Slack | Build (main) |
| 56 | **A cancel with no date guesses the date from the conversation** instead of looking it up | **RESOLVED 29 Sep, verified live through Slack 17:53-17:55 PHT** (Cancel v20, Find v7, main v191): "cancel QANODATE" with no date -> Find Booking by name -> card for 7 Oct -> cancelled |
| 57 | **A late Slack retry after a re-send runs twice**: two identical summaries (29 Sep 15:41, 16:16) | **LIVE 29 Sep 17:20 PHT:** main v189 Duplicate Check |
| 58 | **Lowercase initials / a bare "bp" answer refused**; an unbacked "not on the staff list" | **LIVE 29 Sep 15:59 PHT:** main v188. Bookers: BP Valenzuela's Initials to BPV (Tel), keep BP in Info |
| 59 | **Series summaries and events:** model-written summary lines lose their bold labels and gain a leading space; no Booking Type line; the created events carry no "Type:" (Book Series does not pass the booking type) | Build (after launch unless quick): prepared series summaries; pass bookingType in Book Series |
| 60 | **Two cancels in one message: the model sometimes prepares only the first** ("cancel QAS3 ... and LIKHA - BD ..." - one card, no Next line); three dates of one title worked | Watch; a deterministic split would need the titles parsed from the message |
| 61 | **"no" to a move card re-offered the corrected move** instead of cancelling it (29 Sep 22:29: the earlier "3-6pm not 6-7" still counted); a second "no" cancelled | **LIVE 29 Sep 23:10 (main v193), verified 23:16 through Slack** |
| 62 | **"This week" availability checks one day** (29 Sep 23:17: one Monday-to-Sunday window starting on a day already past - a room was "taken" if anything touched it all week; "Dates checked" named only Monday) | **LIVE 30 Sep ~16:14: Room Availability v12 (multi-day check fix) + main v197 (this-week range fix); verified 16:15-16:16 against the calendar.** A window over several days is answered day by day, the same hours each day (whole days when midnight to midnight, up to 14 days): per room free / taken by what and when, or each day's free rooms; "this week" runs from today |
| 63 | **A change right after a series moves one date without asking which** ("make it 3pm instead" after a 2-date series -> the 9 Nov date only) | **LIVE 30 Sep: main v198-v201.** Decided: ask which date. Verified live: the question, a picked date, "all" -> the 2 Nov card (code) with Next, the yes moves 2 Nov only (v200), the next card's yes goes through (v201). **Left: item 68** - at the 9 Nov yes the model called Move Booking twice at once: one extra 9 Nov event (room declined), and a misleading "partial" message |
| 64 | **Session-type shorthand as project / client** ("book isr ..." -> ISR / ISR / EG), and any client that is only the project again | **LIVE 30 Sep ~13:20:** Book Session v68. Optional: Tel adds an "Also known as" field to Session Types (e.g. VO Recording: ISR, In-Studio Recording) - needs main's Room Table to pass it on as `aka` |
| 65 | **A colleague booked for became the engineer** ("book orange studio 7 for anj" -> "Angelo Villegas is down as the engineer"; Anj is a Music Arranger), and a music session type was assumed | **LIVE 30 Sep ~14:03: Book Session v70 (for-person fix) + main v196 (client nickname search); verified 14:06-14:16** (which-Anj asked; "angela" -> QAANJ / Angela Dela Calzada / HL, External, no "(for ...)"). Decided 30 Sep: with no engineer named and a requester who is an engineer, the requester is the engineer - in code from Book Session v71 (LIVE 30 Sep), with a note on the summary. The two Anjs: Angelo Villegas (Bookers, Music Arranger) and Angela Dela Calzada (Clients, Advertising Producer, Notes "Goes by Anj") - asked which one. Still open: the session type was assumed (Music Vocal Recording) with none typed - a judgement call, like QA M2. Nicknames shared by two clients, or a client's nickname that is only in the Name, are not covered: a "Goes by" in Clients Notes is what makes it work |
| 66 | **The date is forgotten when the requester answers within seconds** ("no client" 3 s after the question -> "What is the date for this booking?"; "tomorrow" was in the request) - static data is saved only when a turn finishes | Built: main v195 (date carry fix) reads the date from the requester's earlier messages when nothing is carried. **LIVE 30 Sep ~13:28, verified 13:29** (Turn Log: v194 exec 18503 MISSING_DATE with the reply 3 s after the last row; v195 exec 18526, same 3 s gap, date carried). Other static-data carries (the epoch) have the same race - a reset answered within seconds is the case to watch |

### 🟢 Additive: fine after launch

| # | What | Blocked on / owner |
|---|---|---|
| 36 | Booth holder can't book their own held booth directly | Build |
| 1–4, 7 | Airtable room-data contradictions (stereo rooms marked 5.1, Studio 1, Studio E, a trailing space, duplicate rankings) | Airtable (Tel) |
| 10 | Backfill each new window (Jan onward); optionally match the alt-email column | Per window |
| 11 | Explore an n8n update | Server |
| 13, 18, 39 | Speed: first Code node ~3.5s, first outbound call ~4s, new staff-list reads ~1s | Server / later |
| 40 | Leftover snapshot files from renames in `workflows/live/` | **Done 28 Sep:** approved; current snapshots refreshed first, then the 5 old-name files removed (all 5 ids still active under their current names) |
| 41 | `Booked For` notice quotes three words instead of the name | **LIVE 28 Sep 16:28 PHT** (main v166) |
| 67 | **Day-by-day availability layout:** a blank line between days, and within each day the studios, the M booths and the vocal booths on separate lines | Build (Room Availability + Guard Probe); parked 30 Sep |

**Resolved** (details at the bottom): 5, 6, 8, 9, 12, 17, 19, 20, 24, 25, 31, 32, 45. **Item 14** is a permanent
known constraint, not a task.

---

## 🔴 Urgent: details

**32. Thread-broadcast errors: harmless duplicates, not lost replies. RESOLVED — v156 LIVE 2026-09-26.** *Corrected
2026-09-26 — the first write-up of this, which came from Tara's side, was wrong about the impact.*

When a tester replies in a thread with **"also send to channel"** ticked, Slack sends **two** events:

| Event | Sender at top level | What happened (24 Sep, Tricia) |
|---|---|---|
| `thread_broadcast` — the reply itself | yes | **processed normally**: execs 10920, 10924, 10929 all succeeded, and Jessie booked and replied |
| `message_changed` (inner `thread_broadcast`) — Slack's notice that the thread was updated | no | `Get Sender` looked up an empty user id → `user_not_found`: execs 10921, 10925, 10930 |

So **no reply was lost and no booking was missed**. The three errors are the duplicate notice failing. It
is log noise, not a user-facing failure — downgraded from urgent.

**Do not fix this by making `Get Sender` read the nested `message.user`.** That would send the duplicate
notice through the agent too, and Jessie would process every thread-broadcast reply **twice**.

**The fix: v156, `DM filter` only.** Two conditions added, dropping `subtype` `message_changed` and
`message_deleted`; `thread_broadcast` and plain DMs pass exactly as before. Built from a fresh pull of live
v155, so it reverts nothing. Replayed against the seven real events from 24 Sep: every success still kept,
every error dropped. 209 checks + 28 scenarios pass. `leftValue` is `$json.subtype || ''` so an absent
subtype is a string under strict type validation, not undefined.

**Pushed 2026-09-26 03:41 UTC and smoke-tested live:** Tara's plain "test" DM (exec 12116) passed `DM filter`,
ran 24 nodes and got a reply; Jessie's own echo (12117) passed `DM filter` and stopped at `Loop filter` as
designed. `reapply-main-fixes --check`: all v151–v155 fixes present.

**33. Launch switches: flip together on 12 Oct.** Full detail and the post-flip checks are in
[`docs/launch-checklist.md`](docs/launch-checklist.md). In short: `YEAR_SHIFT` → 0 in `Gate Context` together
with the prompt's `plus({ years: 1 })`; `DEV_REDIRECT = ''` in **three** places (Cancel → Build Recipients,
Move → Build Recipients, Open Consent Request → Build Request; the third was missing from the checklist
until 2026-09-25); and a decision on `HAIST Dev` god-mode (keep for Howard/Tel/Genzo, or pull).

**15. The instance goes unreachable to the outside world for hours, recurring, mechanism unproven.**
Recorded so far: 2026-09-02, twice on 2026-09-03, and a long one on 2026-09-05.
Each time, Slack messages stop producing executions while n8n keeps running
scheduled work and serving HTTP — so the container is healthy and the inbound path,
not n8n, is failing. Recoveries have happened with nobody touching it.

The 2026-09-05 window is the best-documented. Jessie's last inbound execution was
00:05, the next was 13:03 — about thirteen hours. Both bots came back at the *same
second*: Posty at 13:03:13, Jessie at 13:03:31. Two separate bots resuming together
means the shared front door recovered, not either bot — strong support for the
Cloudflare tunnel / host DNS being the cause. The daily pruner (04:00) ran straight
through the outage, confirming the scheduler stayed alive. Note the reported "up by
10:30" was not real: no message got through until 13:03, so a test at 10:30 was
still hitting silence.

Independent, external corroboration arrived by accident: the nightly backup runs on
GitHub's servers, outside this network, and it failed to reach the API at ~05:00
Manila on both 2026-09-04 and 2026-09-05 — an outside client getting nothing,
confirming the site was unreachable from the internet at that time, not merely
internally wedged. (The backup now retries and skips cleanly instead of crashing,
and was moved off that window.)

Still the only hints at the moment of failure are outbound DNS errors (`EAI_AGAIN`,
"DNS server returned an error") minutes before. What would settle it: a real
external uptime check on the public URL (catches it live, alerts even when the
network is down, needs no server access), and the `cloudflared`/tunnel container's
own log from a failure window (needs shell). The nightly backup and daily pruner
are in place; a watchdog and an uptime check are not yet. Pruning once correlated
with recovery but was never cleanly isolated from toggling, and the 2026-09-05
recovery happened with nobody pruning, so "the execution table filled up" is not
the cause.

**21. The Cloudflare change — and nobody on this project can make it.** The Cloudflare
account for `signal.hitpromanila.net` belongs to IT, not to anyone working on Jessie. Do
not write this up as something the reader can go and do; it has to be **requested**.

What to ask for, in this order:

1. **Look up ray id `a3b90afebfcd9b19`** in Security → Events. It names the exact rule or
   service that issued the challenge. One lookup, and the cause stops being a shortlist.
2. **Filter Security → Events to `signal.hitpromanila.net` for 21:00–22:00 UTC on
   15 September** — a measured outage hour. Slack's blocked requests should be there.
3. **The fix: a WAF skip rule on `/webhook/*` for that hostname**, exempting it from bot,
   reputation and challenge logic. Needed before launch (12 October) regardless of what the
   lookups say — any rule that can issue a challenge on that path will take both bots
   down again, and **no automated caller can ever solve a challenge**.
4. While they are in there: allow the GitHub Actions ranges, or include the API path in
   the skip, so the nightly backup can run again (item 22).

**Event Subscriptions is enabled — do not send anyone to check it.** Slack's email said
they had turned dispatch off, but events have arrived since on both nights measured
(exec 8953, 16 Sep 07:00 PHT, replied in 19s). Nothing arrives with dispatch off, so it
is on. Either Slack re-enabled it once requests started succeeding, or the wording was
loose. Worth one glance only if the bot is silent for a full day and the Cloudflare side
is known good.

**22. Closed 29 Sep 2026: the nightly backup Action was deleted** (Tara's call); backups are
`./scripts/backup-live`, run by hand after imports. History below.

**The nightly backup is disabled, and `workflows/live/` is stale.** Disabled
manually on 2026-09-16 (`gh workflow disable nightly-backup.yml`) because every run
since 14 September failed on a Cloudflare Managed Challenge — the runner is a
datacenter IP and cannot solve one.

**Refreshed by hand on 2026-09-17** — `./scripts/backup-live` run from a Mac works
fine, because a residential IP is not challenged. That is the stopgap while the
GitHub job is off: run it locally and commit, rather than letting the snapshot age.

This is the rollback artifact, so while the job is off the repo is the only copy of
what n8n runs, and it is only as current as the last hand run. Re-enable with:

```bash
gh workflow enable nightly-backup.yml
```

Do that as soon as the Cloudflare rule in item 21 is fixed — a WAF skip on `/webhook/*`
plus API access for the runner, or an allowlist for GitHub's ranges. Until then, either
run `./scripts/backup-live` from the VM (not challenged there) or take a manual snapshot
before any risky change. See `docs/outages/OUTAGES.md` for the captured challenge response.

**42. Envoy studio tablets need read + write with Jessie before launch.** Moved to pre-launch by Howard on
2026-09-25; Tel's design had it post-launch ([`docs/design/envoy-calendar.md`](docs/design/envoy-calendar.md)).
People will book on the door tablets (Envoy Rooms) as well as through Jessie, so both must see each other.
- **Write (Jessie → tablets): works, except Studio E.** Jessie invites the room's resource calendar on
  every booking, which is the surface Envoy reads (validated live 2026-09-23 with a Studio 7 booking).
  Studio E is broken by item 43.
- **Read (tablets → Jessie): not built.** A tablet booking lands on the room's resource calendar only,
  never on KDC Bookings, which is all Jessie reads, so she can't see it and could double-book over it.
  Tel's recommendation is the **mirror** ([`docs/design/envoy-mirror-build.md`](docs/design/envoy-mirror-build.md)):
  one scheduled workflow (~2 min) copying Envoy bookings onto KDC Bookings, where every guard already looks.
  **v2 built 2026-09-26** (`workflows/envoy-mirror-v2.json`): Google calls moved to HTTP Request nodes with
  the existing credential, and it fails closed (a failed room read deletes nothing, a failed KDC read writes
  nothing). Offline-tested (`./scripts/test-mirror`), **never imported**. Import steps are in the design doc.
  v1 is superseded; don't import it.
  **2026-09-26:** imported through the browser by Tel (not yet published). Reads all 27 room calendars; a
  tablet test booking was copied to KDC Bookings correctly. The file was then revised: successful runs not
  saved (database-fill risk at 720 runs a day), copies take the tablet booking's full room-name location
  (Move Booking compares locations exactly and would not have seen a bare "Studio 7"), and failures turn the
  run red. **Revised file re-imported 16:35:** both test copies updated to the full room-name location
  (confirmed on KDC Bookings), and a tablet edit (end time shortened) was followed. Jessie can't be asked
  about a tablet booking before launch: with the QA year shift "today" is 2027 to her (she called Studio 7
  free) and an explicit 2026 date is refused as past. Instead her live Room Availability and Move Booking code
  was run against the real copy: BUSY and ROOM_OCCUPIED (the old bare "Studio 7" copy let the move through).
  **Left: release a tablet booking → `deletes: 1`, then publish.** Known edge case, not
  fixed: Move Booking's exact-location check still won't see a copy when the booking being moved is a
  two-room booth pairing (its location lists both rooms). Its one weakness is the poll gap (a tablet booking is
  invisible to Jessie for up to one interval). The heavier read-side change
  ([`docs/design/envoy-jessie-readside-build.md`](docs/design/envoy-jessie-readside-build.md)) closes that gap
  but rewrites three hot-path workflows; hold it unless the gap bites.
- **Order:** item 43 first, then import and test the mirror on year-shifted test bookings, then confirm
  both directions live (a Jessie booking appears on the tablet; a tablet booking blocks Jessie).
- **What each mirrored copy needs: nothing Jessie-specific (reviewed with Howard 2026-09-25).** The
  scaffold writes the title `<Room> - <tablet title>`, location `<Room>`, the times, a description ("Created
  by Envoy (mirrored). Manage this booking in Envoy.") and a private `envoyMirrorSource` marker for
  update/delete reconcile. That's enough for availability, conflicts and lookups: rooms are found by
  location and the title's first segment. No `ref:`/`SType:` is deliberate. Jessie mustn't cancel or move a
  copy (the mirror would recreate it next run; manage it on the tablet), and an emergency same-day booking
  should never be preemptible. **Keep:** the copy must **not** invite the room resource, or the tablet shows
  a duplicate and the room declines it.
- **Polish, not needed for launch:** (a) when asked to cancel or move a mirrored booking, reply "That was
  booked on the studio tablet. Cancel it there." instead of the generic no-reference refusal (detect
  `envoyMirror` / "Created by Envoy (mirrored)" in Cancel and Move); (b) if Envoy records who booked, copy
  their name onto the mirror, so Jessie can answer "who has Studio 7?" for same-day coordination.

**43. Studio E points at a dead calendar id.** Found by Tel 2026-09-23
([`docs/design/studio-e-id-fix.md`](docs/design/studio-e-id-fix.md)); still live on 2026-09-25 (Book Session's
room map has `c_18807te03d2sqh0lmtal9sbb04gao`, which returns not found; the real Studio E resource is
`c_1888r4bbc2lhqgndmprism70nft64`). Effects: a Jessie booking of Studio E invites the dead resource, so it
never reaches the real room calendar or its tablet; and Studio E events are never matched to the room, so
availability can call Studio E free when it isn't. The old id is in **five** live workflows (checked 2026-09-25): Book Session, Room Availability, Move
Booking, Find Booking and main. Each needs the new id (pull each first; count only the nodes, not n8n's
`activeVersion` copy, gotcha 8). A small, mechanical change, and step 1 of item 42. **2026-09-26: fix built, not applied.**
`./scripts/fix-studio-e` makes the swap in a fresh pull (nodes only). Dry-run on the 25 Sep backups: 6 places
(Book Session has two, `Check Conflicts` and `Create Event`), id the only change, `test-nodes` all pass. Main's
hit is a disabled, unconnected node, so main can wait for its next import. Commands in
[`docs/design/studio-e-id-fix.md`](docs/design/studio-e-id-fix.md). Also still open: IT to confirm the old id is
retired rather than hidden from one account.

---

### 68. Move Direct - the move at the yes, without the model

*Raised 30 Sep 2026 17:20, after the QASER series tests (main v198-v201).* Every move card is written by code now (Move
Booking v25, Guard Probe's series cards), and since v200 the yes moves exactly the card shown - but the yes still goes
through the model, which calls Move Booking itself. Three live failures today, all the model: it carded the wrong date
(v198), moved both dates on one yes (v198, v199), and at 17:18 called Move Booking twice in parallel for the same card
(v201) - two replacements for 9 Nov (the second one's room declined), the original deleted by the first call, and the
second reporting PARTIAL ("could not remove the original") for an original that was already gone.

**Build** (the Book Direct / Cancel Direct pattern, main only): Prepared Cancel (or a Prepared Move node beside it)
flags `_moveDirect` when Gate Context says the move is confirmed and Booked For's `approvedMove` is set -> a `Move
Direct?` IF -> `Move Direct` (Execute Workflow: Move Booking, once, with the card's title / date / new times / room,
confirmed) -> `Move Direct Reply` in code: 'Moved "TITLE" on DATE to TIME.' plus Booked For's `seriesNextCard` when
there is one; PARTIAL / REJECTED answered in plain words. The Turn Log path column gains "move direct". Sim: the
QASER run end to end, and a single booking's move. Then the 1 Oct end-to-end Slack run covers it.

## 🟠 Soon: details

**34. A1: Jessie sometimes leaves free rooms out when she lists them.** Found in the early-September QA
(about 30% of availability answers dropped a bookable room) and carried as the top build item through
18 Sep, then never marked fixed. `Room Availability` computes the free list deterministically, but the
model restates it and nothing checks the restatement: `Guard Probe` only refuses an offer that this turn's
check contradicts. **Next step:** a targeted re-test (ask "what's free tomorrow afternoon?" several times
and compare each answer with the tool's `free` list in the execution). If it still drops rooms, have Guard
Probe append the tool's list instead of trusting the prose.

**26. The agent can fabricate a preemption ("I've asked the current holder to move") without
calling Book Session.** Found 2026-09-22 in consent-engine live QA (main exec `10293`): a
Celebrity Recording request into an occupied Studio F made the agent call *Room Availability*,
see the room busy, and then reply "Studio F is held by INCUMBENT… I've asked the current holder
to move" — a claim of a side-effecting action (opening a consent request) that it never
performed. No Book Session, no Open Consent Request, no PENDING row, no incumbent DM. The
requester is told a consent request is pending when none exists. Guard Probe's claim-verifier
catches fabricated "Booked/Cancelled/Moved" but not fabricated preemption offers. Fix (our code,
not a wait): extend the claim-verifier so a "asked/requesting the holder to move / current holder"
reply is replaced unless an `Open Consent Request` tool call appears in this turn's
`intermediateSteps` with success. Same enforcement pattern as the existing claim check. Not
started.

**27. The agent sometimes double-calls Book Session, opening duplicate consent requests.**
Found 2026-09-22 (Book Session execs `10306`+`10307`, both `Return Offer` → Open execs
`10308`+`10309`): one confirmed Celebrity request produced two identical preemptions, DMing the
incumbent twice. No data corruption here only because both Opens generated the same timestamp
Request ID (same second) so the second write updated the first row rather than adding a second;
a sub-second-apart double-call would write two rows, and on resolution the second placement
would hit `ROOM_OCCUPIED`/`NOT_ELIGIBLE` (no double-book — the guard holds — but a spurious
"couldn't place" message). Fix options: make `Open Consent Request` idempotent (skip if a PENDING
row already exists for the same requester+room+window+incumbent), and/or make the incumbent DM
`executeOnce`. Not started; low risk given the double-book guard, but it spams the incumbent.
**Also observed 2026-09-22:** the stray second placement surfaced a contradictory "the booking did
not go through" **after** the requester had already been told "Done - Studio F is yours" — so this
isn't only incumbent spam, it can confuse the requester with a false failure. Bumps the priority.

**28. Booking over your OWN booking opens a self-consent instead of "you already have this."**
Raised by Howard 2026-09-22. The preempt branch (`decide.js`/`branch.js`) never checks whether the
incumbent's booker (`approver`, from the event `ref:`) is the same person as the requester. So when an
authorized user books a higher-priority session over their *own* existing booking, Jessie opens a
consent request and DMs *them* asking permission to move their own session — you consent to yourself.
It works (no double-book), but it's the wrong interaction: it should recognize the booking is yours and
either say "you already have <title> in <room> at <time> — want to move it?" or just fall through to the
normal `ROOM_OCCUPIED` refusal (which already names your own booking). Fix (small, our code): in Decide
Preempt, if `approver === requester` return `offer:false, reason:'SELF_BOOKING'` so it takes the normal
refusal path — never a self-consent. **Note this also means solo preemption testing is impossible once
the guard is in** (you can only ever book over your own bookings), which is fine: real preemption QA
needs a second person owning the incumbent booking. This is a genuine post-launch fix, not a test-only
artifact. Only reason it opens for Howard today is his HAIST Dev authority makes him an authorized
preempter; a Standard user booking over their own booking already just gets the plain "room's taken"
refusal (`NOT_AUTHORIZED` → no preempt). Not started.

**23. After a `ROOM_OCCUPIED` rejection, Jessie re-offers the identical doomed move.**
Found 2026-09-21 reviewing a live move (execs `9962`, `9971`): Move Booking returned
`REJECTED / ROOM_OCCUPIED` (Studio 1 taken by `NET-PUSO / JC` in the target window),
Jessie relayed it correctly — but on the next confirmation it re-presented the *same*
"Confirm to move" summary and hit the exact same wall, twice. The first rejection's own
guidance ("offer another time") was ignored because nothing carries the just-failed slot
across turns. Harmless (the original booking is never touched, `ROOM_OCCUPIED` holds every
time), but it wastes turns and reads as a loop.

This is our own behavior to fix, not a wait on another system — parked here so it isn't
lost. Same root as the CLAUDE.md "Not done" note that availability isn't remembered across
turns. Likely fix: after a `ROOM_OCCUPIED` (or availability) refusal, have Guard Probe /
the move summary refuse to re-present an unchanged room+window and instead force a
time/room change — deterministic, in the sub-workflow or Guard Probe, not the prompt. Not
started; low priority vs. launch items but a clear UX win. Related to the priority-preempt
consent work in `docs/design/booking-authority-phase2.md` (the "proper" answer to an
occupied higher-priority slot is to broker the incumbent's move, not just refuse).

**29. Music sessions that require an arranger don't capture one.** Found 2026-09-23 booking a Celebrity
Recording (Music) — the summary had `Engineer: Drey` and **no Arranger**, and Jessie never asked, even
though Airtable **Session Types → "Celebrity Recording" → `Engineer Role Required`** lists **Music Engineer,
Post Engineer, and Music Arranger**. The role data is injected via `Room Table` but this is a prompt-level
behavior (the "one principle"): the model dropped it. Fix (deterministic): for a session type whose
`Engineer Role Required` includes **Music Arranger**, Book Session should treat the arranger as a captured
role — surface an **Arranger** line in the summary and prompt for it (or refuse) when it's missing. Needs a
new arranger input + a guard, not just a prompt tweak. `Arranger` already exists as a role on the
`Advertising Projects` table. Not started; normal-booking pre-launch polish.

**30. Celebrity / "pair with a conference room" sessions don't recommend a holding room.** Found 2026-09-23:
a Celebrity Recording in Studio F was summarized with no suggestion of a holding room, though Airtable
**Session Types → "Celebrity Recording" → `Room Requirements`** = *"Large, pair with one or more conference
room as holding areas"* (and celeb-in-F/C is the classic case — Likha/Katha as holding). It's advisory (a
recommendation, not a hard requirement), so it fits **Guard Probe**: for a session type whose
`Room Requirements` says "pair with … conference room", append a *"consider adding Likha/Katha as a holding
room"* line to the summary deterministically, rather than relying on the prompt. Not started; pairs
naturally with #29 (both read the same `Session Types` data).

**35. The timestamp junk-guard isn't in Move Booking or Expand Series yet.** QA on 2026-09-24 caught the
model gluing visible junk onto timestamps (`…+08:00ភាsa`). `isoOnly()` now strips it in Room Availability
(v8) and Book Session (v44+), but Move Booking and Expand Series also take model-supplied times and would
still reject such a value. Not seen there yet. A small, contained change in two sub-workflows (CLAUDE.md
gotcha 16).

**55. Two cancels in one message show only one card.** Found in live QA 29 Sep (exec 16739): "qamove - november 17 /
qatime - nov 16". The model called Prepare Cancel twice and both came back PREPARED, but only QATIME's card reached
Slack, and the "yes" cancelled QATIME only. QAMOVE needed a second request. Nothing was cancelled wrongly: Cancel
Direct acts on the card that was shown. Either show every prepared card with one confirmation for all of them, or
prepare only the first and say the next will follow.

**56. A cancel with no date guesses the date from the conversation.** Live QA 29 Sep: "cancel QANEW" (exec 16715)
was looked up on 21 Nov, the date of a booking just cancelled, when the one left was on 18 Nov. "cancel qamove from
november and qatime as well" (exec 16735) was looked up on 18 Nov only. Both times Jessie said she found nothing and
asked for the date, so it cost a turn, not a wrong cancel. A title with no date could be searched across the
requester's upcoming bookings instead.

**57. A late Slack retry after a re-send is handled twice.** 29 Sep 15:41 PHT: a message's first delivery never reached
n8n, the requester re-sent it 32 s later, and Slack's retry of the original then arrived (61 s late). Both ran, so two
identical summaries went out. Harmless here (a summary, not a booking: every booking still needs its own yes), but
confusing. Each copy has its own Slack message id, so dedupe on the id does not catch it; skipping a message whose text
is identical to one the same person sent within about 2 minutes would. See `docs/outages/OUTAGES.md` (29 Sep, 15:41).

**58. Lowercase initials, and a bare answer to "Who is the arranger?".** Live QA 29 Sep 15:45 PHT (execs 16886-16897):
asked for the arranger, the requester answered "bpv", then "bp" (BP Valenzuela). "bpv" is not on record (her Initials
are "BP " with a trailing space, and BPV is not in Info), so that refusal was right. But the first "bp" got '"bp" is
not on the Hit Productions staff list' with no tool call at all - the model copied the previous refusal - and only the
second "bp" went through. Booked For only read initials typed in capitals and only after a role word. **Built:** main
v188 reads initials in any case, reads a bare answer to Jessie's "Who is the arranger / engineer?", and Guard Probe
replaces a staff-list refusal nothing backed. **Airtable (Tel, asked 29 Sep):** BP Valenzuela's Initials to BPV (what she
uses); keep "BP" in her Info "Goes by" so "bp" still resolves.

**59. Series summaries and events (live Slack test 29 Sep 18:16 PHT, execs 17135-17138).** "Book Studio 8 every Tuesday
from November 2 to November 16 ..." booked all three correctly, but the summary (model-written; only the dates list is
rebuilt in code) had " Time: 10:00 AM – 12:00 PM" - a leading space, no bold label - on every detail line and no Booking
Type line, and the three events' descriptions have no "Type: External" where single bookings do: Book Series does not
pass the booking type on to its per-date Book Session call (CLAUDE.md gotcha 21). Cosmetic in the summary; the missing
Type matters only to anything reading the event description.

**60. Two cancels in one message: the model sometimes prepares only the first** (live 29 Sep 18:22 PHT, exec 17201).
"cancel QAS3 on November 24 and LIKHA - BD on November 25" -> Find Booking and Prepare Cancel for QAS3 only; the card had no
"Next:" line, so the Likha booking had to be asked for again. The queue (main v187) shows only cards the model prepared;
"cancel QASERIES on November 2, November 9 and November 16" (three dates, one title) prepared all three and chained.
Nothing is cancelled wrongly - one booking is simply left for a second request.

**37. Consent paths that have never run live.** (a) A **priority (PREEMPT) request timing out**: the Sweep
marks it `EXPIRED` and nothing moves. Unit-tested and wired, never exercised end to end. It can run now with
the manual-deadline trick (edit a PENDING row's `Deadline` to the past, wait for the ~10-minute Sweep).
(b) **Same-day and next-day M-booth windows** (3h / 10:00 on the booking day, live since
open-consent-request v10) can only occur at launch, because QA's year-shifted dates are always 2+ days out.
`./scripts/test-consent` covers them with a fixed clock; watch the first real same-day request after launch.

**38. 2027 test events to clear off the calendar** (the Calendar connector is read-only, so this is
manual). From consent and M-booth testing: M1 on 25, 26 and 28 Sep 2027 and M4 on 27 Sep 2027;
`BROWSE / Jem Lim / Drey x Brian Cua` (Studio F, 30 Sep 2027, 10am–1pm, booked before the initials guard was
fixed); the M3 holds from the 18 Sep recurring tests; and `GUARDCHK` (item 16). All year-shifted, so they
collide with nothing real, but they clutter lookups and QA. Check and clear before launch.

**16. A seeded QA event is still on the calendar.** `GUARDCHK / Bea Jose / HL`,
Studio 6, Friday 2027-09-10 10:00–11:00, carrying a fake booker ref (`UFAKE99999`).
Created to prove `NOT_YOURS` — the refusal to cancel someone else's booking — and
left in place. On a 2027 date so it cannot collide with anything real. Delete it
through Jessie or Google Calendar once it is no longer needed for that test.

**44. Jessie says "Booked" even when the room turns the booking down seconds later.** Found 2026-09-25
while reviewing the Envoy flow. Book Session's `Verify` node looks for a room that `declined` in the Create
Event *response*, but room resources answer the invitation a few seconds after the event is created (the
node's own comment says `responseStatus` is always `needsAction` there), so the check effectively never
fires. When the room is already held by something Jessie can't see on KDC Bookings (a tablet booking inside
the mirror's poll gap, a standing hold, anything booked directly on the room), she replies "Booked", the room
declines moments later, and the event sits on KDC Bookings with the room crossed out. This happened on
2026-09-23 with the M1 test (Rico's hold). **Fix:** after creating the event, wait a few seconds and re-read
its attendees; if the room declined, delete the new event and tell the requester the room is taken. It
matters more once tablets are a booking source (item 42).

**45. Retest the trimmed prompt (main v157) before the SOP starts on 29 Sep. RESOLVED 2026-09-28** — retested by
the eval twin, 27–28 Sep (900+ real-Gemini conversations; see [`docs/eval/eval-report-2026-09-27.md`](docs/eval/eval-report-2026-09-27.md)); the
prompt-trim checklist is scenarios TC-1..10, all passing on v165. The "Dhang" example leak it found is removed. *v157 is LIVE — pushed
2026-09-26 ~07:05 UTC; first real turn (exec 12158) replied normally. The retest is still owed.*
**`reapply-main-fixes --check` now reports "v152 on-behalf prompt guidance MISSING" — a false alarm.** The
guidance is present (`booked_for`, "Booked by: <you> (for <them>)", not the client, never in the title), just
reworded; the check looks for the exact old phrase " Booking on behalf of a colleague:". Don't re-apply it —
update the check to the new wording instead. *(Done 2026-09-26: the check accepts either wording; `--check` is clean again.)* Raised 2026-09-26. The
system prompt is cut from 47,084 to 29,223 characters (38%) — duplication, incident anecdotes, and long
explanations of rules the sub-workflows already enforce. The QA round-2 failures traced to the model, not
the workflows, and a smaller prompt gives a small model less to drop. Tara is pushing v157; **Howard
retests** using the conversation list in [`docs/prompt-trim-proposal.md`](docs/prompt-trim-proposal.md), and
checks the seven decisions listed there, which go live with it (e.g. only the newer `booked_for` "Booked
by" rule survives; a stale Studio 7/8 fact and a self-contradicting duration clause are removed). Push,
check and rollback commands are at the top of that file. `test-nodes` passing proves nothing about the
prompt — only a conversation pass does.

**46. Speed: cache the reference tables (main v158) — FAILED LIVE, ROLLED BACK. Do not push v158.**
*2026-09-26: pushed 07:4x UTC; the first message (exec 12218) failed in **Ref Store**, which ran 60,026 ms and
died with "Unknown error" — the task-runner timeout, same signature as gotcha 11. Rolled back to v157 at
07:49:54 UTC. Only Tara's test message was hit (no reply; its 👀 was never cleared). Ref Cache, which only
*reads* static data, took 50 ms; the hang is in *writing* the cache. Leading suspect: assigning a large
nested object to `$getWorkflowStaticData` from the task runner — Gate Context only ever writes small
strings. The offline simulation passed 17/17 and could not catch this: it is runtime behaviour. Next step:
prove a fix (e.g. store the cache as one JSON string) on a throwaway webhook workflow before Jessie.*

*Isolation tests, same day, on a throwaway webhook workflow `ZZ scratch - static data test` (`Sb59OfsUnVmBsjNl`,
now deactivated). All ran in under 0.5 s unless noted, none hung: writing a 40 KB nested object to static
data; writing it as a JSON string; storing records read from another node via `$('Emit').all()` raw, as a
string, and deep-copied; looking the node up through a variable (`$(name)`, as Ref Store did); the same with
an idle AI agent + tool node present; and finally **v158's exact Fetch Rooms / Fetch Session Types / Fetch
Bookers + exact Ref Store code** against live Airtable — 7 s, `cached: true`. So the hang happens only inside
Jessie's workflow and has not been reproduced. The one code difference from all working Jessie nodes: Ref
Store is the only node, in v157 or v158, that looks a node up through a variable instead of a literal name.
The n8n container log for 07:45:01–07:46:10 UTC (task runner) should name the real cause.*
Raised 2026-09-26. Every
message read Rooms & Studios, Session Types and Bookers from Airtable (~1.1s each, one after another), then
searched Bookers again for the sender (Get Booker, 1.2s typical, 4.8s worst). Median over 25 real turns: ~6s
of reads before Gemini starts; one turn today spent 9.4s on All Rooms alone. v158:

- **Ref Cache** checks for a copy of the three tables under 10 minutes old; **Cache Fresh?** skips the
  Airtable reads when there is one. On a miss the reads run as before (renamed **Fetch Rooms / Fetch Session
  Types / Fetch Bookers**) and **Ref Store** saves them — only a complete read, so a failed read never
  replaces a good cache.
- Code nodes now carry the old names **All Rooms, All Session Types, All Bookers** and emit the same
  `{id, createdTime, fields}` items, so Room Table, Booked For, `test-nodes` mocks and `reapply-main-fixes`
  are unchanged.
- **Get Booker** is now a Code node reading the sender from All Bookers instead of a second search — same
  name, same output (one empty item when the sender isn't in Bookers), so its ~20 references are untouched.
- Staff **Email is left out of the cache** (nothing reads it). `scripts/n8n pull` and `scripts/backup-live`
  strip `staticData.global.refCache` so the cache never lands in git.

Expected: ~4.5s off a typical turn (~15s → ~10s), and far fewer spikes. **Trade-off:** an Airtable edit (new
room, renamed session type, new staff member) reaches Jessie up to 10 minutes late. **Known small risk:**
n8n saves static data whole at the end of an execution, so a cache refresh that overlaps another user's
turn can drop that turn's `epoch_*` memory write (or vice versa) — the same last-writer-wins race Gate
Context's epochs already have, now slightly more frequent (once per 10 minutes).

Verified offline against the real data from exec 12158: cold start, warm cache, expiry, a failed Airtable
read, an unknown sender, and Booked For producing byte-identical output on the cached path — 17/17. Built
from a fresh pull of live v157; 209 checks + 28 scenarios pass. **To ship:** `./scripts/n8n-write put
uVVYVB2M7kxpLleI workflows/project-jessie-v158.json`, then `./scripts/health` after two messages (the first
refreshes the cache, the second should show no Fetch nodes). Rollback: push v157.


**47. Date guard LIVE (main v159 + Book Session v47), 2026-09-26 08:30 UTC.** Fixes QA round 2's wrong-date
booking (Camille: "next Thursday" resolved to 30 Sep and carried every turn; the model checked and booked 7 Oct).
Book Session now refuses **DATE_MISMATCH** when a booking's date (in Manila) is not one of Gate Context's
`datesUnderDiscussion` — every date the requester named in this message, else the one carried from earlier in
this conversation today. The model never supplies it (`expected_date` is wired from Gate Context, like
`confirmed`). Empty = no guard; series occurrences exempt; PAST_DATE still fires first.
To make that safe, Gate Context now also: resolves month-day dates with no year ("oct 5", "5 October",
"October 7th") using the prompt's year rule — they were not resolved at all before, so a requester changing the
date that way left the old one carried; lets a written date win over a bare weekday ("Friday Oct 1" = 1 Oct);
and **drops the carried date** when a message names one it cannot read ("the 30th", "next week").
**Known cost:** if Jessie offers another day and the requester only says "ok book that", the booking is refused
once and she asks them to confirm the date — an extra turn, never a wrong booking. Tara chose enforcing over a
watch-only trial. Verified: `scripts/sim-date-guard.js` 20/20 (Camille's replay, date changes, unreadable dates,
UTC timestamps, all-day, series, past date), `test-gate` 28/28, `test-nodes` 209/209. **Watch for
DATE_MISMATCH refusals in QA** — each one is either a caught error or a false refusal worth reporting.

**48. "Next week" is worked out by the model, and it got it wrong. RESOLVED — main v160 LIVE 2026-09-26 11:13 UTC.** Found 2026-09-26 (exec 12258). Asked
"show my bookings next week" on Sunday 26 Sep 2027 (Jessie's calendar), she answered for **Oct 4–11** — next week
is **Sep 27 – Oct 3** (weeks start Monday, Tara's rule). Same class as the QA round-2 date bug: Gate Context
resolves weekdays, today/tomorrow and written dates, but not week or month phrases, so the model computes them.
**Fix:** have Gate Context resolve "this week", "next week" (and "this/next weekend", "next month") into an
explicit Monday–Sunday range in `dateNotice`, like it does for "next Thursday". Note the v159 date guard currently
*drops* the carried date on those phrases (they're unreadable to it); once resolved, the range could feed the guard
too. Also from the same session: the reply range was 8 days (Oct 4–11), not 7.
*Fixed in v160: Gate Context resolves "this/next week", "(this/next) weekend" and "this/next month" into an exact
range in `dateNotice` (weeks start Monday); every day in it counts for the date guard; a range is never carried to
the next turn. Re-asked live (exec 12283): "No bookings found for you in that period (September 27 – October 3,
2027)" — correct. `sim-date-guard.js` 26/26, test-gate 28/28, test-nodes 209/209.*

**49. Localization title initials made up from the engineer's name — FIXED, Book Session v48 LIVE 2026-09-26 11:19 UTC.**
Howard, 26 Sep 15:21–15:26 PHT (execs 12198–12213, on v157): staff lookup returned Jek Panganiban, **Initials FP**; the
first summary was right (`NET-KUBA / FP`), but when he changed the length the model rebuilt it as `NET-KUBA / JP` —
initials invented from the name — and that was booked (2027 test event `tgifi2oci5nn0mp3dokqpi1p3s`). v45 already
rewrites the title's initials from the engineer's Bookers record, but only for three-segment titles; Localization's
two-segment `Project Code / Initials` was skipped. v48 applies the same correction when the session type is
Localization or QC. `scripts/sim-title-initials.js` 6/6 (v47 reproduces the bug); test-nodes 209/209.
The project code in the Localization client slot (`Client: NET-KUBA`) is intended — the department works by project code (Tara, 2026-09-26). Not a bug.
**50. Clients are optional; new clients go to a review sheet; client room preferences are dropped.** Decided
2026-09-28 (decided in discussion). **LIVE: main v161 + Book Session v49, imported 2026-09-28 10:58 PHT** (test-nodes --live 221/221 + 28, verify-ids clean). `New Clients` tab created by Howard, headers checked.
- *Prompt (v161):* still always ask for a client, but a booking goes ahead without one — title `PROJECT /
  initials`, summary `Client: None`. A client not in Clients is a new client for every department (Advertising
  and Localization included): booked as typed, one line saying it will be flagged for review, never blocked. The
  "lead with the client's preferred room" rule and its "Studio 8, Dhang's usual room" example are gone (the eval
  caught the model copying the example into real replies, and the field reached it as record ids).
- *Book Session (v49):* `MISSING_CLIENT` no longer refuses a missing client (it still refuses the booked-for
  colleague as the client); `TITLE_INITIALS` and the staff resolver's initials rewrite cover the two-segment
  `PROJECT / initials` title. After a CREATED booking, `New Client?` → `New Client Row` → `Log New Client` writes
  the client to the **`New Clients`** tab of the Jessie Log spreadsheet (`appendOrUpdate` on `Client`, one row per
  client, Status `For Review`) — Tel reviews it and adds the client to Airtable, since only Tel can write Airtable.
  The write never fails a booking.
- *Airtable, done 2026-09-28:* Tel deleted every hidden Clients field (the three preferred-room fields, Typical Session
  Length, Technical Requirements, Min Simultaneous Rooms, Tends to Overrun, the Advertising / Localization Projects links,
  Rooms & Studios). Clients is now Name, Importance, Notes, Booker Type, Client Type; from 03:35 UTC live Clients lookups
  return only those (28 lookups, no errors). The deleted links' partner fields in Rooms & Studios, Localization Projects and
  Advertising Projects became plain text columns; Jessie reads none of them.
- *Needs (done):* **Howard** — add a tab named exactly `New Clients` to the Jessie Log spreadsheet with this header row:
  `Client | Status | Booked by | Project | Session Type | Department | Booking Date | Room(s) | Calendar Title |
  Event ID | Added`. Until it exists the write fails silently and the booking still goes through. **Tel** — delete
  `Preferred Rooms`, `Preferred Room Name` and `Preferred Room Names` from Clients (their inverse fields in Rooms &
  Studios, `Booking Profiles` and `Booking Profiles copy`, go with them; nothing in Jessie reads either). Nothing in
  the workflows reads the three fields and the Clients tool returns whatever exists, so the deletion cannot break a
  lookup. Re-check the Clients schema afterwards.
- Tests: `test-nodes` 221/221 + 28 gate scenarios (the old files fail exactly the four new checks); eval with
  `./scripts/eval-run --main workflows/project-jessie-v161.json --only NC,CLI,FOR,ASK,ENG-1,ENG-2,ENG-8,QA-M3`.

**51. A padded timestamp makes the calendar query fail, and the failure reads as "every room free".** Found by
the hallucination eval, 2026-09-27 (`docs/eval/eval-report-2026-09-27.md`, finding 1; gotcha 18). The model glues
junk onto a timestamp (`…+08:00hq`, `…p`, `…Cllr`, U+FE0F, Khmer letters). *Room Availability* sends it raw to
Google, gets a 400, carries on (`continueRegularOutput`), and `Compute Availability` reads no events as all free —
`isoOnly()` runs after the query. 79 of 199 checks in the eval, 4 of 27 live since 24 Sep; Jessie offered a booked
Studio F 7 times in 10. *Book Session*'s `Get Events In Window` has the same shape: a padded start is NaN, so it
queries now → now+24 h and `Check Conflicts` compares against the wrong day; `Create Event` then gets the raw
value (fails, or books over a session — unverified). 0 of 14 live write calls were padded. *Move Booking*'s `Get
New Window` follows the pattern (see also 35). **Fix:** clean every model-supplied timestamp before the query, and
fail closed on a calendar error ("couldn't check" / refuse). Small, no speed cost; **Done 2026-09-28:** fixed in Room Availability v9, Book Session v50, Move v20, Cancel v16, Find v4, Expand
Series v2, Book Series v3 and main's List Events (`./scripts/test-dates`); live eval after the 03:33 UTC import: 64 of 140
availability checks had padded times and all 64 returned the real busy rooms — none said every room was free.

**53. Clients table data quality.** Found 2026-09-28 while picking eval cases (read-only listing of all 106 rows).
*Duplicates* (two records each): Ino Magno, Allan Sy, Aldrin Galang, Migs Dela Peña, Marlyn Montano, Brian Cua, Cha Agcaoili
(one of them stored as " Cha Agcaoili"). *Stray spaces*: " Cha Agcaoili", " Denise Galoyo", "Arnold Buena ". *Rows that are not
clients*: "Business Development", "Event Lobby", "Direct Clients (Post)". Harmless to bookings — an exact match still resolves
and a duplicate just makes Jessie pick the first — but a duplicate with different Client Types could flip External/Personal,
and the non-client rows can match a "for Business Development" request. Fix in Airtable (Tel): merge the duplicates, trim the
names, and move or delete the non-client rows.

**52. M2 and M6 are not marked bookable.** Found 2026-09-28 from the eval (QA A2: "List all rooms" twice named
M2 and M6, which the scorer took as invented). Both rows exist in Rooms & Studios (Room Type `M Booth`), but their
`Active / Bookable` checkbox is unticked, and `All Rooms` in main reads only `{Active / Bookable}` rooms — so Room
Table never lists them and Room Availability never reports them. (An earlier note here said they were missing from
the table; they are not — Howard, 2026-09-28.) If they should be bookable, tick the box; if they are deliberately
held (the calendar has standing "M2 - Peemo" / "M6 - Marketing" events), nothing to do. **Resolved 2026-09-28:** Tel ticked
both; from 03:35:31 UTC `All Rooms` returns 27 rooms and Room Table lists M2 and M6.

---

### 69. Short booking summary

*Asked 30 Sep 2026 for a presentation at the end of the week; scheduled Fri 2 Oct morning, after the functional fixes
(68, 44) and the 1 Oct Slack run, and before the human QA round so it is tested in its final form.* Wanted:

```
DIGICON / Vic Icasas / TL
Date: Thursday, September 30, 2027
Time: 5:00 PM – 7:00 PM
Room: Studio 8
```

Keep every check and every detail gathered (client, session type, engineer, arranger, department, booking type, booked
by) - only the message is shorter. **Why it is not just deleting lines:** at the yes, Prepared Booking reads Jessie's
newest message back, verifies the `_check_` code and Book Session books *those* lines; hidden lines would be lost.
**Build:** Render Summary also writes the full field set to the existing reference-cache data table under
`cache_key = prep-<check code>` (no new table to create); the message shows the title, Date, Time and Room, the check
code (it can be made smaller) and the confirmation line; Prepared Booking looks the fields up by the code at the yes
and books all of them. Notes that need an answer stay (the room picked, the proposed time, the length heads-up, the
self-engineer note). A lookup that fails refuses and re-prepares - it never books with missing fields. Old rows are
pruned by the daily 04:00 job.
**Decided 30 Sep: hide them always.** The engineer is already in the title's initials; the session type and booking
type are for the system (and the calendar event keeps all of them), not for the booker. Also: the whole exchange
should read like a short conversation, not terms and conditions - every question and note in as few words as it
takes (Tara: "LESS WORDS better"). Needed working in Slack by the end of the week for the DIGICON video demo.


**Built 1 Oct (Book Session v73 + main v203).** Prepared rows (`prep-<fingerprint>`) accumulate in the reference-cache
table - add them to the daily 04:00 prune (older than a day) after the demo. Import order: main v203 first (it still
books summaries with a printed code), then Book Session v73 - the other way round, a yes to a short card would find
nothing stored to read.

### 70. Booking type: Advertising, Entertainment, Internal, Personal

*Decided 30 Sep 2026 (Howard with Tara), for the end-of-week demo.* External / Personal becomes four categories. The
question "Is this booking External (Hit Productions work) or Personal (their own project)?" read as clunky and
over-explained; the type should be worked out wherever it can be, and asked in a few words only when it cannot.

- **Personal:** the client is a Hit employee (in Bookers - e.g. the arrangers listed as clients), or the requester says
  it is their own project.
- **Advertising / Entertainment:** from the client's record; a new client who is not staff is never Personal or
  Internal, so the only question left is **"Is this an advertising or entertainment project?"**
- **Internal:** Hit's own work with no outside client (decided 30 Sep).
- **The rule, in order (decided 30 Sep):** (1) what the requester said ("personal", "my own" / "Hit project",
  "internal" / "TVC", "ad", "commercial" / "dubbing", "series"); (2) the client's record wins - department alone is not
  enough, a Hit convention VO recording can be Internal; several types on the record -> one short question with those;
  (3) removed 1 Oct (a client who is staff is not always Personal); (4) no client -> "Is this a Hit project or your own?"; (5) a new client
  who is not staff -> the department's default (Audio Post, Music -> Advertising; Localization -> Entertainment), else
  "Advertising or entertainment?". Open: whether (5) should ask instead of defaulting, since the short summary no longer
  shows the booking type.
- **Tel, by Thu 1 Oct:** Clients `Client Type` -> Advertising / Entertainment / Internal / Personal, every client
  recoded (in-house arrangers Personal, Hit's own projects Internal). A client still on External after that asks (5).
- **Touches:** Book Session (Check Conflicts' booking-type step, NEED_BOOKING_TYPE wording, Render Summary, the
  calendar `Type:` segment, New Clients sheet), main (Booked For's words, the prompt's booking-type lines, Guard
  Probe's summary line), Book Series (passes the type), the Log sheet.

## 🟢 Additive: details

**36. A booth holder can't book their own held booth directly.** When the requester *is* the standing
hold's owner, Book Session's M-booth logic returns `book_as_holder`, but nothing handles it, so it falls
through to the normal `ROOM_OCCUPIED` refusal. Additive: the holder already has the booth, and can cancel
their hold instance or pick another booth.

**1. `Room Type` marks nine rooms as `5.1 Mixing`. Two of them record in stereo only.**

Read out of Rooms & Studios directly:

```
                 Room Type has 5.1   Recording Format      Equipment says
Studio 3,4,5,6   yes                 5.1, Stereo
Studio C         yes                 Stereo, 5.1, Atmos
Studio 7         yes                 Stereo                "stereo only"
Studio 8         yes                 Stereo with Sub       "stereo only"
Studio 1         yes                 Stereo                "5.1 capable"
```

Jessie answers format questions from `Recording Format` now, so she says Studios
3, 4, 5, 6 and C. `Room Type` is still misleading for anyone reading the table.
Either correct it for 7 and 8, or rename it so it reads as a category rather
than a capability.

Confirmed working live on 2026-08-30: asked "which rooms are 5.1?" the tool
queried `recording_format` and returned exactly those five. Asked to book Studio
7 for a 5.1 mix, she refused — "Studio 7 can only record in stereo". So the
workaround holds; the underlying data is still wrong for a human reader.

**Update 2026-09-21 (verified live):** Resolved. Studios 7 and 8 no longer carry `5.1 Mixing` in
`Room Type`; no `5.1 Mixing` room has a stereo-only `Recording Format` anymore.

**2. Studio 1 contradicts itself.** `Equipment` says "5.1 capable",
`Recording Format` says `Stereo`. Jessie reports it as stereo. If that is wrong,
it is an Airtable edit — nothing in the workflow needs to change.

**Update 2026-09-21 (verified live):** Resolved. Studio 1 is Stereo throughout — `Recording Format`
Stereo, no `5.1 Mixing` in Room Type, Equipment no longer claims 5.1.

**3. Studio E — booth or not?** `Room Type` includes `Recording Booth`, but the
`Vocal Booth` flag is not set. The flag covers Studio A, B and D only, and that
is what Jessie answers from, so E is excluded.

**Update 2026-09-21 (verified live):** Studio E still has `Recording Booth` in Room Type but no
`Vocal Booth` flag (flag = A/B/D only). It's a video-post room, so exclusion is likely right —
decide if the `Recording Booth` tag belongs. Low priority; no behavior impact.

**4. `Studio 2 ` has a trailing space in `Room Name`.** Any exact-match query for
"Studio 2" fails. It is only reachable by partial match.

**Update 2026-09-21 (verified live):** `Room Name` now reads `Studio 2` with no trailing space —
appears resolved (verify by eye, the character is invisible).

**7. Four session types list the same rooms as both Priority and Last Resort.**

```
Event         both lists: Lobby, Katha, Likha, Salin   (identical)
VO Recording  both lists: Studio 7, 8, F, C            (identical)
Meeting       both lists: Salin, Katha
QC            both lists: Studio 5
```

Where the two lists are identical, "last resort" means nothing, and Jessie could
truthfully describe a room as both the usual choice and the fallback — she called
Studio 7 "a last-resort choice for VO Recording" when VO can be recorded
anywhere. The wording no longer reaches requesters, but the ranking still drives
which room she offers first and which the guards allow.

Decide per session type whether the second list should be empty, or a genuinely
different set of rooms.

**Update 2026-09-21 (verified live):** Resolved. Tel's ranking changes gave every type a distinct
Priority vs Last Resort (VO, Music Vocal Recording, Music Mixing, Celebrity Recording now have
Studios 7/8 or 4/5/6 as genuine fallbacks; Event/Meeting/QC no longer duplicate).

**10. Bookings Jessie did not create can never be cancelled through her.** — **MOSTLY RESOLVED 2026-09-23:** every untagged event from 23 Sep to 31 Dec 2026 (39 edits) was backfilled with `ref:` / `Booked by:` / `Dept:` (see `docs/BACKFILL-CHECKLIST.md`). Still open for events added directly in Google Calendar *after* the backfill, and for 2027 onward: rerun the backfill per window. Original note:

`Cancel Booking` reads a `ref:` marker out of the event description to decide
whose booking it is. Events created before this build, or added directly in
Google Calendar since, carry no marker, so the guard refuses them with
`NO_REFERENCE` and tells the requester it has to be done by hand.

Confirmed live on 2026-08-30 against a pre-existing booking, and the refusal was
correct — with no marker there is no way to tell whose booking it is, and
guessing is worse than refusing.

The decision needed before launch: is "booked by hand, cancel it by hand" an
acceptable answer for the existing calendar? If not, the descriptions of
existing events need a `ref:` added, which is a bulk edit against the calendar
and needs someone to map each booking to a Slack user id first.

**11. Worth exploring an update — we don't know what the current version can do.**

Two things we wanted turned out not to be reachable from the installed version:

- the OpenAI Chat Model node always sends `frequency_penalty`, which Gemini's
  OpenAI-compatible endpoint rejects outright, so that node can't talk to Gemini
  at all here
- neither that node nor the Gemini node exposes a thinking or reasoning setting,
  and prompt caching isn't exposed either

Gemini itself accepts those parameters — tested directly against the API — so
the limits are on the n8n side. Whether a newer version lifts any of them is an
open question, not a promise: worth checking the changelogs for those two nodes
against what's installed before deciding whether an update is worth the restart.

**13. The first Code node in every execution costs about 3.5 seconds.**

n8n runs Code nodes in a separate task-runner process. The first one in an
execution waits for that process to be ready; later ones in the same execution
take about 0.07s. Measured across 14 consecutive turns on the live build:

```
message                       Gate Context   Room Table   Guard Probe
yes                                  3.50s        0.09s         0.05s
no                                   3.42s        0.07s         0.05s
book studio 8 next thursday          3.45s        0.07s         0.05s
cancel both of my studio 8...        3.71s        0.08s         0.06s
actually yes cancel it               0.08s        0.07s         0.04s
y                                    0.09s        0.07s         0.04s
```

Bimodal: either ~3.5s or ~0.07s, depending on whether the runner is still warm
from a recent execution. Ten of those fourteen turns paid it.

`Gate Context` is the first Code node and always will be — something has to be
first, so this cannot be fixed by reordering. It is paid on every message,
including ones that do nothing: a bare "hi" costs it.

**It is about 28% of a 12.5-second turn — the largest single piece of latency
left, and larger than everything else outside the model put together.**

**The runner shuts down after 12-13 seconds idle.** Measured across 29
executions: the longest gap that still found a warm runner was 12s, the shortest
that went cold was 13s. That is a sharp enough boundary to look like a
configured idle-shutdown timeout rather than chance.

That rules out the obvious workaround. Keeping it warm with a scheduled workflow
would mean firing a Code node every ten seconds forever - roughly 8,600
executions a day, filling the execution log and the database to save 3.5s a
turn. Not worth it.

*What to ask the server for, in order:*

1. **Raise or disable the runner's idle-shutdown timeout.** n8n's task-runner
   configuration has a setting of this shape, and the measured 12-13s window is
   consistent with a small default. Raising it keeps the process alive between
   messages. One environment variable, reversible, no workflow change. Check the
   installed version's task-runner settings for the exact name.
2. **Or run Code in the main process**, as n8n did before external task runners.
   Also an environment variable. It gives up the runner's process isolation,
   which matters less on an internal instance where we write all the code.
3. If neither is available on the installed version, that is a concrete argument
   for item 11.

Whichever is tried, it is measurable afterwards: re-run the same comparison of
`Gate Context` against `Room Table` in the execution data. First Code node ~3.5s
means it is still happening; ~0.07s means it is fixed.

*Measured 2026-08-30. An earlier note in this file withdrew this finding as a
mismeasurement — that withdrawal was itself the mistake, taken from a sample that
happened to catch warm runs.*

**18. The first outbound call of every turn pays a ~4s cold-connection tax — same root
as the outages.** Measured 2026-09-06 across many turns: `Get Booker` (the first
Airtable call) takes ~4.2s consistently, while `All Rooms` and `All Session Types`
— the *same* base and credentials, a few seconds later in the same turn — take
~1.1s. The Bookers table is ~14 rows, so it is not scan cost or the query; it is
DNS resolution + TLS handshake on the first call, which later calls reuse warm.
Spikes to 8–16s coincide with the host's known DNS flapping (`EAI_AGAIN`), the same
symptom behind the outages in item 15. So caching `Get Booker` would not help — the
tax just moves to whatever call is first. The fix is on the host: a DNS cache or
keep-alive so the first call per execution stops paying resolution cost. This and
item 13 (the Code-node cold start) are the two fixed per-turn costs, ~7.5s of a
16.5s median turn, and both are server-side, not workflow changes. Cross-links
[[15]] (the outages) and 13 (the task runner).

**39. The two staff-list reads added on 2026-09-25 cost about 1s each.** `All Bookers` runs in main (every
message; 58 rows, 1.1s measured live) and in Book Session (every booking). Correctness first. If turn time
matters later, read Bookers once per turn and pass it down (for example via `Room Table`'s `referenceData`),
or cache it. Related to 13 and 18.

**40. Leftover snapshot files from renames in `workflows/live/`.** `backup-live` never deletes (CLAUDE.md
gotcha 15), so a renamed workflow leaves its old snapshot behind: `finalize-consent__…`,
`open-consent-request__…` and `tmp-timesheet-credential-probe__…` (untracked), plus
`posty-airtable-typo-check__…` and `posty-monthly-digest__…` (tracked). Each shares its workflow id with a
current snapshot. Safe to delete; needs Howard's OK.

**41. `Booked For`'s notice quotes three words, not just the name.** It tells the model the requester
wrote "for Japs next Thursday", because the capture takes up to three words. Harmless (the name itself
resolves correctly), but `matched` should be trimmed to the words that actually matched.

---

### 67. Day-by-day availability: a clearer layout

*Parked 30 Sep 2026, after the PENDING 62 fix went live (Room Availability v12).* "What studios are free this week?"
now answers day by day, but each day is one long comma list - M booths, studios and vocal booths mixed together
(16:16 PHT: "Thursday, September 30: M2, M3, M5, M7, Studio 1, Studio 2, ... Studio M"). Wanted:

```
Thursday, September 30
Studios: Studio 1, Studio 2, ... Studio M
M booths: M2, M3, M5, M7
Vocal booths: Studio A, Studio B, Studio D

Friday, October 1
...
```

- A blank line after each day.
- Within a day, one line each for studios, M booths and vocal booths (vocal booths are the Airtable `Vocal Booth`
  flag; M booths are M1-M8; conference rooms only when the requester asked about rooms, not studios).
- Written by code, not the model: Room Availability builds the lines (`days[].groups`), and Guard Probe sends them as
  they are, as it does for other code-written replies - the model merges and reorders lists otherwise.
- **Decided 30 Sep:** a question with no time checks the whole day, even right after one that had a time ("what studios
  are free this week?" after "... from 2pm to 4pm" reused 2-4 PM). In code: the window comes from what this message says,
  not the previous one.

## ✅ Resolved

Kept for history: each says how it was found and how it was closed.

**5. ~~`Clients.Preferred Rooms` needs a companion field.~~ RESOLVED (marked 2026-09-25):** the Clients tool now returns `Preferred Room Names`, so Jessie can read preferred rooms (see CLAUDE.md *Not done*: proposing them is still best-effort, not deterministic). Original note:

The field is a link to Rooms & Studios, so the API returns record ids —
`reced8Jk7wG24KpdE` — not names. Jessie cannot read those. When she tried, she
reported one client's preferred rooms as three studios that were not the right
ones. She is no longer sent the field at all, which is why she asks which room
instead of proposing one.

*What to add:* a new **Lookup** field on the Clients table, `Preferred Room Names`:

    Field type:        Lookup
    Linked record:     Preferred Rooms
    Field to look up:  Room Name

Read-only and computed, so it cannot drift from the link.

*What not to do:* do not delete or convert `Preferred Rooms`. The link is where
the data lives and the lookup reads through it — remove the link and both fields
go.

*What it unlocks:* Jessie can propose a room again instead of always asking.
Until then, always-ask is correct and is what she does.

**Update 2026-09-21:** the `Preferred Room Names` lookup now exists and the Clients tool returns it
(verified: Dhang Santiago → Studio F, Studio 8); the prompt directs Jessie to lead with it. The data
unlock is done, but she does not yet *reliably* propose the preferred room (prompt-level behavior) —
reliable proposal would need deterministic enforcement. Tracked as a soft follow-up.

**6. ~~A client's Technical Requirements points at a field Jessie cannot read.~~ RESOLVED (marked 2026-09-25):** the reference now resolves: item 5's `Preferred Room Names` lookup landed, which is one of the two fixes proposed below. Original note:

Jem Lim's `Technical Requirements` reads:

    Long sessions. Prefers no separate vocal booth — room preference already
    noted in Preferred Room.

`Preferred Rooms` is withheld from Jessie because it returns record ids (item 5),
so that last clause dangles. Asked why she had picked a room, she completed it:
*"Jem Lim's client notes specifically mention a preference for rooms noted in
their profile"* — which reads as though the room was chosen to suit the client.
She cannot know that. The prompt tells her never to claim a room is a client's
preferred one, and the data invites her to anyway.

Fix either end: add the `Preferred Room Names` lookup from item 5 so the
reference resolves, or remove the clause from the Technical Requirements text.
Until then expect the claim to reappear — it is the data prompting it, not the
model inventing freely.

**8. ~~Does the bot have `reactions:write`?~~ RESOLVED (marked 2026-09-25):** yes. The 👀 acknowledgement visibly lands on incoming messages (seen on the 2026-09-23 QA smoke tests). Original note:

Jessie puts 👀 on an incoming message and removes it when she replies, so people
can see it landed during the 7–12 seconds a turn takes. Without the scope the
reaction silently never appears — replies still work, so it fails invisibly.
Needs the scope added in the Slack app config and a reinstall.

**9. The Claude Slack connector appends a suffix to messages. Fixed.**

Messages sent through it arrive as `reset *Sent using* <@U0AVDBNH1K4>`.

Fixed as of v81: the confirmation gate strips that suffix before deciding
whether a reply was a yes or a no, so approval and refusal steps *can* now be
driven through the connector.

Also fixed in v84: the memory `reset` command strips the suffix too, so `reset`
sent through the connector clears memory. Nothing outstanding here — kept as a
record of why the gate strips that suffix at all.

**12. `PUT /api/v1/workflows/:id` reports success and changes nothing.** — RESOLVED 2026-09-18.

Seen on 2026-08-30 pushing the main workflow: the request returned without an
error, the response carried no `name` or `updatedAt`, and pulling the workflow
back showed every node unchanged. The same JSON imported through the browser UI
applied correctly.

**Root cause: payload shape, not a broken write path.** The public API `PUT`
accepts a body of exactly `{name, nodes, connections, settings}` and rejects any
extra top-level or `settings` key (`400 request/body/settings must NOT have
additional properties`). The 2026-08-30 attempt sent the whole pulled export
(carrying `id`, `active`, `activeVersion`, `tags`, and settings keys like
`binaryMode`, `callerPolicy`, `availableInMCP`, `timeSavedMode`), so it never
applied. Pruning `settings` to the API-allowed keys makes the `PUT` land, and
n8n *preserves* the internal settings that were not sent (verified: `binaryMode`
and `callerPolicy` survive a prune-and-PUT), so nothing is lost.

`./scripts/n8n-write` now does this safely: `put <id> <file>` (schema-clean PUT),
plus `activate` / `deactivate` for the tool-schema reload toggle. Proven on the
live main + Book Session on 2026-09-18 (External/Personal `bookingType` ship).
Still: pull before you write, and toggle Active off/on after changing tool inputs.

**17. ~~Engineer initials in booking titles are composed by the model.~~ RESOLVED 2026-09-25 (Book Session v45):** the `All Bookers` staff resolver rewrites the title's initials from Bookers `Initials` (see #31). Original note: A title like
`SESSION / Client / KC` has the engineer's initials written by the agent with no
lookup behind them, so a wrong guess becomes a wrong calendar title. Fixing it
properly means an Airtable engineer lookup inside `Book Session` — a new node in
that sub-workflow, and a design decision, not a repair.

**19. ~~Two diverging working copies of this repo.~~ RESOLVED (marked 2026-09-25):** everything listed below as missing is now in this repo: `webhook-canary`, `baseline`, the 2–4 Sep evidence (now `docs/outages/evidence/`), the 7 Sep QA and test log, the outage write-up, CANARY-SETUP, EOD-09-08, and the v116–v120 / book-session v26–28 files. Original note:
Numbering is settled: **we use v120**, Howard's number. Verified 8 Sep that the live
main workflow is **byte-for-byte identical** to
`workflows/project-jessie-v120.json` — same 40 nodes, same Guard Probe (436 lines),
same system prompt. (It was briefly numbered v119 here; renamed, content untouched, so
the file still matches live exactly. Guard Probe's own code comments still say "until
v119" — left alone deliberately, since editing them would make the file stop matching
live.) Going forward, don't hand-number in parallel: name the file after what the pull
actually is.

The real problem is that his copy is **not this repo**. His EOD reports "nothing
committed since 31 Aug 12:29", while this repo has been committed to daily all week —
so he is working in a separate folder (most likely the original handoff copy, not a
clone). Things that exist only in his copy and are **missing from here**:

- `scripts/webhook-canary` — the signed-verification probe, the only thing that
  catches a silent signature rejection
- `scripts/baseline` and `evidence/baseline-2026-09-07_1712.json`
- `evidence/jessie-executions-2026-09-02_to_09-04.json` — **the only surviving copy of
  the 2-4 Sept execution data**, everything else was pruned
- `QA-2026-09-07.md`, `TEST-LOG-2026-09-07.md`, `OUTAGE-2026-09-02.md`,
  `CANARY-SETUP.md`, `EOD-2026-09-08.md`
- his `v116-v120` and `book-session v26-28` workflow files

Until those are merged in, this repo is not the record it claims to be. Whoever
reconciles them should merge *into* this repo (it has the history), not the other way.

**20. ~~`EOD-2026-09-08.md` is referenced but not in hand.~~ RESOLVED (marked 2026-09-25):** it's in the repo at `docs/eod/EOD-2026-09-08.md`. The connector-machine-sleeps hypothesis it carries is still an open outage lead; see `docs/outages/OUTAGES.md`. Original note: `MONITOR-SETUP.md` cites it
for the **connector-machine-sleeps hypothesis** — that the machine running the
Cloudflare tunnel connector sleeps, dropping inbound while n8n keeps running. That
would fit the "breaks when nobody is using it, heals itself" pattern better than
anything in `OUTAGES.md`. Note the 8 Sept instrumented window argues against it for
*that* window (278 consecutive 200s straight through the tunnel), but it may well
explain others. Get that doc and the connector's sleep/wake log.

**24. ~~Add a `Preemption Rank` field to `Session Types`.~~ RESOLVED (marked 2026-09-25):** the field exists and is populated. Live `referenceData.preemptionRanks` reads e.g. Celebrity Recording 100, Post Mixing / QC / Localization Editing 50, and the preemption flow was proven live on 2026-09-23. Original note:
Raised 2026-09-21. The consent engine ([consent-engine.md](docs/design/consent-engine.md)) needs a
deterministic way to know one session type outranks another (e.g. Celebrity Recording > VO) before it
may offer to preempt an occupied room. Add a Number field `Preemption Rank` on `Session Types`
(`tblxEvRNPneUhQxUv`), higher = outranks, blank = 0 = never preempts. Tel (she) sets the values — a
suggested starting table is in the design doc. **Inert until the preemption branch reads it**, so it
can be added any time with zero effect on the live bot. Not created yet (spec only) per Howard's "write
the spec" instruction.

**25. Every booking is stamped "Created by: Howard Luistro", and the invite emails go to Howard.** — RESOLVED 2026-09-22.

Switched live 2026-09-22: the "Google Calendar account" credential (`6D1r3kaq6KaFdL0a`)
was reconnected as `calendar@hitproductions.net` (display name "Jessie Calendar Bot"). No
workflow edits, no re-import — `verify-ids` still green. Confirmed end to end: a SWITCHTEST
booking through Jessie created an event whose `creator.email` is `calendar@hitproductions.net`
(UI "Created by: Jessie Calendar Bot"), with Booked by / ref / engineer / room all intact;
`health`, `verify-ids`, `test-nodes --live` all green. **Both paths verified live under the new
credential:** a full book→cancel cycle through Jessie (execs 10181 book / 10187 cancel,
`claimProbe` booked + cancelled confirmed) — so Cancel Booking's `Delete Event` + calendar
`httpRequest` reads work as `calendar@` too, and the event was confirmed removed from KDC. Google Workspace prerequisites done by
Howard + Sir Pao (write on KDC, resource booking, account rename in Admin console).

**Token-expiry risk checked and cleared 2026-09-22.** Confirmed the OAuth app (Google Cloud
project "JESSIE" → Google Auth Platform → Audience) is **User type: Internal**. Internal apps
have no "Testing" mode and no ~7-day refresh-token expiry, so there is no silent-break risk from
this. Do NOT click "Make external" — that would move it out of the safe state.

Original problem (for the record):

The calendar OAuth credential in n8n (`googleCalendarOAuth2Api`, id `6D1r3kaq6KaFdL0a`,
"Google Calendar account") is authenticated as `howard@hitproductions.net`, so Google stamps
that account as the event *creator* and sends every "New event" organizer email to Howard's
inbox. Noticed 2026-09-22 — the CEO flagged that all test bookings look like they're Howard's.
The booker (`ref:` / "Booked by:") is already correct; only the Google-level creator is wrong.

Fix is to re-authenticate that one credential as a neutral `calendar@hitproductions.net` — no
workflow edits, no re-import (`verify-ids` stays green). Full cutover + smoke-test runbook:
`docs/runbooks/CALENDAR-ACCOUNT-SWITCH.md`.

**Blocked on Google Workspace (needs admin), all prerequisites before the reconnect:**
- `calendar@hitproductions.net` exists as a sign-in-able Workspace account (not just an alias).
- It has "Make changes to events" on KDC Bookings (`c_re5mcrg9om0macp9doqhlsi83g@...`).
- It can book the room resources (Studio 1–8 / A–F / M1–8 etc.).
- The Google Cloud OAuth client's consent screen allows it (add as test user if External/Testing).

The reconnect itself needs the `calendar@` password, so Howard runs it (can't be scripted).
Past events keep Howard's name — Google won't change an existing event's creator.

**31. ~~Title initials are blocked, but not auto-corrected to the right person.~~ RESOLVED 2026-09-25 (Book Session v45):** an `All Bookers` read + staff resolver now rewrites engineer/arranger to the canonical Bookers name and initials, and refuses anyone not on the list (`ENGINEER_UNKNOWN`). Original note: Found 2026-09-24: a
Celebrity Recording titled *BROWSE / Jem Lim / Drey* — the engineer's nickname (Daryl Reyes goes by "Drey",
initials **DR**) landed in the initials slot instead of `DR`. Book Session now has a `TITLE_INITIALS` guard
that **blocks** any 3-segment studio title whose last segment is not proper initials (`DR` / `DR x PL`), so a
name/nickname can no longer reach the calendar — but the model has to *retry* and produce the right initials
itself, and it is nondeterministic (in testing it produced "Drey x Brian Cua" one turn and the correct
"DR x BC" the next). The clean fix is a **deterministic rewrite**: map the engineer/arranger name-or-nickname
to canonical initials from Airtable and rewrite the segment, so `Drey → DR` always. Blocker: **Book Session
has no Bookers data** (only Get Client + Get Booker-for-the-requester). Needs a Bookers alias→initials map
plumbed in — cleanest via `Room Table`'s `referenceData` (already an input to Book Session), which means
adding a Bookers read to the context lane. Deferred from QA round 2 (2026-09-24) as a core-path change; the
guard holds the line meanwhile.

---

## Known constraints (not tasks)

Things that are true of the platform and cost time to rediscover. Nothing to do.

**14. A Code node cannot reference a tool node — it hangs the task runner.**

`$('Book Session')` inside `Guard Probe` blocks until the task runner's 60-second
timeout, then fails the node with `Unknown error`. Measured repeatedly on
2026-08-30: 60,007 / 60,008 / 60,015 / 60,026 ms across four runs, against ~70 ms
for the same node without it.

It is specific to nodes wired to the agent's `ai_tool` port, which produce no
`main` output — `$('Gate Context')` and `$('Room Table')` are both fine. Isolated
by shipping the lookup on its own as a diagnostic that rewrote no text.

What it cost: the natural guard against Jessie claiming a booking she never made
(seen once in 120 runs) had to be built another way. **Solved without needing
anything from the server** — `returnIntermediateSteps` on the agent node makes it
report its own tool calls, and those arrive on `Guard Probe`'s input, where no
lookup is involved. That turned out to be a better check than the one that was
blocked: it can require a *success status* on this turn, not merely that a node
executed at some point.

Worth raising with whoever maintains the n8n instance only as a question: whether
this is expected for `ai_tool` nodes or a bug in the installed version. Nothing
is blocked on the answer — it is recorded so the next person does not spend an
evening rediscovering it.

---

## Withdrawn

*Nothing currently withdrawn.*

**Task-runner warm-up, briefly withdrawn and reinstated.** This file once claimed
the first Code node costs ~3.5s; that was withdrawn on 2026-08-30 as a
mismeasurement, then reinstated the same day as item 13 when a proper sample
showed it is real and bimodal. The withdrawal was based on runs that happened to
catch a warm runner. Kept here as a note on how the mistake was made.
