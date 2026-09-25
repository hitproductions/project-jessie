# Outage evidence

## `jessie-executions-2026-09-02_to_09-04.json`

A partial, pre-prune capture of the main Jessie workflow's executions from **2–4 September 2026**,
152 records. It is **the only surviving copy** of that window: the execution pruner (`KEEP_DAYS = 3`)
deleted everything before 4 September at 04:00 on 6 September, and the oldest execution n8n still holds
is 4 September 10:03.

What it does **not** cover: **5 September** is not in it, and it is a capture, not a complete export,
so an absence here does not prove an event didn't happen. Everything else about the 2 September outage
survives only as the written conclusions in [`../OUTAGE-2026-09-02.md`](../OUTAGE-2026-09-02.md) and
[`../OUTAGES.md`](../OUTAGES.md).

Moved here from the repo root `evidence/` on 2026-09-25 when the outage docs were grouped. The root
`evidence/` folder is still where `scripts/baseline` writes its snapshots.
