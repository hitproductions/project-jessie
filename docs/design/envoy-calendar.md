# Design — Envoy Rooms on the studio resource calendars

Status: **exploration (post-launch)** · Started 2026-09-22 · Owner: Tel

## Idea

Use **Envoy Rooms** (door tablet / mobile / Google Calendar) as a **visibility layer** for studio
bookings — the tablets and Envoy views show what's booked. **Bookings are made only through Jessie**
(and, for launch, on our calendar); Envoy is not a second booking front-end. It works without a direct
Jessie ↔ Envoy integration because both sit on the same Google Calendar **room resources**.

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

## Jessie → Envoy visibility — validated

**Jessie → Envoy: works — validated 2026-09-22.** Jessie invites the room resource on every event, so
her bookings appear on the resource calendars, which is exactly what Envoy reads. Confirmed live with
the Studio 7 test booking above (on the resource calendar, room accepted). ✅

Because **bookings are made only through Jessie**, Envoy stays a read-only view of what Jessie has
booked — so there's no reverse-direction sync to design around.

## Process to connect Envoy (for IT)

1. **Resources confirmed** ✅ (2026-09-22) — rooms are managed Google resources.
2. **Super-admin confirmed** ✅ — IT holds it.
3. **Envoy Rooms plan** — confirm the workspace is licensed for Rooms (paid product).
4. **Auth method** — either a service account granted a super/global admin role (Envoy auto-lists all
   rooms), or share each room's resource calendar with the service account ("Share with specific
   people" → **Make changes to events**). Least-privilege = the sharing route.
5. **Connect in Envoy dashboard** — Rooms → Google Calendar → authenticate → select the rooms to pair
   with the location → Assign → Save.
6. **Confirm visibility** — open a connected room in Envoy and check that a Jessie booking shows on
   the correct date (mind the 2027 QA year-shift). Envoy is display-only; bookings stay in Jessie.

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

## Sources

- Envoy — [Connecting your calendar](https://envoy.help/en/articles/3613982-connecting-your-calendar)
- Envoy — [Preparing your Google calendar](https://envoy.help/en/articles/3688694-preparing-your-google-calendar)
- Envoy — [Troubleshooting Rooms](https://envoy.help/en/articles/3625453-troubleshooting-rooms)
- Google — [Share room and resource calendars](https://knowledge.workspace.google.com/admin/calendar/share-room-and-resource-calendars)
