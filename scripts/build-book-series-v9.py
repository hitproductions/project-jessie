#!/usr/bin/env python3
"""Builds workflows/book-series-v9.json - Jessie — Book Series — v9 (series review), 4 Nov.

PENDING 150 (series by design, Howard's "C"). Prepare mode ran every date through Book Session (its own calendar read, Airtable
checks, ~3 s a date) - at six months that is minutes. v9's prepare mode:
- one Room Availability call for every date (Span Check, Room Availability v26: one read for the span, each date's answer, the
  booking's rooms' busy times over each whole day);
- Book Session's prepare checks ONCE, on the first date where the booking's rooms are free (First Date) - the title, client,
  people, booking type and department are the same on every date;
- each other date from the span answer: free -> booked as asked; a room taken -> another suitable room free then (the booking
  type's usual rooms for a studio, a free vocal booth for a booth, a free meeting room for a meeting room, another M booth) -
  "Studio 2 instead of Studio 1"; nothing suitable -> a choice for the requester: the nearest free time that day for the same
  rooms (earlier / later) or skip; nothing free that day at all (or all day) -> left out;
- returns `review` (every date and what happens to it) for Slack Interactions v66's review screen, the stored series as before
  (inputs.choices holds each choice's options, so a picked option is checked against what was offered), and card_text.
The cap: six months from the first date (was 16 dates), at most 200 dates. Book mode is unchanged.
Built on workflows/imported/book-series-v8-imported.json (the live download).
"""
import copy
import json
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
wf = json.load(open(os.path.join(ROOT, "workflows", "imported", "book-series-v8-imported.json")))
by = {n["name"]: n for n in wf["nodes"]}
RA_ID = "e7tBQB458nstrqei"


def sub(js, a, b, n=1):
    assert js.count(a) == n, (js.count(a), a[:140])
    return js.replace(a, b)


# ---- Expand Dates: six months, not 16 dates
p = by["Expand Dates"]["parameters"]
p["jsCode"] = sub(p["jsCode"],
    "if (res.count > 16) {\n  return [{ json: { _go:false, status:'TOO_MANY', count:res.count,\n"
    "    human: 'That series is ' + res.count + ' sessions. I can book up to 16 at a time for now - book the first 16, a shorter run, or set the full series up in Google Calendar directly.' } }];\n}",
    "// v9 (PENDING 150, decided 4 Nov): up to six months from the first date (was 16 dates); never more than 200 dates\n"
    "{ const _ds = res.occurrences.map(o => o.all_day ? o.date : String(o.start_iso).slice(0, 10)).sort();\n"
    "  const _lim = new Date(_ds[0] + 'T00:00:00Z'); _lim.setUTCMonth(_lim.getUTCMonth() + 6);\n"
    "  if (_ds[_ds.length - 1] > _lim.toISOString().slice(0, 10) || res.count > 200)\n"
    "    return [{ json: { _go:false, status:'TOO_LONG', count:res.count,\n"
    "      human: 'That series runs past six months from its first date - the most is six months. Book a shorter run.' } }]; }")

# ---- new nodes: Prepare? -> Span Input -> Span Check (Room Availability) -> First Date -> Create Each
go = by["Go?"]
x0, y0 = by["Create Each"]["position"]
prep_if = copy.deepcopy(go)
prep_if.update({"id": str(uuid.uuid4()), "name": "Prepare?", "position": [x0 - 220, y0 - 260]})
prep_if["parameters"]["conditions"]["conditions"] = [{"id": "prep", "leftValue": "={{ String($json.mode || '').toLowerCase() === 'prepare' }}",
    "rightValue": "", "operator": {"type": "boolean", "operation": "true", "singleValue": True}}]

SPAN_INPUT = r"""// Span Input (v9, PENDING 150): one Room Availability call for every date of the series being prepared - the dates, the time,
// the booking's rooms (watched over each whole day, for the nearest free time), the same reference data Book Session gets.
const occ = $input.all().map(i => i.json || {});
const R = $('When Executed by Another Workflow').first().json || {};
const ds = occ.map(o => o._date).filter(Boolean);
const hm = iso => (String(iso || '').match(/T(\d{2}:\d{2})/) || [])[1] || '';
const allDay = !!(occ[0] || {}).all_day;
const t0 = allDay ? '00:00' : hm((occ[0] || {}).start_iso), t1 = allDay ? '23:59' : hm((occ[0] || {}).end_iso);
return [{ json: { dates: ds.join(','), t0, t1, start_iso: ds[0] + 'T' + t0 + ':00+08:00', end_iso: ds[ds.length - 1] + 'T' + t1 + ':00+08:00',
  session_type: String(R.session_type || ''), room: '', scope: '', hours: '', reference_data: String(R.reference_data || ''), watch: String(R.rooms || '') } }];
"""
FIRST_DATE = r"""// First Date (v9, PENDING 150): Book Session's prepare checks run once - on the first date where every room of the booking is free
// (the details are the same on every date); with none free, the first date (Book Session then finds it another room or time).
const occ = $('Expand Dates').all().map(i => i.json || {}).filter(o => o._go);
const sp = $('Span Check').first().json || {};
const B = String(($('When Executed by Another Workflow').first().json || {}).rooms || '').split(',').map(s => s.trim()).filter(Boolean);
const day = {}; for (const x of [].concat(sp.per_date || [])) if (x && x.date) day[x.date] = x;
const freeOn = d => { const D = day[d]; if (!D || D.status !== 'OK') return false;
  const busy = new Set([].concat(D.busy || []).map(b => String(b).replace(/\s*\(.*$/, '').trim())); return B.every(r => !busy.has(r)); };
const pick = occ.find(o => freeOn(o._date)) || occ[0];
return pick ? [{ json: pick }] : [];
"""
span_input = {"parameters": {"jsCode": SPAN_INPUT}, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [x0, y0 - 260],
              "id": str(uuid.uuid4()), "name": "Span Input"}
span_check = {"parameters": {"workflowId": {"__rl": True, "mode": "list", "value": RA_ID, "cachedResultName": "Jessie — Room Availability"},
              "mode": "each", "options": {}}, "type": "n8n-nodes-base.executeWorkflow", "typeVersion": 1.2, "position": [x0 + 220, y0 - 260],
              "id": str(uuid.uuid4()), "name": "Span Check", "onError": "continueRegularOutput", "alwaysOutputData": True}
first_date = {"parameters": {"jsCode": FIRST_DATE}, "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [x0 + 440, y0 - 260],
              "id": str(uuid.uuid4()), "name": "First Date"}
code_tv = by["Aggregate"].get("typeVersion", 2)
span_input["typeVersion"] = first_date["typeVersion"] = code_tv
wf["nodes"] += [prep_if, span_input, span_check, first_date]
C = wf["connections"]
assert C["Go?"]["main"][0] == [{"node": "Create Each", "type": "main", "index": 0}], C["Go?"]
C["Go?"]["main"][0] = [{"node": "Prepare?", "type": "main", "index": 0}]
C["Prepare?"] = {"main": [[{"node": "Span Input", "type": "main", "index": 0}], [{"node": "Create Each", "type": "main", "index": 0}]]}
C["Span Input"] = {"main": [[{"node": "Span Check", "type": "main", "index": 0}]]}
C["Span Check"] = {"main": [[{"node": "First Date", "type": "main", "index": 0}]]}
C["First Date"] = {"main": [[{"node": "Create Each", "type": "main", "index": 0}]]}

# ---- Aggregate: prepare mode from the span answer + one Book Session check
PREP = r"""if (String(REQ0.mode || '').trim().toLowerCase() === 'prepare') {
  // v9 (PENDING 150): Book Session's checks once (First Date), every date from one read (Span Check) - see Span Input / First Date.
  const MONP = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  const DAYP = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const long = d => { const x = new Date(d + 'T00:00:00Z'); return DAYP[x.getUTCDay()] + ', ' + x.getUTCDate() + ' ' + MONP[x.getUTCMonth()] + ' ' + x.getUTCFullYear(); };
  const tl = iso => new Date(iso).toLocaleTimeString('en-US', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' });
  const hm = iso => { const m = String(iso || '').match(/T(\d{2}:\d{2})/); return m ? m[1] : ''; };
  const t12 = m => { let h = Math.floor(m / 60) % 24; const mm = m % 60, ap = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12; return h + ':' + String(mm).padStart(2, '0') + ' ' + ap; };
  const mHM = m => String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0');
  const all = $('Expand Dates').all().map(i => i.json || {}).filter(o => o._go);
  const FD = $('First Date').first().json || {};
  const r = results[0] || {};
  let P = null; try { P = r.prep_payload ? JSON.parse(r.prep_payload) : null; } catch (e) {}
  if (!(r.status === 'PREPARED' && P && P.F) || r.needs_consent)
    return [{ json: { status: 'REJECTED', reason: r.needs_consent ? 'ROOM_OCCUPIED' : (r.reason || 'FAILED'), human: r.human || 'Nothing was prepared.' } }];   // a question, as Book Session wrote it
  const SP = $('Span Check').first().json || {};
  const day = {}; for (const x of [].concat(SP.per_date || [])) if (x && x.date) day[x.date] = x;
  if (SP.status !== 'OK' || all.some(o => o._date !== FD._date && !day[o._date]))
    return [{ json: { status: 'REJECTED', reason: 'CALENDAR_ERROR', human: 'The calendar could not be read for those dates, so nothing was prepared. Try again in a moment.' } }];
  const F = Object.assign({}, P.F);
  const allDay = !!(all[0] || {}).all_day;
  if (r.swap) { F['Room'] = r.swap.from_rooms; if (!allDay) F['Time'] = tl(r.swap.from_start) + ' – ' + tl(r.swap.from_end); }
  const B = String(REQ0.rooms || '').split(',').map(s => s.trim()).filter(Boolean);
  let REF = {}; try { REF = JSON.parse(String(REQ0.reference_data || '') || '{}'); } catch (e) {}
  const info = {}; for (const x of [].concat(REF.rooms || [])) info[String(x.name || '').trim()] = x;
  const st = String(REQ0.session_type || '').trim(), post = /^post processing$/i.test(st);
  const only = /atmos/i.test(st) || /^van recording$/i.test(st);
  const kindOf = n => /^M\d$/.test(n) ? 'mbooth' : (info[n] || {}).common ? 'common' : ((info[n] || {}).vocalBooth && !(n === 'Studio E' && post)) ? 'vbooth' : 'studio';
  const t0m = (h => h ? +h.slice(0, 2) * 60 + +h.slice(3) : 0)(hm((all[0] || {}).start_iso)), t1m = (h => h ? +h.slice(0, 2) * 60 + +h.slice(3) : 0)(hm((all[0] || {}).end_iso));
  const dur = t1m - t0m;
  const items = [], perDate = {}, choices = {}, ok = [], leftOut = [];
  for (const o of all) {
    const d = o._date;
    if (d === FD._date) {   // Book Session's own answer for this date
      if (r.swap) { const rm = String(r.final_rooms || P.F['Room'] || ''), s0 = r.final_start || '', e0 = r.final_end || '';
        perDate[d] = { rooms: rm, start: hm(s0), end: hm(e0) };
        const what = [rm !== String(F['Room']) ? rm + ' instead of ' + F['Room'] : '', s0 && (tl(s0) + ' – ' + tl(e0)) !== F['Time'] ? tl(s0) + ' – ' + tl(e0) : ''].filter(Boolean).join(', ');
        items.push({ d, kind: 'moved', note: what || 'moved' }); }
      else items.push({ d, kind: 'ok' });
      ok.push(d); continue;
    }
    const D = day[d];
    const busy = new Set([].concat(D.busy || []).map(b => String(b).replace(/\s*\(.*$/, '').trim()));
    const taken = B.filter(x => busy.has(x));
    if (!taken.length) { items.push({ d, kind: 'ok' }); ok.push(d); continue; }
    // another suitable room free then, for each room taken
    const rep = {}, used = new Set(B);
    let fixed = !only;
    for (const t of taken) {
      if (!fixed) break;
      const k = kindOf(t);
      const pool = k === 'vbooth' ? [].concat((D.vocal_booths || {}).free || [])
        : k === 'studio' ? [].concat(D.free_priority || []).filter(x => kindOf(x) === 'studio')
        : k === 'common' ? [].concat(D.free_priority || [], D.free_rooms || []).filter(x => kindOf(x) === 'common')
        : [].concat(D.free_rooms || []).filter(x => /^M\d$/.test(x));
      const c = pool.find(x => !used.has(x) && !busy.has(x) && !(x === 'Studio M' && !/^van recording$/i.test(st)) && !(x === 'Studio E' && !post && k === 'studio'));
      if (c) { rep[t] = c; used.add(c); } else fixed = false;
    }
    if (fixed) {
      const rooms = B.map(x => rep[x] || x).join(', ');
      perDate[d] = { rooms, start: '', end: '' };
      items.push({ d, kind: 'moved', note: taken.map(t => rep[t] + ' instead of ' + t).join(', ') });
      ok.push(d); continue;
    }
    // no suitable room: the nearest free time that day for the same rooms - one earlier, one later
    const ivs = [].concat(...B.map(x => (D.day_busy || {})[x] || []));
    const opts = [];
    if (!allDay && dur > 0 && D.day_busy) {
      const freeAt = s => ivs.every(([a, b]) => s + dur <= a || s >= b);
      let before = null, after = null;
      for (let s = 360; s + dur <= 1440; s += 30) { if (s === t0m || !freeAt(s)) continue; if (s < t0m) before = s; else if (after === null) after = s; }
      if (before !== null) opts.push({ v: 'a', start: mHM(before), end: mHM(before + dur), rooms: B.join(', '), label: t12(before) + ' – ' + t12(before + dur) + ' (earlier)' });
      if (after !== null) opts.push({ v: 'b', start: mHM(after), end: mHM(after + dur), rooms: B.join(', '), label: t12(after) + ' – ' + t12(after + dur) + ' (later)' });
    }
    const why = taken.join(' and ') + (taken.length > 1 ? ' are' : ' is') + ' taken' + (allDay ? '' : ' then');
    if (opts.length) { choices[d] = opts.concat([{ v: 'skip', label: 'Skip – find another time later' }]); items.push({ d, kind: 'choose', note: why, options: choices[d].map(x => ({ v: x.v, label: x.label })) }); }
    else { leftOut.push(d); items.push({ d, kind: 'none', note: why + ', and nothing else that day' }); }
  }
  if (!ok.length && !Object.keys(choices).length) return [{ json: { status: 'REJECTED', reason: 'ROOM_OCCUPIED',
    human: 'Nothing was prepared - the room is taken on every one of those dates (' + leftOut.map(long).join('; ') + '). Ask exactly this, in one message: "❌ *' + (String(REQ0.rooms || '').trim() || 'The room') + ' is already booked on all of those dates.*\n\nAnother room or time?"' } }];
  const shown = items.filter(x => x.kind === 'ok' || x.kind === 'moved').map(x => long(x.d) + (x.kind === 'moved' ? ' · ' + x.note : ''));
  // notes from the first date's card ("Not a usual ... room", "Want a holding room?") - never a date-specific one
  const _notes = String(r.summary_text || '').split('\n\n').slice(1, -1).join('\n').split('\n').map(s => s.trim())
    .filter(s => s && !/already passed|^(?:❌ )?Heads up: \*?\S.*\bbooked\b|picked|No time given/i.test(s));
  const L = ['*' + F['Title'] + '*', '*Dates (' + ok.length + '):*'].concat(shown.map(s => '- ' + s), ['*Time:* ' + F['Time'], '*Room:* ' + F['Room']]);
  const _for = (String(F['Booked by'] || '').match(/\(for\s+([^)]+)\)/i) || [])[1]; if (_for) L.push('*For:* ' + _for.trim());
  const notes = _notes.slice();
  const _ch = items.filter(x => x.kind === 'choose'), _none = items.filter(x => x.kind === 'none');
  if (_ch.length) notes.unshift('Needs a choice: ' + _ch.map(x => long(x.d) + ' (' + x.note + ')').join('; ') + '.');
  if (_none.length) notes.unshift('❌ Left out - nothing free: ' + _none.map(x => long(x.d)).join(', ') + '.');
  const card = L.join('\n') + (notes.length ? '\n\n' + notes.join('\n') : '') + '\n\nConfirm to book.';
  const ref = String(P.ref || ((String(REQ0.description || '').match(/\bref:\s*([A-Z0-9]+)/) || [])[1]) || '').trim();
  const desc = (F['Engineer'] ? ['Engineer: ' + F['Engineer']] : []).concat(F['Arranger'] ? ['Arranger: ' + F['Arranger']] : [])
    .concat(String(REQ0.description || '').split('|').map(s => s.trim()).filter(s => s && !/^(engineer|arranger)\s*:/i.test(s))).join(' | ');
  const inputs = { summary: F['Title'], rooms: F['Room'], session_type: F['Session Type'] || '', client: /^none$/i.test(F['Client'] || '') ? '' : (F['Client'] || ''),
    engineer: F['Engineer'] || '', description: desc, bookingType: F['Booking Type'] || '', department: F['Department'] || '',
    room_override: F['Override'] === 'yes', all_day: allDay,
    time_start: String(REQ0.time_start || ''), time_end: String(REQ0.time_end || ''), dates: ok.join(','),
    requester_text: String(REQ0.requester_text || ''), per_date: JSON.stringify(perDate),
    choices: JSON.stringify(choices), left_out: leftOut.join(',') };   // v9: what the review offers / leaves out
  const key = ref ? seriesKey(ref, { Title: F['Title'], Dates: shown.concat(_ch.map(x => long(x.d) + ' · ?')), Time: F['Time'], Room: F['Room'] }) : '';
  return [{ json: { status: 'PREPARED', card_text: card, title: F['Title'], dates: ok, skipped: leftOut, prep_key: key,
    review: { title: F['Title'], time: allDay ? 'All day' : F['Time'], room: F['Room'], items },
    prep_payload: JSON.stringify({ v: 1, kind: 'series', ref, code: seriesCode(inputs), inputs, card: { Title: F['Title'], Dates: shown, Time: F['Time'], Room: F['Room'] }, at: new Date().toISOString() }),
    human: 'The series card is ready and is sent to the requester automatically, exactly as prepared. Do not write anything about this booking yourself. Their yes books it - do not call Book Series.' } }];
}
"""
p = by["Aggregate"]["parameters"]
js = p["jsCode"]
a = js.index("if (String(REQ0.mode || '').trim().toLowerCase() === 'prepare') {")
b = js.index("const DOW = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];")
js = js[:a] + PREP + js[b:]
# book mode zips Expand Dates with the results - unchanged (Prepare? sends book items straight to Create Each)
p["jsCode"] = js

wf["name"] = "Jessie — Book Series — v9 (series review)"
out = os.path.join(ROOT, "workflows", "book-series-v9.json")
with open(out, "w") as f:
    json.dump(wf, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("wrote", os.path.relpath(out, ROOT), len(wf["nodes"]), "nodes")
