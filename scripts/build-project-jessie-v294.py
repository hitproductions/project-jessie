#!/usr/bin/env python3
"""Builds workflows/project-jessie-v294.json - Project Jessie — v294 (typed date ranges), 19 Nov (PENDING 157).

A Localization coordinator's typed requests (Turn Log, 12 / 15 Nov) all reached the form wrong. Form Offer, by code:
- A date span is read: "dec 9 to 25", "december 9 to 25", "november 24 to nov 28", "24-28 nov", "dec 28 to jan 2" (also "-", "–",
  "until", "till", "thru", "through"; a time after the second number - "dec 9 to 10am" - is not a span). It makes a series: the
  first date on or after the start that is one of the days asked for, until the end. No days named -> every day in the span.
  Before: only "until / through" + a full date was read, so "dec 9 to 25" started on the next Wed / Fri after today, and
  "november 24 to nov 28" had no date at all.
- A day range is read: "wed to fri", "wed-fri", "wed thru fri" -> Wednesday, Thursday and Friday (before: Wednesday and Friday;
  "thru" even ended the day list). Monday to Friday is still "Every weekday". A list after "days:" / "Repeats:" counts as a series.
- The same booking request sent again after an offer gets the offer again (before: "I can only help with bookings." - it was
  "nothing new after an offer").
- A project code is not also the client: a Client equal to the Project or Code is dropped, and when Project and Code are the same
  the reply shows "Code:" once (before: "Project: NET-PANDA / Code: NET-PANDA / Client: NET-PANDA").
- Booked For: a name after "engineer" / "arranger" ends at a full stop or comma ("Engineer John. Time is ..." gave no engineer);
  "engr", "engr." and "eng:" are read as engineer ("Engr John", "engr: JC" gave no engineer).
Built on workflows/project-jessie-v293.json (== live).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "project-jessie-v293.json")))
by = {n["name"]: n for n in wf["nodes"]}


def rep(old, new, count=1):
    p = by["Form Offer"]["parameters"]
    assert p["jsCode"].count(old) == count, (old[:70], p["jsCode"].count(old))
    p["jsCode"] = p["jsCode"].replace(old, new)


HELPERS = r"""    // v294 (PENDING 157): day ranges ("wed to fri", "wed-fri", "wed thru fri") written out as the days, before anything reads them
    const __DN7 = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];
    const __dIx = w => { const x = String(w || '').toLowerCase().slice(0, 3); return __DN7.indexOf(x); };
    const __dayRanges = s => s.replace(/\b(sun|mon|tue|wed|thu|fri|sat)[a-z]*\.?\s*(?:-|–|to|thru|through)\s*(sun|mon|tue|wed|thu|fri|sat)[a-z]*\b/g, (m, a, b) => {
      const i = __dIx(a), j = __dIx(b); if (i < 0 || j < 0 || i === j) return m; const out = []; for (let k = i; ; k = (k + 1) % 7) { out.push(__DN7[k]); if (k === j) break; } return out.join(' '); });
    // v294: a date span ("dec 9 to 25", "november 24 to nov 28", "24-28 nov", "dec 28 to jan 2") -> { s, e } (YYYY-MM-DD)
    const __rg = (function (txt, todayIso) {
      try {
        const MO = { jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6, jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12 };
        const mOf = w => MO[String(w || '').toLowerCase().slice(0, 3)] || 0;
        const MON = '(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)';
        const SEP = '\\s*(?:-|–|to|until|till|thru|through)\\s*', ORD = '(?:st|nd|rd|th)?';
        const NOTTIME = '(?!\\s*(?::|am\\b|pm\\b|nn\\b|a\\.m|p\\.m)|\\d)';
        let m1 = 0, d1 = 0, m2 = 0, d2 = 0, y = 0, m;
        if ((m = String(txt).match(new RegExp('\\b' + MON + '\\.?\\s*(\\d{1,2})' + ORD + SEP + '(?:' + MON + '\\.?\\s*)?(\\d{1,2})' + ORD + '\\b' + NOTTIME + '(?:,?\\s*(20\\d\\d))?', 'i'))))
          { m1 = mOf(m[1]); d1 = +m[2]; m2 = m[3] ? mOf(m[3]) : 0; d2 = +m[4]; y = m[5] ? +m[5] : 0; }
        else if ((m = String(txt).match(new RegExp('\\b(\\d{1,2})' + ORD + '\\s*(?:-|–|to)\\s*(\\d{1,2})' + ORD + '\\s+(?:of\\s+)?' + MON + '\\b(?:,?\\s*(20\\d\\d))?', 'i'))))
          { d1 = +m[1]; d2 = +m[2]; m1 = mOf(m[3]); y = m[4] ? +m[4] : 0; }
        if (!m1 || !d1 || !d2) return null;
        if (!m2) m2 = d2 < d1 ? (m1 % 12) + 1 : m1;
        const T = /^\d{4}-\d{2}-\d{2}$/.test(String(todayIso || '')) ? todayIso : new Date(Date.now() + 8 * 3600000).toISOString().slice(0, 10);
        const iso = (yy, mm, dd) => { const x = new Date(Date.UTC(yy, mm - 1, dd)); return x.getUTCMonth() === mm - 1 && x.getUTCDate() === dd ? x.toISOString().slice(0, 10) : ''; };
        let y1 = y || +T.slice(0, 4); let s = iso(y1, m1, d1); if (!s) return null;
        if (!y && s < T) { y1 += 1; s = iso(y1, m1, d1); }
        let e = iso(y1 + (m2 < m1 ? 1 : 0), m2, d2); if (!e || e < s) return null;
        if ((Date.parse(e) - Date.parse(s)) / 86400000 > 186) return null;   // six months at most (Slack Interactions' series cap)
        return { s, e };
      } catch (er) { return null; }
    })(t, g.todayIso);
"""
rep("    const tl8 = t.toLowerCase();\n", HELPERS + "    const tl8 = __dayRanges(t.toLowerCase());   // v294\n")
rep("    const seriesWords = /\\b(?:every|weekly|daily|weekdays|recurring|repeat(?:ing|s)?|series)\\b/.test(tl8)",
    "    const seriesWords = !!__rg || /\\b(?:days?|repeats?)\\s*:/.test(tl8) || /\\b(?:every|weekly|daily|weekdays|recurring|repeat(?:ing|s)?|series)\\b/.test(tl8)")
rep("      else { R8.f = 'weekly'; if (days.length) R8.days = days; }\n",
    "      else { R8.f = 'weekly'; if (days.length) R8.days = days; }\n"
    "      if (R8.f === 'weekly' && days.slice().sort().join() === 'FR,MO,TH,TU,WE') { R8.f = 'weekdays'; delete R8.days; }   // v294: mon to fri\n"
    "      if (__rg && R8.f === 'weekly' && !days.length) R8.f = 'daily';   // v294: a span with no days named - every day in it\n")
rep("      P.rep = R8;\n    } else if (dates.length === 1) P.d = dates[0];",
    "      // v294: a span - the first date on or after its start that is one of the days asked for, until its end\n"
    "      if (__rg) {\n"
    "        const want = R8.f === 'daily' ? [0, 1, 2, 3, 4, 5, 6] : R8.f === 'weekdays' ? [1, 2, 3, 4, 5] : (R8.days || []).map(k => ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'].indexOf(k));\n"
    "        const cur = new Date(__rg.s + 'T12:00:00Z'); let first = '';\n"
    "        for (let i = 0; i < 8; i++) { const iso = cur.toISOString().slice(0, 10); if (iso > __rg.e) break; if (!want.length || want.indexOf(cur.getUTCDay()) !== -1) { first = iso; break; } cur.setUTCDate(cur.getUTCDate() + 1); }\n"
    "        if (first) { P.d = first; R8.u = __rg.e; delete R8.n; }\n"
    "      }\n"
    "      P.rep = R8;\n    } else if (dates.length === 1) P.d = dates[0];")
rep("    if (prev && !intent && JSON.stringify(P) === JSON.stringify(prev)) skip('nothing new after an offer');",
    "    // v294: a project code is not the client too (\"for NET-PANDA\" was Project, Code and Client)\n"
    "    if (P.c && [P.pj, P.cd].some(x => x && String(x).trim().toLowerCase() === String(P.c).trim().toLowerCase())) delete P.c;\n"
    "    // v294: the same booking request sent again after an offer gets the offer again, not the menu\n"
    "    const __again = /\\bstudio\\s*[1-8a-fm]\\b|\\bm[\\s-]?booth\\s*[1-8]\\b|\\bm[1-8]\\b|\\b(?:likha|salin|katha|lobby)\\b/i.test(t) || !!__rg\n"
    "      || /\\b\\d{1,2}(?::\\d{2})?\\s*(?:am|pm|nn)\\b/i.test(t) || /\\b(?:project|client|session|recording|mixing|dubbing|editing|meeting|title|code)\\b/i.test(t);\n"
    "    if (prev && !intent && !__again && JSON.stringify(P) === JSON.stringify(prev)) skip('nothing new after an offer');")
rep("P.pj ? 'Project: ' + P.pj : '', P.cd ? 'Code: ' + P.cd : '',",
    "P.pj && !(P.cd && String(P.cd).toLowerCase() === String(P.pj).toLowerCase()) ? 'Project: ' + P.pj : '', P.cd ? 'Code: ' + P.cd : '',   /* v294 */")

# Form Offer reads Booked For's phrases back in this message - with the same spelling
rep("    const lowT = t.toLowerCase();\n",
    "    const lowT = t.toLowerCase().replace(/\\bengrs\\b\\.?/g, 'engineers').replace(/\\bengr\\b\\.?/g, 'engineer').replace(/\\beng\\.?\\s*:/g, 'engineer:');   // v294: as Booked For reads it\n")
# Booked For: "engr" / "engr." / "eng:" read as engineer ("Engr John", "engr: JC" gave no engineer)
bf = by["Booked For"]["parameters"]
OLDC = "const clean = s => String(s || '').replace(/\\*sent using\\*[\\s\\S]*$/i, '').trim();"
assert bf["jsCode"].count(OLDC) == 1, bf["jsCode"].count(OLDC)
bf["jsCode"] = bf["jsCode"].replace(OLDC, "const clean = s => String(s || '').replace(/\\*sent using\\*[\\s\\S]*$/i, '').trim()\n"
  "    .replace(/\\bengrs\\b\\.?/gi, 'engineers').replace(/\\bengr\\b\\.?/gi, 'engineer').replace(/\\beng\\.?\\s*:/gi, 'engineer:');   // v294 (PENDING 157)")

# Booked For: a name after "engineer" / "arranger" ends at a full stop or comma ("Engr John. Time is ..." read "John. Time")
OLDR = "    for (const re of after) { let m; while ((m = re.exec(text))) { const r = resolveWords(m[1].split(/\\s+/)); if (r) return Object.assign(r, { phrase: m[0].trim() }); } }"
assert bf["jsCode"].count(OLDR) == 1, bf["jsCode"].count(OLDR)
bf["jsCode"] = bf["jsCode"].replace(OLDR, "    for (const re of after) { let m; while ((m = re.exec(text))) { const _w = m[1].split(/[.,;!?]/)[0].trim(); const r = _w ? resolveWords(_w.split(/\\s+/)) : null;   // v294: the name ends at punctuation\n"
  "      if (r) return Object.assign(r, { phrase: m[0].trim().split(/[.,;!?]/)[0].trim() }); } }")

wf["name"] = "Project Jessie — v294 (typed date ranges)"
out = os.path.join(ROOT, "workflows", "project-jessie-v294.json")
with open(out, "w") as fh:
    json.dump(wf, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
