#!/usr/bin/env node
// Slack Interactions v52 (Howard, 28 Oct): Atmos Mixing (Studio C) / Van Recording (Studio M) have one room - when it is taken,
// step 2 lists that room's bookings that day under the notice, so the next time picked is not a guess.
// Usage: node scripts/sim-one-room-day.js [slack-interactions v52]
const fs = require('fs');
const SI = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v52.json', 'utf8'));
if (!/RADAY/.test(JSON.stringify(SI.nodes))) { console.log('0 ok, 0 failed (an older build: v52 not in it)'); process.exit(0); }
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const node = n => SI.nodes.find(x => x.name === n);
const run = async (name, input, outs) => {
  const $ = n => { if (outs[n] === undefined) { const e = () => { throw new Error(n + ' not executed'); }; return { first: e, all: e }; }
    return { first: () => (outs[n] || [])[0], all: () => outs[n] || [] }; };
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + node(name).parameters.jsCode + '\n}).call(this);').call({ helpers: {} }, $, $input); };
const bookers = [{ id: 'b1', fields: { Name: 'Howard Luistro', 'Slack User ID': 'U1', Info: 'Post Engineer', Department: ['Audio Post'], Initials: 'HL' } }];
const ST = (t, pri, roles) => ({ id: 'st-' + t, fields: { Type: t, Priority: pri, 'Last Resort': [], 'Engineer Role Required': roles } });
const sessionTypes = [ST('Atmos Mixing', ['rc'], ['Loc Engineer', 'Post Engineer', 'Music Engineer']), ST('Van Recording', ['rm'], ['Post Engineer']), ST('VO Recording', ['r7'], ['Post Engineer'])];
const rooms = [['rc', 'Studio C'], ['rm', 'Studio M'], ['r7', 'Studio 7']].map(([id, n]) => ({ id, fields: { 'Room Name': n, 'Room Type': ['Recording Control Room'] } }));
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];
const S = (purpose, kind, o) => Object.assign({ date: '2027-10-28', t0: '16:00', t1: '20:00', purpose, kind, requester: 'U1', channel: 'D1', ext: 'x' }, o || {});
const toRA = async s => (await run('To Room Availability', [], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cache })).map(i => i.json);
const step2 = async (s, ras) => (await run('Build Step 2', ras.map(j => ({ json: j })), { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cache, 'Loc Projects 2': [] }))[0].json.view;
const txt = v => v.blocks.map(b => (b.text && b.text.text) || (b.elements || []).map(e => e.text || '').join(' ') || '').join('\n');

(async () => {
  console.log('To Room Availability');
  let it = await toRA(S('Atmos Mixing', 'atmos'));
  ok(it.length === 2 && it[0].start_iso === '2027-10-28T16:00:00+08:00' && it[1].start_iso === '2027-10-28T00:00:00+08:00' && it[1].end_iso === '2027-10-28T23:59:00+08:00',
     'Atmos: the asked window, then the whole day', it.map(x => x.start_iso + '..' + x.end_iso));
  ok((await toRA(S('Van Recording', 'studio'))).length === 2, 'Van Recording (Studio M) too');
  ok((await toRA(S('VO Recording', 'studio'))).length === 1, 'other types: one call, as before');
  ok((await toRA(S('Atmos Mixing', 'atmos', { allDay: true }))).length === 1, 'all day: one call (the window is the day)');
  ok((await toRA(S('Atmos Mixing', 'atmos', { series: { dates: ['2027-10-28', '2027-11-04'] } }))).length === 2, 'a series: one call per date, no day call');

  console.log('Build Step 2');
  const win = (free) => ({ status: 'OK', window: { start: 'a', end: 'b' }, free_priority: free ? ['Studio C'] : [], free_last_resort: [], free_rooms: free ? ['Studio C'] : [], busy: free ? [] : ['Studio C (x)'], busy_detail: [] });
  const E = (title, s, e, o) => Object.assign({ id: title, title, start: '2027-10-28T' + s + ':00+08:00', end: '2027-10-28T' + e + ':00+08:00', stype: 'Atmos Mixing', ref: 'U2', recurring: false, allDay: false }, o || {});
  const day = { status: 'OK', busy_detail: [{ room: 'Studio C', events: [E('KUBA / DR', '17:00', '21:00'), E('NET-BONJOUR6 / JT', '09:00', '13:00')] }, { room: 'Studio 7', events: [E('OTHER', '10:00', '11:00')] }] };
  let v = await step2(S('Atmos Mixing', 'atmos'), [win(false), day]);
  let t = txt(v);
  ok(/Studio C is taken then - pick another date or time\./.test(t) && /\*Studio C bookings that day:\*/.test(t), 'taken -> the notice, then "Studio C bookings that day:"', t);
  ok(/\*NET-BONJOUR6 \/ JT\*\n\*Time:\* 9:00 AM – 1:00 PM[\s\S]*\*KUBA \/ DR\*\n\*Time:\* 5:00 PM – 9:00 PM/.test(t) && !/OTHER/.test(t), 'each booking as title + Time, earliest first; other rooms left out', t);
  ok(!v.blocks.some(b => b.block_id === 'room' || b.block_id === 'project'), 'still no room to pick - Back to step 1, as before');
  v = await step2(S('Atmos Mixing', 'atmos'), [win(true), day]);
  t = txt(v);
  ok(!/bookings that day/.test(t) && JSON.stringify(v).includes('Studio C') && v.blocks.some(b => b.block_id === 'project'), 'free -> Studio C offered, the form as usual, no list');
  v = await step2(S('Atmos Mixing', 'atmos'), [win(false)]);
  ok(/Studio C is taken then/.test(txt(v)) && !/bookings that day/.test(txt(v)), 'no day answer (an old run) -> the notice alone, as before');
  v = await step2(S('Atmos Mixing', 'atmos'), [win(false), { status: 'CALENDAR_ERROR' }]);
  ok(/Studio C is taken then/.test(txt(v)) && !/bookings that day/.test(txt(v)), 'the day read failed -> the notice alone');
  v = await step2(S('Atmos Mixing', 'atmos'), [win(false), { status: 'OK', busy_detail: [{ room: 'Studio C', events: [E('HOLD', '00:00', '00:00', { allDay: true })] }] }]);
  ok(/\*HOLD\*\n\*Time:\* All day/.test(txt(v)), 'an all-day booking -> "All day"');
  v = await step2(S('VO Recording', 'studio', { requester: 'U1' }), [{ status: 'OK', free_priority: ['Studio 7'], free_last_resort: [], busy: [], busy_detail: [] }]);
  ok(!/bookings that day/.test(txt(v)), 'other types unchanged');
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('FAIL crashed: ' + e.stack); process.exit(1); });
