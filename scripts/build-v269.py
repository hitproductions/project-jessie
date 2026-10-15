#!/usr/bin/env python3
"""main v269 (build A: wording, buttons, series first day): notes from the slice 1 Slack test (15 Oct), with Slack
Interactions v17.
  - typed change / cancel reply: "Here's your proposed change – press *Change* to check the new time." / "Here's the
    booking – press *Change* to pick the new time." / "Here's the booking – press *Cancel* to cancel it." (was "Here it is");
  - the menu's examples in quotes: _"book studio 7 tomorrow 2-4pm"_ or _"is studio 8 free friday?"_;
  - My bookings beside Book a room on the booking reply;
  - a typed series naming several days started on the wrong one ("every tuesday and thursday" -> from Thursday Oct 21; live
    14:55): with no calendar date typed, a weekly series starts on the first of its days after today.
Built on workflows/imported/project-jessie-v268-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v268-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v269.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def patch(node, pairs):
    js = by[node]["parameters"]["jsCode"]
    for a, b in pairs:
        assert js.count(a) == 1, (node, a[:70], js.count(a))
        js = js.replace(a, b)
    by[node]["parameters"]["jsCode"] = js


patch("Change Reply", [
    ("""  blocks.push({ type: 'section', text: md(!one ? 'Which one?' : co.kind === 'cancel' ? 'Here it is - press *Cancel* to cancel it.'
    : hasNew ? 'Here it is - press *Change* to check the new time.' : 'Here it is - press *Change* to pick the new time.') });""",
     """  // v269: the wording from the Slack test
  blocks.push({ type: 'section', text: md(!one ? 'Which one?' : co.kind === 'cancel' ? 'Here’s the booking – press *Cancel* to cancel it.'
    : hasNew ? 'Here’s your proposed change – press *Change* to check the new time.' : 'Here’s the booking – press *Change* to pick the new time.') });"""),
])
patch("Menu Check", [
    ("'Or just type it, like _book studio 7 tomorrow 2-4pm_ or _is studio 8 free friday?_'",
     "'Or just type it, like _\"book studio 7 tomorrow 2-4pm\"_ or _\"is studio 8 free friday?\"_'"),
])
patch("Form Offer", [
    ("""          text: { type: 'plain_text', text: 'Book a room' } }] },""",
     """          text: { type: 'plain_text', text: 'Book a room' } },
          { type: 'button', action_id: 'my_bookings', value: 'menu', text: { type: 'plain_text', text: 'My bookings' } }] },   // v269"""),
    ("""      const ds = dates.slice().sort();
      if (untilAt !== -1 && ds.length) { R8.u = ds[ds.length - 1]; if (ds.length > 1) P.d = ds[0]; else delete P.d; }
      else if (ds.length) P.d = ds[0];""",
     """      const ds = dates.slice().sort();
      // v269 (live 14:55): "every tuesday and thursday" started on Thursday - Gate resolved only one of the named days. Unless a
      // calendar date is typed (a month and day, a d/m date, "tomorrow", "today"), a weekly series with named days starts on
      // the first of those days after today (worked out below), not on Gate's date.
      const head8 = untilAt === -1 ? tl8 : tl8.slice(0, untilAt);
      const typedDate = /\\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\\.?\\s*\\d{1,2}\\b|\\b\\d{1,2}(?:st|nd|rd|th)?\\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)|\\b\\d{1,2}\\/\\d{1,2}\\b|\\b(?:tomorrow|today|tonight|tom)\\b/.test(head8);
      const namedOnly = R8.f === 'weekly' && R8.days && R8.days.length && !typedDate;
      if (untilAt !== -1 && ds.length) { R8.u = ds[ds.length - 1]; if (ds.length > 1 && !namedOnly) P.d = ds[0]; else delete P.d; }
      else if (ds.length && !namedOnly) P.d = ds[0];
      else delete P.d;"""),
])
wf["name"] = "Project Jessie — v269 (build A: wording, buttons, series first day)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
