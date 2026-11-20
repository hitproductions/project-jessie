#!/usr/bin/env node
// main v297 (PENDING 160, before the commercial roll-out 23 Nov): typed requests the Sales & Accounts / Business Development /
// Marketing teams are likely to send, through the real Gate Context, Booked For and Form Offer - "m booth" with no number, "next week"
// / "this week" spans, "a client presentation" not a client, and meetings / events / studios for others as before.
//   node scripts/sim-commercial-typed.js [main v297]
const fs = require('fs');
const MAIN = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/project-jessie-v297.json', 'utf8'));
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const jsOf = n => MAIN.nodes.find(x => x.name === n).parameters.jsCode;
const $f = O => n => ({ first: () => { if (!(n in O)) throw new Error('not run: ' + n); return O[n][0]; }, all: () => O[n] || [] });
const rooms = FX.rooms.concat(['Likha', 'Katha', 'Salin', 'Lobby'].filter(n => !FX.rooms.some(r => r.fields['Room Name'] === n)).map((n, i) => ({ id: 'cr' + i, fields: { 'Room Name': n, 'Room Type': [n === 'Lobby' ? 'Lobby' : 'Conference Room'] } })))
  .concat(['M3', 'M4'].map((n, i) => ({ id: 'mb' + i, fields: { 'Room Name': n, 'Room Type': ['M Booth'] } })));
const types = FX.sessionTypes.concat([{ id: 'ev', fields: { Type: 'Event' } }]);
const STAFF = FX.bookers.map(b => b.fields).concat([{ Name: 'Sales Person', Initials: 'SP', 'Slack User ID': 'U1', Department: ['Sales & Accounts'], Info: 'Account Manager', Authority: ['Standard', 'Client Booking'] },
  { Name: 'Eng Person', Initials: 'EP', 'Slack User ID': 'U2', Department: ['Audio Post'], Info: 'Post Engineer, Goes by Engy.' }]);
async function offer(text) {
  Date.now = () => Date.parse('2026-11-20T06:00:00Z');   // Friday 20 Nov 2026, 2 PM PHT
  const base = { 'Slack Trigger': [{ json: { text, user: 'U1', ts: '1794500000.1', channel: 'D1' } }], 'Get Recent Messages': [{ json: { ts: '1794500000.1', text, user: 'U1' } }],
    'Get Booker': [{ json: { fields: STAFF.find(s => s.Name === 'Sales Person') } }], 'All Bookers': STAFF.map(f => ({ json: { fields: f } })), 'All Rooms': rooms.map(r => ({ json: r })), 'All Session Types': types.map(t => ({ json: t })) };
  base['Gate Context'] = [{ json: new Function('$', '$input', '$getWorkflowStaticData', jsOf('Gate Context'))($f(base), { first: () => ({ json: {} }), all: () => [] }, () => ({}))[0].json }];
  base['Booked For'] = [{ json: new Function('$', '$input', jsOf('Booked For'))($f(base), { first: () => ({ json: {} }) })[0].json }];
  return (await new Function('$', '$input', 'return (async function(){' + jsOf('Form Offer') + '\n})();')($f(base), { first: () => ({ json: { keep: 1 } }), all: () => [{ json: { keep: 1 } }] }))[0].json.formOffer;
}
const has = (p, want) => Object.keys(want).every(k => JSON.stringify(p[k]) === JSON.stringify(want[k]));
(async () => {
  for (const [t, want, no, why] of [
    ['book an m booth for tomorrow', { d: '2026-11-21', p: '__booth' }, [], '"an m booth" -> an M booth (was: no type)'],
    ['book m booth all day tomorrow', { d: '2026-11-21', p: '__booth', ad: 1 }, ['s', 'e'], '"m booth all day" -> All day (was: 12:00 AM - 11:59 PM, no type)'],
    ['book m booth mon to fri next week', { d: '2026-11-23', p: '__booth', rep: { f: 'weekdays', u: '2026-11-29' } }, [], '"mon to fri next week" -> weekdays 23-29 Nov (was: Fri 27 only)'],
    ['I need an M booth every day next week', { d: '2026-11-23', p: '__booth', rep: { f: 'daily', u: '2026-11-29' } }, [], '"every day next week" -> 23-29 Nov (was: open-ended, no type)'],
    ['book likha every day this week 9-10am', { d: '2026-11-20', r: 'Likha', p: 'Meeting', rep: { f: 'daily', u: '2026-11-22' } }, [], '"every day this week" -> from today to Sunday'],
    ['book studio f for a client presentation tomorrow 3-5pm', { d: '2026-11-21', r: 'Studio F', s: '15:00', e: '17:00' }, ['c'], '"a client presentation" -> no client "Presentation"'],
    ['book studio 7 tomorrow 2-4pm, client is Jollibee', { r: 'Studio 7', c: 'Jollibee' }, [], '"client is Jollibee" -> Jollibee, as before'],
    ['book studio 7 tomorrow 2-4pm vo recording for Jollibee, engineer engy', { r: 'Studio 7', p: 'VO Recording', c: 'Jollibee', enN: 'Eng Person' }, [], 'a studio booked for a client with an engineer, as before'],
    ['book studio 7 monday next week 2-4pm', { d: '2026-11-23', r: 'Studio 7' }, ['rep'], '"monday next week" -> one date, not a series, as before'],
    ['book katha tomorrow 2-4pm client meeting with Jollibee', { r: 'Katha', p: 'Meeting' }, ['c'], 'a client meeting in Katha -> Meeting, no client'],
    ['book likha and katha monday 10am to 12nn for the sales meeting', { r: 'Likha', mr: 'Katha', p: 'Meeting' }, [], 'Likha + Katha -> one meeting in both, as before'],
    ['book the lobby for an event on dec 5, whole day', { d: '2026-12-05', r: 'Lobby', p: 'Event', ad: 1 }, [], 'the Lobby, whole day -> an all-day Event, as before'],
    ['book M2 for Trish all day tomorrow', { p: '__booth', ad: 1, fn: 'Trish' }, [], 'an M booth for someone -> For: Trish, as before'],
    ['book salin every tuesday 10-11am for BD huddle until dec 22', { r: 'Salin', p: 'Meeting', rep: { f: 'weekly', days: ['TU'], u: '2026-12-22' } }, [], 'a weekly meeting until 22 Dec, as before']]) {
    const fo = await offer(t), p = (fo && fo.prefill) || {};
    ok(fo && fo.offer && has(p, want) && no.every(k => !(k in p)), JSON.stringify(t) + ': ' + why, p);
  }
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
