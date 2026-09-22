# Design — Envoy Rooms on the studio resource calendars

Status: **exploration (post-launch)** · Started 2026-09-22 · Owner: Tel

## Idea

Use **Envoy Rooms** (door tablet / mobile / Google Calendar) as a second way to book studios,
alongside Jessie, without a direct Jessie ↔ Envoy integration. Both would sit on the same Google
Calendar **room resources**, which become the shared source of truth for what's booked.

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

## Two directions — and they are not symmetric

**Jessie → Envoy: works today.** Jessie invites the room resource on every event, so her bookings
appear on the resource calendars → Envoy sees them. ✅

**Envoy → Jessie: does NOT work as-is.** ❌ An Envoy booking lands on the room's resource calendar,
but Jessie's availability logic reads a *different* calendar:

- `Book Session` → **Check Conflicts** and the whole **Room Availability** workflow query events from
  **only** the group calendar `c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com`. Neither reads
  the resource calendars.
- So Jessie would be **blind to an Envoy reservation and could double-book over it.**

**Do not roll Envoy out for live booking on shared rooms until the Jessie read-side is switched
(below) and QA'd.** Until then Envoy is safe only as read-only visibility of Jessie's bookings.

## The Jessie change that makes it two-way safe

Point Jessie's availability reads at the **room resource calendars** instead of the group calendar.
Because Jessie's own bookings are *also* on the resource calendars (she invites the resource), reading
there means she sees **everything** — her own bookings and Envoy's — in one place.

- Scope: **2 places** — `Check Conflicts` (in `Book Session`) and the `Room Availability` workflow.
- Preferred form: a Google **freebusy** query across the resource calendars — returns each room's busy
  blocks regardless of who booked it, matching the build's "compute availability, don't reason about
  it" principle.
- Must be QA'd: availability and double-booking are load-bearing guarantees. This is a **post-launch**
  change (launch is 2026-10-12, dev freeze 2026-09-23).

## Process to connect Envoy (for IT)

1. **Resources confirmed** ✅ (2026-09-22) — rooms are managed Google resources.
2. **Super-admin confirmed** ✅ — IT holds it.
3. **Envoy Rooms plan** — confirm the workspace is licensed for Rooms (paid product).
4. **Auth method** — either a service account granted a super/global admin role (Envoy auto-lists all
   rooms), or share each room's resource calendar with the service account ("Share with specific
   people" → **Make changes to events**). Least-privilege = the sharing route.
5. **Connect in Envoy dashboard** — Rooms → Google Calendar → authenticate → select the rooms to pair
   with the location → Assign → Save.
6. **Scoped pilot** — connect ONE low-traffic room, make a test booking in Envoy on a **2027 (QA)
   date**, confirm it appears on that room's resource calendar. Do not book real shared rooms in Envoy
   until the Jessie read-side change lands.

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
| Studio E | `c_18807te03d2sqh0lmtal9sbb04gao@resource.calendar.google.com` |
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
- Watch the write-contention question in the pilot: both Jessie and Envoy write to the same resource
  calendars — Google's resource auto-accept/decline should handle conflicts, but confirm behavior.
- Build + QA the Jessie read-side switch (Check Conflicts + Room Availability → resource calendars /
  freebusy) before any shared-room rollout.

## Sources

- Envoy — [Connecting your calendar](https://envoy.help/en/articles/3613982-connecting-your-calendar)
- Envoy — [Preparing your Google calendar](https://envoy.help/en/articles/3688694-preparing-your-google-calendar)
- Envoy — [Troubleshooting Rooms](https://envoy.help/en/articles/3625453-troubleshooting-rooms)
- Google — [Share room and resource calendars](https://knowledge.workspace.google.com/admin/calendar/share-room-and-resource-calendars)
