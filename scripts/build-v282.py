#!/usr/bin/env python3
"""Builds workflows/project-jessie-v282.json - main "Project Jessie", v282 (my bookings over a date span), 26 Oct.

Howard (26 Oct, Slack 3:18 PM): "what are my bookings nov 1-4" answered "Your bookings · Mon, Nov 1 - Nothing booked for you
then." - only Nov 1. Gate Context reads week and month phrases as ranges, but a written span ("nov 1-4") gives only its first
date, and Mine Check took that one date as the window. Mine Check now reads the span itself: "nov 1-4", "nov 1 to 4",
"november 1 - nov 4", "nov 1st to 4th", "oct 30 - nov 2", "1-4 nov" -> the window runs from the first day to the last
(at most 62 days). "nov 1 2-4pm" is a date and a time, not a span. Nothing else changes (Gate Context untouched).
Built on workflows/imported/project-jessie-v281-imported.json (the live download).
"""
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "workflows", "imported", "project-jessie-v281-imported.json")
OUT = os.path.join(ROOT, "workflows", "project-jessie-v282.json")
wf = json.load(open(SRC))
by = {n["name"]: n for n in wf["nodes"]}


def sub(node, a, b):
    js = by[node]["parameters"]["jsCode"]
    assert js.count(a) == 1, (node, js.count(a), a[:80])
    by[node]["parameters"]["jsCode"] = js.replace(a, b)


sub("Mine Check", "    let start = today, end = add(today, 7), week = true;\n    if (/\\bnext week\\b/.test(t)) {",
    "    let start = today, end = add(today, 7), week = true;\n"
    "    // v282 (26 Oct, \"what are my bookings nov 1-4\" listed Nov 1 only): a written span - \"nov 1-4\", \"nov 1 to 4\", \"oct 30 - nov 2\",\n"
    "    // \"1-4 nov\" - is the window, first day to last (Gate Context passes only its first date)\n"
    "    const _M = '(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\\\\.?', _D = '(\\\\d{1,2})(?:st|nd|rd|th)?', _TO = '\\\\s*(?:-|\\u2013|\\u2014|to|thru|through|until|till)\\\\s*';\n"
    "    const _s1 = t.match(new RegExp('\\\\b' + _M + '\\\\s+' + _D + _TO + '(?:' + _M + '\\\\s+)?' + _D + '\\\\b(?!\\\\s*(?::|am\\\\b|pm\\\\b|nn\\\\b))'));\n"
    "    const _s2 = !_s1 && t.match(new RegExp('\\\\b' + _D + _TO + _D + '\\\\s+(?:of\\\\s+)?' + _M + '\\\\b'));\n"
    "    let _span = null;\n"
    "    if (_s1 || _s2) {\n"
    "      const MI = x => ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'].indexOf(String(x).slice(0, 3));\n"
    "      const m1 = _s1 ? MI(_s1[1]) : MI(_s2[3]), d1 = +(_s1 ? _s1[2] : _s2[1]), m2 = _s1 ? (_s1[3] ? MI(_s1[3]) : m1) : m1, d2 = +(_s1 ? _s1[4] : _s2[2]);\n"
    "      const y0 = +today.slice(0, 4), mo0 = +today.slice(5, 7) - 1, y1 = m1 < mo0 ? y0 + 1 : y0, y2 = m2 < m1 ? y1 + 1 : y1;\n"
    "      const iso = (y, m, d) => { const x = new Date(Date.UTC(y, m, d)); return x.getUTCMonth() === m && x.getUTCDate() === d ? x.toISOString().slice(0, 10) : ''; };\n"
    "      const a = iso(y1, m1, d1), b = iso(y2, m2, d2);\n"
    "      if (a && b && b >= a && (Date.parse(b) - Date.parse(a)) / 86400000 <= 62) _span = [a, add(b, 1)];\n"
    "    }\n"
    "    if (_span) { start = _span[0]; end = _span[1]; week = false; }\n"
    "    else if (/\\bnext week\\b/.test(t)) {")
wf["name"] = "Project Jessie — v282 (my bookings over a date span)"
with open(OUT, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(OUT, ROOT))
