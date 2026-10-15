#!/usr/bin/env python3
"""main v268 (typed series to form): a typed repeating booking - "book studio 7 every monday 2-4pm for 4 weeks", "book a
dubbing session every weekday until nov 30", "book likha every tuesday and thursday, 6 times" - no longer goes to the
chat's series card and its typed yes (the last one; decided 15 Oct: every confirmation a button or a form). Form Offer
reads the pattern too - how often (every week / every weekday / every day), the days, how many times or until a date, and
the first date (the next of those days when none is named) - shows it in the reply ("Every Monday · 4 times") and puts it
on the Book a room button; Slack Interactions v14 opens step 1 with Repeats ticked and filled in. The form then checks
every date and books through Book Series, as a series started in the form does (v13).
Built on workflows/imported/project-jessie-v267-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v267-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v268.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}
js = by["Form Offer"]["parameters"]["jsCode"]


def rep(a, b):
    global js
    assert js.count(a) == 1, a[:70]
    js = js.replace(a, b)


rep("// Form Offer (main v263; v264: labels with colons, \"for X\" as the project; v266: read only from this message):",
    "// Form Offer (main v263; v264: labels with colons, \"for X\" as the project; v266: read only from this message; v268: a series too):")
rep("  else if (/\\b(?:every|weekly|daily|biweekly|fortnightly|recurring|series|weekdays)\\b/i.test(t)) skip('a series');\n", "")
rep("    if (dates.length === 1) P.d = dates[0];\n    else if (dates.length > 1) delete P.d;\n",
    r"""    // v268: a repeating booking - how often, the days, how many times or until when, read from this message
    const tl8 = t.toLowerCase();
    const DK = { sun: 'SU', sunday: 'SU', mon: 'MO', monday: 'MO', tue: 'TU', tues: 'TU', tuesday: 'TU', wed: 'WE', wednesday: 'WE',
      thu: 'TH', thur: 'TH', thurs: 'TH', thursday: 'TH', fri: 'FR', friday: 'FR', sat: 'SA', saturday: 'SA' };
    const seriesWords = /\b(?:every|weekly|daily|weekdays|recurring|repeat(?:ing|s)?|series)\b/.test(tl8) || /\b(?:mon|tues?|wednes|thurs?|fri|satur|sun)days\b/.test(tl8);
    let R8 = null;
    if (seriesWords) {
      R8 = {};
      const days = []; let m8; const rd = /\b(sun(?:day)?|mon(?:day)?|tue(?:s(?:day)?)?|wed(?:nesday)?|thu(?:r(?:s(?:day)?)?)?|fri(?:day)?|sat(?:urday)?)s?\b/g;
      const untilAt = tl8.search(/\b(?:until|till|thru|through)\b/);
      while ((m8 = rd.exec(tl8))) { if (untilAt !== -1 && m8.index > untilAt) continue; const k = DK[m8[1]]; if (k && days.indexOf(k) === -1) days.push(k); }
      if (/\b(?:every ?day|daily)\b/.test(tl8)) R8.f = 'daily';
      else if (/\b(?:weekdays?|every weekday|mon(?:day)?\s*(?:-|–|to|thru|through)\s*fri(?:day)?)\b/.test(tl8)) R8.f = 'weekdays';
      else { R8.f = 'weekly'; if (days.length) R8.days = days; }
      const NUM = { two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10, eleven: 11, twelve: 12, thirteen: 13, fourteen: 14, fifteen: 15, sixteen: 16 };
      const mc = tl8.match(/\b(\d{1,2}|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen)\s*(?:x\b|times\b|sessions?\b|weeks?\b|days?\b|occurrences?\b)/);
      if (mc) { const n = NUM[mc[1]] || Number(mc[1]); if (n >= 2 && n <= 16) R8.n = n; }
      const ds = dates.slice().sort();
      if (untilAt !== -1 && ds.length) { R8.u = ds[ds.length - 1]; if (ds.length > 1) P.d = ds[0]; else delete P.d; }
      else if (ds.length) P.d = ds[0];
      // no first date named: the next of those days after today
      if (!P.d && /^\d{4}-\d{2}-\d{2}$/.test(String(g.todayIso || ''))) {
        const want = R8.f === 'daily' ? [0, 1, 2, 3, 4, 5, 6] : R8.f === 'weekdays' ? [1, 2, 3, 4, 5]
          : (R8.days || []).map(k => ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'].indexOf(k));
        if (want.length) { const cur = new Date(g.todayIso + 'T12:00:00Z');
          for (let i = 0; i < 8; i++) { cur.setUTCDate(cur.getUTCDate() + 1); if (want.indexOf(cur.getUTCDay()) !== -1) { P.d = cur.toISOString().slice(0, 10); break; } } }
      }
      if (R8.f === 'weekly' && !R8.days && P.d) R8.days = [['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'][new Date(P.d + 'T12:00:00Z').getUTCDay()]];
      P.rep = R8;
    } else if (dates.length === 1) P.d = dates[0];
    else if (dates.length > 1) delete P.d;
""")
rep("""      const head = [P.r, dl, P.s ? fmtT(P.s) + ' – ' + fmtT(P.e) : ''].filter(Boolean).join(' · ');""",
    """      // v268: the pattern of a series ("Every Monday · 4 times", "Every weekday · until Tuesday, November 30")
      const DN = { SU: 'Sunday', MO: 'Monday', TU: 'Tuesday', WE: 'Wednesday', TH: 'Thursday', FR: 'Friday', SA: 'Saturday' };
      const ul = P.rep && P.rep.u ? new Date(P.rep.u + 'T12:00:00+08:00').toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' }) : '';
      const pat = !P.rep ? '' : [P.rep.f === 'daily' ? 'Every day' : P.rep.f === 'weekdays' ? 'Every weekday' : 'Every ' + (P.rep.days || []).map(k => DN[k]).join(' and '),
        P.rep.n ? P.rep.n + ' times' : '', ul ? 'until ' + ul : ''].filter(Boolean).join(' · ');
      const head = [P.r, P.rep ? (dl ? 'from ' + dl : '') : dl, P.s ? fmtT(P.s) + ' – ' + fmtT(P.e) : ''].filter(Boolean).join(' · ');""")
rep("""      const lines = any ? ['Here’s what I have so far:'].concat(head ? ['🗓️ *' + head + '*'] : []).concat(more ? [more] : [])""",
    """      const lines = any ? ['Here’s what I have so far:'].concat(head ? ['🗓️ *' + head + '*'] : []).concat(pat ? ['🔁 ' + pat] : []).concat(more ? [more] : [])""")
by["Form Offer"]["parameters"]["jsCode"] = js
wf["name"] = "Project Jessie — v268 (typed series to form)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT), len(wf["nodes"]), "nodes")
