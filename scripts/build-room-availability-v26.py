#!/usr/bin/env python3
"""Builds workflows/room-availability-v26.json - Jessie — Room Availability — v26 (a series in one read), 4 Nov.

PENDING 150 (series by design). A series was checked one date at a time - Slack Interactions called Room Availability once per
date (~3 s each), which is why the cap was 16 dates. v26 answers every date in one call:
- called with `dates` (comma list, two or more), `t0` / `t1` (HH:MM) and start_iso / end_iso spanning the first to the last date,
  it reads KDC Bookings and the rooms' free/busy ONCE for the whole span, then runs the same per-window code for each date on that
  date's events only, and returns { status, span: true, per_date: [ <the usual answer + date>, … ] } (human / reply_text left out);
- `watch` (comma list of rooms): each date also carries day_busy { room: [[startMin, endMin], …] } for those rooms over the whole
  day (KDC bookings + the rooms' own calendars) - what the series review needs to offer the nearest free time that day;
- Get Events In Window reads up to 2500 events a page and follows nextPageToken (a six-month span is several thousand events);
  a read that still has a next page after 20 pages is CALENDAR_ERROR, as before for any unfinished read;
- one window (no `dates`): exactly the old answer.
Built on workflows/imported/room-availability-v25-imported.json (the live download).
"""
import copy
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "room-availability-v25-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}


def sub(js, a, b, n=1):
    assert js.count(a) == n, (js.count(a), a[:140])
    return js.replace(a, b)


# ---- the trigger takes the new inputs
trig = by["When Executed by Another Workflow"]["parameters"]["workflowInputs"]["values"]
for name in ("dates", "t0", "t1", "watch"):
    if not any(v["name"] == name for v in trig):
        trig.append({"name": name})

# ---- Get Events In Window: 2500 a page, every page
ge = by["Get Events In Window"]["parameters"]
for q in ge["queryParameters"]["parameters"]:
    if q["name"] == "maxResults":
        q["value"] = "2500"
ge.setdefault("options", {})["pagination"] = {"pagination": {
    "completeExpression": "={{ !$response.body.nextPageToken }}", "limitPagesFetched": True, "maxRequests": 20,
    "paginationCompleteWhen": "other",
    "parameters": {"parameters": [{"name": "pageToken", "value": "={{ $response.body.nextPageToken }}"}]}}}

# ---- Compute Availability: the old code becomes one window's answer; a series runs it per date on one read
ca = by["Compute Availability"]["parameters"]
body = ca["jsCode"]
i = body.index("const ROOMS = {"); j = body.index("};", i) + 2
rooms_literal = body[i:j].replace("const ROOMS = {", "const __ROOMS = {", 1)
body = sub(body, "$('When Executed by Another Workflow').first().json", "__REQIN")
body = sub(body, "$input.all()", "__INALL", n=2)
body = sub(body, "$('Room Free Busy').first()", "__FBF")
# pages: the read is finished when the LAST page has no nextPageToken (every earlier page has one)
body = sub(body, "  if (!_read || _in.some(j => j.error || j.nextPageToken)) {",
    "  if (!_read || _in.some(j => j.error) || (_in.length && _in[_in.length - 1].nextPageToken)) {   // v26: pages - only the last has none")

WRAP_HEAD = r"""// v26 (PENDING 150, 4 Nov): a series in one call. The code below (to the end of __one) is the one-window answer, unchanged;
// called with `dates`, the events and the rooms' free/busy are read once for the whole span and each date gets that answer
// from its own day's events. The literal node names stay here so n8n hands their data to this node.
const __TRIG = $('When Executed by Another Workflow').first().json || {};
const __IN0 = $input.all();
let __FB0 = null; try { __FB0 = $('Room Free Busy').first(); } catch (e) { __FB0 = null; }
function __one(__REQIN, __INALL, __FBF) {
"""
WRAP_TAIL = r"""
}
""" + rooms_literal + r"""
const __DATES = String(__TRIG.dates || '').split(',').map(s => s.trim()).filter(s => /^\d{4}-\d{2}-\d{2}$/.test(s));
if (__DATES.length < 2) return __one(__TRIG, __IN0, __FB0);
const __pages = __IN0.map(it => (it && it.json) || {});
if (!__pages.some(j => Array.isArray(j.items)) || __pages.some(j => j.error) || (__pages.length && __pages[__pages.length - 1].nextPageToken))
  return [{ json: { status: 'CALENDAR_ERROR', span: true, per_date: [], human: 'The calendar could not be read for those dates, so nothing can be confirmed as free or busy.' } }];
const __all = [], __seen = {};
for (const j of __pages) for (const ev of (j.items || [])) if (ev && ev.id && !__seen[ev.id]) { __seen[ev.id] = 1; __all.push(ev); }
const __ms = v => { const s = String(v || ''); return /^\d{4}-\d{2}-\d{2}$/.test(s) ? Date.parse(s + 'T00:00:00+08:00') : new Date(s).getTime(); };
const __hm = v => /^\d{1,2}:\d{2}$/.test(String(v || '')) ? String(v).padStart(5, '0') : '';
const __t0 = __hm(__TRIG.t0) || (String(__TRIG.start_iso || '').match(/T(\d{2}:\d{2})/) || [])[1] || '00:00';
const __t1 = __hm(__TRIG.t1) || (String(__TRIG.end_iso || '').match(/T(\d{2}:\d{2})/) || [])[1] || '23:59';
const __fbj = (__FB0 && __FB0.json) || {}, __cals = __fbj.calendars || {};
const __watch = String(__TRIG.watch || '').split(',').map(s => s.trim()).filter(n => __ROOMS[n]);
const __evRoom = (ev, k) => { const lk = k.toLowerCase(), em = String(__ROOMS[k]).toLowerCase();
  return (ev.attendees || []).some(a => String(a.email || '').toLowerCase() === em) || String(ev.location || '').toLowerCase().indexOf(lk) !== -1
    || String(ev.summary || '').split(' - ')[0].trim().toLowerCase() === lk; };
const __per = [];
for (const d of __DATES) {
  const ds = Date.parse(d + 'T00:00:00+08:00'), de = ds + 86400000;
  const dayEv = __all.filter(ev => ev.status !== 'cancelled' && __ms((ev.start || {}).dateTime || (ev.start || {}).date) < de && __ms((ev.end || {}).dateTime || (ev.end || {}).date) > ds);
  const cals = {};
  for (const id of Object.keys(__cals)) { const c = __cals[id] || {};
    cals[id] = Object.assign({}, c, Array.isArray(c.busy) ? { busy: c.busy.filter(b => Date.parse(b.start) < de && Date.parse(b.end) > ds) } : {}); }
  const R = Object.assign({}, __TRIG, { dates: '', start_iso: d + 'T' + __t0 + ':00+08:00', end_iso: d + 'T' + __t1 + ':00+08:00' });
  let r;
  try { r = Object.assign({}, ((__one(R, [{ json: { items: dayEv } }], { json: Object.assign({}, __fbj, { calendars: cals }) }) || [])[0] || {}).json || {}); }
  catch (e) { r = { status: 'ERROR', error: String((e && e.message) || e) }; }
  delete r.human; delete r.reply_text;
  r.date = d;
  if (__watch.length) {
    const db = {};
    for (const k of __watch) {
      const iv = [];
      for (const ev of dayEv) if (__evRoom(ev, k)) iv.push([__ms((ev.start || {}).dateTime || (ev.start || {}).date), __ms((ev.end || {}).dateTime || (ev.end || {}).date)]);
      const c = cals[__ROOMS[k]]; if (c && Array.isArray(c.busy) && !(c.errors && c.errors.length)) for (const b of c.busy) iv.push([Date.parse(b.start), Date.parse(b.end)]);
      const m = iv.map(([s, e]) => [Math.max(0, Math.round((s - ds) / 60000)), Math.min(1440, Math.round((e - ds) / 60000))]).filter(([s, e]) => e > s).sort((a, b) => a[0] - b[0]);
      db[k] = m.reduce((acc, x) => { const l = acc[acc.length - 1]; if (l && x[0] <= l[1]) l[1] = Math.max(l[1], x[1]); else acc.push(x.slice()); return acc; }, []);   // overlaps merged
    }
    r.day_busy = db;
  }
  __per.push(r);
}
const __bad = __per.find(x => x.status !== 'OK');
return [{ json: { status: __bad ? __bad.status : 'OK', span: true, per_date: __per } }];
"""
ca["jsCode"] = WRAP_HEAD + body + WRAP_TAIL

wf["name"] = "Jessie — Room Availability — v26 (a series in one read)"
out = os.path.join(ROOT, "workflows", "room-availability-v26.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
