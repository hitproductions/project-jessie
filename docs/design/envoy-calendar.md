# Design — Envoy Rooms on the studio resource calendars

Status: **planned (post-launch)** · Started 2026-09-22 · Owner: Tel · Decision 2026-09-23: tablets are a booking source

## Idea

Use **Envoy Rooms** (door tablet / mobile / Google Calendar) as a **second booking source** alongside
Jessie — people can book a studio from the door tablets, and those bookings and Jessie's must stay
consistent. Both sit on the same Google Calendar **room resources**, which become the shared source of
truth for what's booked, so no direct Jessie ↔ Envoy integration is needed.

## Why it can work — the mechanism

Jessie doesn't only write to its own group calendar. On every booking, `Book Session` → **Create
Event** invites the room's Google **resource calendar** as an attendee (the `…@resource.calendar.google.com`
addresses; see the room→resource map below). Google then places the event on that room's resource
calendar and auto-accepts it — the `Verify` node already reads the resource's `declined` response to
detect a room that's already taken.

Envoy Rooms connects to exactly those Google Workspace room resources. So **a Jessie booking already
lands on the resource calendar Envoy would read** — no direct link needed. The resource calendar is
the bridge.

## Confirmed 2026-09-22

- **All studios/booths are managed Google Workspace resources** (Admin → Directory → Buildings and
  resources → Manage resources). Verified against the resource IDs in `Book Session` → Create Event.
- **IT holds Google Workspace super-admin.** Envoy's setup (a service-account grant, or per-room
  calendar sharing) is therefore an **IT request**, not something the Jessie dev team can do alone.
  (Same team that owns the Cloudflare account for `signal.hitpromanila.net`.)
- **Envoy is connected to these resource calendars, and Jessie → Envoy visibility is validated.** A
  Jessie test booking ("TEST JESSIE ENVOY", Studio 7, 23 Sep 2027 10:00–18:00) was confirmed sitting
  on Studio 7's resource calendar with the room accepted — the exact surface Envoy reads — so **a
  Jessie booking is visible in Envoy now** (view it in Envoy on the 2027 date, not tomorrow).
- **Tablet → resource-calendar path validated (2026-09-23).** A real Envoy door-tablet booking
  ("TEST ENVOY", Studio 7, 23 Sep 2026) landed on Studio 7's resource calendar — organizer = the room
  resource, description "Created by Envoy", room accepted — and was **absent from KDC Bookings**.
  Confirms a tablet booking sits on the exact surface Jessie will read after the read-side change, and
  is invisible to her until then.

## Two directions

**Jessie → Envoy: works — validated 2026-09-22.** Jessie invites the room resource on every event, so
her bookings appear on the resource calendars, which is exactly what Envoy reads. Confirmed live with
the Studio 7 test booking above (on the resource calendar, room accepted). ✅

**Envoy → Jessie: needs a change (decided 2026-09-23 — tablets are a booking source).** ❌ (until done)
A tablet booking lands on the room's **resource calendar**, but Jessie's `Check Conflicts` and `Room
Availability` read **only** the group calendar `c_re5…@group.calendar.google.com` — never the resource
calendars. So today Jessie is **blind to a tablet booking and could book over it.** Closing this is the
change below.

## Making tablets a booking source (the read-side change)

Point Jessie's availability **reads** at the **room resource calendars** instead of the group calendar.
Jessie's own bookings are already on the resource calendars (she invites the resource), so reading there
means she sees **everything** in one place — her own bookings, tablet/Envoy bookings, and the
personal-calendar bookings staff already make directly on a resource.

- **Scope (decided 2026-09-23): 3 workflows.**
    - **Prevent double-booking** — `Check Conflicts` (in `Book Session`) and the `Room Availability`
      workflow read the resource calendars, so Jessie won't book over an Envoy/tablet booking.
    - **Booker visibility** — `Find Booking` also reads the resource calendars, so a lookup ("what's
      booked in Studio 7?") includes tablet bookings.
- **Form:** a Google **freebusy** query across the resource calendars (plus the group calendar, for
  safety) for availability/conflicts; `Find Booking` lists the resource-calendar events (deduped —
  Jessie's own bookings and multi-room events appear on more than one calendar).
- **Tablet bookings are read-only in Jessie:** visible and block double-booking, but they carry no
  Jessie `ref:` marker, so Cancel/Move still refuse them (change them in Envoy). Existing behavior.
- **Writing is unchanged:** Jessie still creates bookings on the group calendar and invites the
  resource, so her events still show in Envoy. Only the read side moves.
- **Prerequisite — fix the Studio E id (below)**, or Studio E availability reads a deleted calendar.
- **Must be QA'd** (availability + double-booking are load-bearing) and is a **post-launch** change:
  dev freeze is 2026-09-23, launch 2026-10-12. Schedule it deliberately, not into the freeze.

### Studio E resource id is wrong (found 2026-09-23)

`Book Session` maps **Studio E → `c_18807te03d2sqh0lmtal9sbb04gao`**, which **does not resolve**
(deleted). The live Studio E resource is **`c_1888r4bbc2lhqgndmprism70nft64`** ("Studio E (5)", real
bookings, organizer KDC Bookings). So Jessie currently invites a dead Studio E resource — her Studio E
bookings don't reach the real resource calendar (Envoy won't see them) and Studio E availability is
unreliable. The id appears across the live workflows (Book Session, Room Availability, Find Booking,
main) — fix everywhere via pull-edit-import + QA.

## Process to connect Envoy (for IT)

1. **Resources confirmed** ✅ (2026-09-22) — rooms are managed Google resources.
2. **Super-admin confirmed** ✅ — IT holds it.
3. **Envoy Rooms plan** — confirm the workspace is licensed for Rooms (paid product).
4. **Auth method** — either a service account granted a super/global admin role (Envoy auto-lists all
   rooms), or share each room's resource calendar with the service account ("Share with specific
   people" → **Make changes to events**). Least-privilege = the sharing route.
5. **Connect in Envoy dashboard** — Rooms → Google Calendar → authenticate → select the rooms to pair
   with the location → Assign → Save.
6. **Confirm both directions** — a Jessie booking shows in Envoy (validated); and after the read-side
   change above, a tablet booking shows in Jessie's availability. Mind the 2027 QA year-shift when
   checking dates.

## Room → resource calendar map

From `Book Session` → Create Event (the live attendee map). Studio 1 uses the older
`hitproductions.net_…` resource-ID format — confirm it's still a managed resource.

| Room | Resource calendar ID |
|---|---|
| Studio 1 | `hitproductions.net_3737303833303637363538@resource.calendar.google.com` |
| Studio 2 | `c_18871bprki2umhrkjc4qcaldse1f8@resource.calendar.google.com` |
| Studio 3 | `c_1886me03bdcrki5bhu8vddknl472k@resource.calendar.google.com` |
| Studio 4 | `c_188e94dapvbp8jvrjmuga6qbof826@resource.calendar.google.com` |
| Studio 5 | `c_18889v3glj9cqiotg8j95jaqmdhmm@resource.calendar.google.com` |
| Studio 6 | `c_18838qt2ru30ein7gcefjiarplkre@resource.calendar.google.com` |
| Studio 7 | `c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com` |
| Studio 8 | `c_18863v8hd6f42isegdh9i30psuo9q@resource.calendar.google.com` |
| Studio A | `c_18843dclutqm6hl9nbeg002phapfu@resource.calendar.google.com` |
| Studio B | `c_1881vgb66tkpujjelnn3rniugd9pk@resource.calendar.google.com` |
| Studio C | `c_188797f37eu9ujs6ldpf3smn78joc@resource.calendar.google.com` |
| Studio D | `c_18801gc6ck77gho7jl0e1fug94u92@resource.calendar.google.com` |
| Studio E | ⚠️ workflow has `c_18807te03d2sqh0lmtal9sbb04gao` (**dead** — see Studio E note); live resource is `c_1888r4bbc2lhqgndmprism70nft64@resource.calendar.google.com` |
| Studio F | `c_188em7d58podeju3i8q6juqlufkls@resource.calendar.google.com` |
| Studio M | `c_1885k4adm87fqjd2j3j2usqftph5c@resource.calendar.google.com` |
| M1 | `c_1889v46vd62fkjk3i7r1hsfem7tcm@resource.calendar.google.com` |
| M2 | `c_1883ui6lnfc9ogt2hrmg57a30n72q@resource.calendar.google.com` |
| M3 | `c_188d7dkqgnfs6hu4iunlu5ogftct0@resource.calendar.google.com` |
| M4 | `c_18869nhmsj2uki8mljoi48v1cj7l4@resource.calendar.google.com` |
| M5 | `c_1889h30ci9noqjcbnoogad9qk75vq@resource.calendar.google.com` |
| M6 | `c_188f9gnq0a9tehf4g9ja57l83c0ts@resource.calendar.google.com` |
| M7 | `c_1880r9hhk9c2agpbko87o7fojosh0@resource.calendar.google.com` |
| M8 | `c_1884cu2cc84iujsjnu03s21f0ct9q@resource.calendar.google.com` |
| Salin | `c_1887hh5rsv6q4gt8hnu6ered170lg@resource.calendar.google.com` |
| Katha | `c_1881169pcpn12gsnm6i7sc0gjk7gk@resource.calendar.google.com` |
| Likha | `c_1886t6cjgrq0ihgpime01uibcqsg6@resource.calendar.google.com` |
| Lobby | `c_188227mpeagjuhi7gqlgns1di14be@resource.calendar.google.com` |

## Open items

- Confirm the Envoy Rooms subscription (step 3).
- Decide auth method with IT: super-admin service account vs per-room sharing (step 4).
- **Build + QA the read-side change** (Check Conflicts + Room Availability + Find Booking →
  resource-calendar reads) so tablet bookings block double-booking and show in lookups — post-launch.
- **Fix the Studio E resource id** across the live workflows (prerequisite for the read-side change).
- **Decide "reflected in our calendar":** the read-side change gives Jessie recognition + booker
  visibility; whether Envoy bookings should *also* mirror onto the KDC Bookings master calendar (a new
  sync workflow) vs. overlaying the resource calendars in the master view is a separate, open call.

## Sources

- Envoy — [Connecting your calendar](https://envoy.help/en/articles/3613982-connecting-your-calendar)
- Envoy — [Preparing your Google calendar](https://envoy.help/en/articles/3688694-preparing-your-google-calendar)
- Envoy — [Troubleshooting Rooms](https://envoy.help/en/articles/3625453-troubleshooting-rooms)
- Google — [Share room and resource calendars](https://knowledge.workspace.google.com/admin/calendar/share-room-and-resource-calendars)
