# Design — relative date resolution ("next Thursday", etc.)

Status: **settled, deterministic, shipped** · rule re-confirmed 2026-09-21 (keep Tara's rule)

## Where it happens

Relative dates are resolved **deterministically in `Gate Context`** (main workflow), never by the
model. The resolved date **and its weekday** are injected into the prompt as *"DATES IN THIS MESSAGE,
ALREADY RESOLVED. Use these exactly … do not work them out again."* `Guard Probe` separately corrects
any wrong weekday the model prints beside a date. This exists because the model used to resolve dates
itself and was inconsistent — "next Thursday" came back as Sept 9 in one run and Sept 2 seven minutes
later from the identical prompt.

## The rule (Tara, 2026-08-30; kept 2026-09-21)

Weeks start **Monday**. For a reference "today":

- **"this Thursday"** = Thursday of the **current** week
- **"next Thursday"** = Thursday of the **next** calendar week
- **bare "Thursday"** = the **nearest upcoming** Thursday (this week's if still ahead, else next week's)

Formula (in `Gate Context`): `weekMonday = Monday of today's week`; `next X = weekMonday + 7 +
offset(X)`; `this X = weekMonday + offset(X)`; `bare X = weekMonday + offset(X)`, +7 if already past.

## The consequence QA should expect (not a bug)

"next X" and "nearest upcoming X" **differ only when today is Mon–Wed** (before this week's X). Then
"next X" is a week further out. Worked example — target Thursday:

| "Today" | "next Thursday" |
|---|---|
| Wed Sep 1 · Thu 2 · **Fri 3** · Sat 4 · Sun 5 | **Sep 9** |
| **Mon Sep 6 · Tue 7** | **Sep 16** |

So from **Fri Sep 3**, "next Thursday" = **Sep 9** (correct). A QA that saw Sep 16 from a Friday hit
the *old* model-driven build; from a Mon/Tue, Sep 16 is the rule working as intended. If someone
means the sooner one on a Mon–Wed, they say the bare weekday ("book Thursday") or the explicit date.

## Safety net

Jessie always shows the resolved **date + weekday** in the summary before the `(yes/no)` step, so a
requester can catch a misread at confirmation. Locked by `test-gate` ("next Thursday" → 9 Sep 2027,
"this Thursday" → 2 Sep 2027) within the `test-nodes` run.
