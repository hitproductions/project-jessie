# Archived n8n workflows

Copies of four superseded "Project Jessie v2" workflows, exported from n8n on
2026-08-31 before being deleted from the instance.

| File | Was | Last touched |
|---|---|---|
| `project-jessie-testing-1TFG8DEgEDZMCAHD.json` | Project Jessie v2 (testing) | 2026-08-28 |
| `project-jessie-backup-aug17-502pm-1GcIAeLdJZLeB8js.json` | BACKUP aug17_502pm | 2026-08-28 |
| `project-jessie-copy-aug17-331pm-9sTzJ45mOEIv4Las.json` | copy aug17_331pm | 2026-08-28 |
| `project-jessie-backup-aug14-513pm-jtNid6MGQiIsWL51.json` | backup 0814.513pm | 2026-08-14 |

They were deleted for a reason worth remembering. Each carried a Slack Trigger
with `watchWorkspace` wired to credential `nmFoMiSOz2wjLG1I` — which is now
**Posty's** bot token, not Jessie's. Switching any of them on would have done two
things: made Jessie reply as the Posty bot, and added a second workspace-wide
Slack listener on an app that already has one in `Posty — Events Endpoint`, so
every Slack message would reach two handlers. The blast radius was Posty, a live
service unrelated to this project.

They also predate the determinism rebuild — the oldest is 14 August, all of them
before v79 — so they are of no use as a fallback. `git log` holds every main
workflow version from v36 to v113, which is a better history than these were.

Kept as files rather than deleted outright only so nothing is unrecoverable.
Nothing references them and none had run recently.
