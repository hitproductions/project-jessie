#!/usr/bin/env python3
"""Builds workflows/project-jessie-v297.json - Project Jessie — v297 (commercial typed requests), 20 Nov.

Before the commercial roll-out (Sales & Accounts, Business Development, Marketing - 23 Nov), their likely typed requests were run
through Gate Context / Booked For / Form Offer. Three readings were wrong:
- "M booth" typed with no booth number ("book an m booth for tomorrow", "m booth all day tomorrow") gave no booking type, and "all
  day" became 12:00 AM - 11:59 PM. Now "m booth" / "m-booth" (no studio or room named) is an M booth, so "all day" is All day.
- "next week" / "this week" with a day range or "every day" ("m booth mon to fri next week", "every day next week") kept one date or
  made an open-ended series. Now it is that week as a span: Monday to Sunday (this week: from today), the days asked for.
- "for a client presentation" made the client "Presentation". Now "client" after "a" / "an" is not "client <name>", and presentation,
  pitch, visit, briefing, screening, demo, review, shoot, workshop, training, huddle, interview, consultation, dinner, lunch, event
  after "client" are not names.
Built on workflows/project-jessie-v296.json (== live).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "project-jessie-v296.json")))
by = {n["name"]: n for n in wf["nodes"]}


def rep(n, old, new):
    p = by[n]["parameters"]
    assert p["jsCode"].count(old) == 1, (n, old[:70], p["jsCode"].count(old))
    p["jsCode"] = p["jsCode"].replace(old, new)


# Booked For: "a client presentation" is not a client called Presentation
rep("Booked For",
    "  const NOTACLIENT = '(?!\\\\s+(?:work|project|projects|booking|bookings|session|sessions|side|list|record|records|type|name|names|table|brief|call|meeting)\\\\b)';",
    "  const NOTACLIENT = '(?!\\\\s+(?:work|project|projects|booking|bookings|session|sessions|side|list|record|records|type|name|names|table|brief|call|meeting|meetings|presentation|presentations|pitch|pitches|visit|visits|briefing|screening|demo|review|shoot|workshop|training|huddle|interview|consultation|dinner|lunch|event|events)\\\\b)';   // v297: + the kinds of client meeting")
rep("Booked For",
    "    const m = t.match(new RegExp('\\\\b(?:the\\\\s+)?(?:client|produ|producer)' + NOTACLIENT",
    "    const m = t.match(new RegExp('(?<!\\\\ban?\\\\s)\\\\b(?:the\\\\s+)?(?:client|produ|producer)' + NOTACLIENT")   # v297: not after "a" / "an"

# Form Offer: "m booth" with no number is an M booth
rep("Form Offer",
    "    if (P.r && /^M[1-8]$/.test(P.r) && !P.p) P.p = '__booth';",
    "    if (P.r && /^M[1-8]$/.test(P.r) && !P.p) P.p = '__booth';\n"
    "    if (!P.r && !P.p && /\\bm[\\s-]?booths?\\b/i.test(t)) P.p = '__booth';   // v297: \"an m booth\" - no number, still an M booth")
# Form Offer: "next week" / "this week" with a day range or a repeat word is that week
rep("Form Offer",
    "    })(t, g.todayIso);\n",
    "    })(t, g.todayIso) || (function (txt, todayIso) {   // v297: \"next week\" / \"this week\" with days or a repeat word - that week\n"
    "      try {\n"
    "        const w = String(txt).toLowerCase().match(/\\b(next|this|coming)\\s+week\\b/); if (!w) return null;\n"
    "        const days = new Set((String(__dayRanges(String(txt).toLowerCase())).match(/\\b(?:sun|mon|tue|wed|thu|fri|sat)[a-z]*\\b/g) || []).map(x => x.slice(0, 3)));\n"
    "        if (!(days.size >= 2 || /\\b(?:every|daily|each day|weekdays?|everyday)\\b/i.test(txt))) return null;\n"
    "        const T = /^\\d{4}-\\d{2}-\\d{2}$/.test(String(todayIso || '')) ? todayIso : new Date(Date.now() + 8 * 3600000).toISOString().slice(0, 10);\n"
    "        const d0 = new Date(T + 'T12:00:00Z'), dow = (d0.getUTCDay() + 6) % 7;   // Monday 0\n"
    "        const mon = new Date(d0); mon.setUTCDate(d0.getUTCDate() - dow + (w[1] === 'this' ? 0 : 7));\n"
    "        const sun = new Date(mon); sun.setUTCDate(mon.getUTCDate() + 6);\n"
    "        const s = w[1] === 'this' && T > mon.toISOString().slice(0, 10) ? T : mon.toISOString().slice(0, 10);\n"
    "        return { s, e: sun.toISOString().slice(0, 10) };\n"
    "      } catch (er) { return null; }\n"
    "    })(t, g.todayIso);\n")

wf["name"] = "Project Jessie — v297 (commercial typed requests)"
out = os.path.join(ROOT, "workflows", "project-jessie-v297.json")
with open(out, "w") as fh:
    json.dump(wf, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
