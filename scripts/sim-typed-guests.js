#!/usr/bin/env node
// main v299 (Howard, 20 Nov): guests typed in the first message of a meeting / event fill the form's Guests - through the real
// Gate Context, Booked For and Form Offer. Every name, email and Slack id here is made up.
//   node scripts/sim-typed-guests.js [main v299]
const fs = require('fs');
const MAIN = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/project-jessie-v299.json', 'utf8'));
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 700))); } };
const jsOf = n => MAIN.nodes.find(x => x.name === n).parameters.jsCode;
const $f = O => n => ({ first: () => { if (!(n in O)) throw new Error('not run: ' + n); return O[n][0]; }, all: () => O[n] || [] });
const rooms = FX.rooms.concat(['Likha', 'Katha', 'Salin', 'Lobby'].filter(n => !FX.rooms.some(r => r.fields['Room Name'] === n)).map((n, i) => ({ id: 'cr' + i, fields: { 'Room Name': n, 'Room Type': [n === 'Lobby' ? 'Lobby' : 'Conference Room'] } })))
  .concat(['M3', 'M4'].map((n, i) => ({ id: 'mb' + i, fields: { 'Room Name': n, 'Room Type': ['M Booth'] } })));
const types = FX.sessionTypes.filter(x => !/^(Meeting|Event)$/.test(x.fields.Type)).concat([{ id: 'mt', fields: { Type: 'Meeting' } }, { id: 'ev', fields: { Type: 'Event' } }]);
const P = (id, Name, Initials, Info, Department) => ({ Name, Initials, 'Slack User ID': id, Info, Department: [Department], Authority: ['Standard'] });
const STAFF = [P('UREQ01', 'Sales Person', 'SP', 'Account Manager', 'Sales & Accounts'), P('UANA01', 'Ana Reyes', 'AR', 'Account Manager, Goes by Annie.', 'Marketing'),
  P('ULEA01', 'Lea Santos', 'LS', 'Marketing Lead', 'Marketing'), P('UJDC01', 'John Dela Cruz', 'JDC', 'Producer', 'Business Development'),
  P('UJTN01', 'John Tan', 'JT', 'Producer', 'Business Development'), P('UVIC01', 'Victor Ramos', 'VR', 'Managing Director, Goes by Vic, Sir Vic.', 'Management'),
  P('UBEN01', 'Ben Ong', 'BO', 'Post Engineer', 'Audio Post'), P('UNIK01', 'Nicole Lim', 'NL', 'Account Manager, Goes by Nikki', 'Sales & Accounts')];
const offer = async text => {
  Date.now = () => Date.parse('2026-11-20T06:00:00Z');
  const base = { 'Slack Trigger': [{ json: { text, user: 'UREQ01', ts: '1794500000.1', channel: 'D1' } }], 'Get Recent Messages': [{ json: { ts: '1794500000.1', text, user: 'UREQ01' } }],
    'Get Booker': [{ json: { fields: STAFF[0] } }], 'All Bookers': STAFF.map(f => ({ json: { fields: f } })), 'All Rooms': rooms.map(r => ({ json: r })), 'All Session Types': types.map(t => ({ json: t })) };
  base['Gate Context'] = [{ json: new Function('$', '$input', '$getWorkflowStaticData', jsOf('Gate Context'))($f(base), { first: () => ({ json: {} }), all: () => [] }, () => ({}))[0].json }];
  base['Booked For'] = [{ json: new Function('$', '$input', jsOf('Booked For'))($f(base), { first: () => ({ json: {} }) })[0].json }];
  const r = await new Function('$', '$input', 'return (async function(){' + jsOf('Form Offer') + '\n})();')($f(base), { first: () => ({ json: { keep: 1 } }), all: () => [{ json: { keep: 1 } }] });
  return r[0].json.formOffer || {};
};
const T = [
  ['book a meeting with ana this sunday, for test meeting 12-3pm', { gu: 'UANA01', d: '2026-11-22', s: '12:00', e: '15:00' }, 'Howard\'s message: "with ana this sunday" -> Ana; the date and times as before'],
  ['book a meeting with ana, lea and nicole tomorrow 2-3pm', { gu: 'UANA01,ULEA01,UNIK01' }, '"with ana, lea and nicole"'],
  ['book likha tomorrow 10-11am with ana & lea', { gu: 'UANA01,ULEA01', p: 'Meeting' }, 'a conference room (a Meeting) "with ana & lea"'],
  ['meeting in katha friday 3pm-4pm. attendees are ana, lea', { gu: 'UANA01,ULEA01' }, '"attendees are ana, lea"'],
  ['meeting in katha friday 3pm-4pm, attendees: ana and ben ong', { gu: 'UANA01,UBEN01' }, '"attendees: ana and ben ong" (full name)'],
  ['book salin monday 9-10am, guests: lea, nikki', { gu: 'ULEA01,UNIK01' }, '"guests: lea, nikki" (a Goes by name)'],
  ['book salin monday 9-10am and invite lea and sir vic', { gu: 'ULEA01,UVIC01' }, '"invite lea and sir vic" (honorific dropped, alias)'],
  ['meeting w/ annie and lea tomorrow 1-2pm', { gu: 'UANA01,ULEA01' }, '"w/ annie and lea"'],
  ['book a meeting with lea and client@acme.example tomorrow 1-2pm', { gu: 'ULEA01', ge: 'client@acme.example' }, 'an email typed -> Other guests'],
  ['book a meeting tomorrow 1-2pm, guests are lea, jane@outside.example, bob@outside.example', { gu: 'ULEA01', ge: 'jane@outside.example, bob@outside.example' }, 'emails in the list -> Other guests, in order'],
  ['book a meeting with john dela cruz tomorrow 1-2pm', { gu: 'UJDC01' }, 'a full name with three words'],
  ['book a meeting with john t tomorrow 1-2pm', { gu: 'UJTN01' }, '"john t" - first name + surname initial'],
  ['meeting with ana re budget tomorrow 2pm-3pm', { gu: 'UANA01' }, '"re budget" ends the list'],
  ['meeting with ana to discuss the launch tomorrow 2-3pm', { gu: 'UANA01' }, '"to discuss" ends the list'],
  ['meeting with ana tom 2-3pm', { gu: 'UANA01' }, '"ana tom" - the person, then the list ends (not "Ana Tom")'],
  ['book a meeting tomorrow 2-3pm. Attendees: Ana, Lea, Ben', { gu: 'UANA01,ULEA01,UBEN01' }, '"Attendees: Ana, Lea, Ben" in a second sentence'],
  ['book an event in the lobby on dec 5 all day with LS and BO', { gu: 'ULEA01,UBEN01', p: 'Event' }, 'an Event; initials in capitals'],
];
(async () => {
  console.log('Wordings -> Guests');
  for (const [text, want, why] of T) {
    const fo = await offer(text), pf = fo.prefill || {};
    const bad = Object.keys(want).filter(k => String(pf[k] || '') !== want[k]);
    ok(!bad.length && !/Not on the staff list|More than one/.test(fo.text || ''), why, { pf, text: fo.text });
  }
  console.log('The offer');
  let fo = await offer('book a meeting with ana, lea and nicole tomorrow 2-3pm');
  ok(/\nGuests: Ana Reyes, Lea Santos, Nicole Lim(\n|$)/.test(fo.text), 'the offer lists "Guests: Ana Reyes, Lea Santos, Nicole Lim"', fo.text);
  fo = await offer('book a meeting with lea and client@acme.example tomorrow 1-2pm');
  ok(/Guests: Lea Santos, client@acme\.example/.test(fo.text), 'names, then emails', fo.text);
  ok(JSON.parse(fo.blocks[1].elements[0].value).gu === 'ULEA01', 'the Book a room button carries them (the form picks them)');
  console.log('Not found / not sure');
  fo = await offer('book a meeting with john tomorrow 1-2pm');
  ok(!fo.prefill.gu && /More than one person called "John" – pick them under Guests in the form\./.test(fo.text), 'two Johns -> not guessed, "pick them in the form"', fo.text);
  fo = await offer('book a meeting with lea and bob tomorrow 1-2pm');
  ok(fo.prefill.gu === 'ULEA01' && /Not on the staff list: Bob – type their email in the form to invite them\./.test(fo.text), 'Bob not on the staff list -> named, Lea still a guest', fo.text);
  console.log('Not guests');
  for (const [text, why] of [['book a meeting with the team tomorrow 1-2pm', '"with the team"'], ['book a meeting with everyone tomorrow 1-2pm', '"with everyone"'],
      ['book a meeting with the BD team tomorrow 1-2pm', '"with the BD team"'], ['book a meeting with me tomorrow 1-2pm', '"with me"'],
      ['book a meeting tomorrow 1-2pm', 'no guests typed'], ['book a meeting with client Netflix tomorrow 1-2pm', '"with client Netflix" - not a guest'], ['book katha tomorrow 2-3pm with projector', '"with projector" - a thing']]) {
    fo = await offer(text); ok(!fo.prefill.gu && !fo.prefill.ge && !/Not on the staff list|More than one|Guests:/.test(fo.text), why + ': no guests, no note', { pf: fo.prefill, text: fo.text });
  }
  for (const [text, why] of [['book studio 7 tomorrow 1-3pm for VO recording with ana', 'a studio session "with ana"'], ['book m3 tomorrow with lea', 'an M booth "with lea"']]) {
    fo = await offer(text); ok(!fo.prefill.gu && !/Guests:/.test(fo.text || ''), why + ': not a meeting - no guests', { pf: fo.prefill, text: fo.text });
  }
  console.log('\n' + pass + ' ok, ' + fail + ' failed'); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
