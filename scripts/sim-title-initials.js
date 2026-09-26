// Offline check of Book Session v48: title initials come from the engineer's Bookers record,
// now for two-segment Localization titles too. Replays Howard's NET-KUBA booking of 2026-09-26.
//   node scripts/sim-title-initials.js
const fs = require('fs');
const CHECK = JSON.parse(fs.readFileSync(process.env.BOOK || 'workflows/book-session-v48.json', 'utf8'))
  .nodes.find(n => n.name === 'Check Conflicts').parameters.jsCode;
let fails = 0; const ok = (c, m) => { console.log((c ? '  ok    ' : '  FAIL  ') + m); if (!c) fails++; };
Date.now = () => Date.UTC(2026, 8, 26, 7, 26, 0);
const STAFF = [
  { Name: 'Jek Panganiban', Initials: 'FP', Info: 'Loc Engineer, Goes by Jek, Francis, FP.' },
  { Name: 'Daryl Reyes', Initials: 'DR', Info: 'Music Engineer. Goes by Daryl, Drei, Drey, DR.' },
  { Name: 'Paolo Lim', Initials: 'PL', Info: 'Music Arranger. Goes by Paolo, PL.' },
];
const run = req => {
  const $ = name => ({
    first: () => ({ json: name === 'When Executed by Another Workflow' ? req : {} }),
    all: () => name === 'All Bookers' ? STAFF.map(f => ({ json: { fields: f } })) : []
  });
  const $input = { all: () => [], first: () => ({ json: {} }) };
  return new Function('$', '$input', CHECK)($, $input)[0].json;
};
const REF = JSON.stringify({ rooms: [{ name: 'Studio 1' }], types: [{ type: 'Localization Dubbing', min: 240, max: 600 }, { type: 'Music Mixing', min: 60, max: 480 }] });
const base = { confirmed: true, reference_data: REF, rooms: 'Studio 1, Studio A',
               start_iso: '2027-10-05T16:00:00+08:00', end_iso: '2027-10-05T22:00:00+08:00' };
let r = run(Object.assign({}, base, { summary: 'NET-KUBA / JP', engineer: 'Jek Panganiban (Loc Engineer)', session_type: 'Localization Dubbing' }));
ok(r.final_summary === 'NET-KUBA / FP', "Howard's case: 'NET-KUBA / JP' is booked as '" + r.final_summary + "'");
r = run(Object.assign({}, base, { summary: 'NET-KUBA / FP', engineer: 'Jek Panganiban (Loc Engineer)', session_type: 'Localization Dubbing' }));
ok(r.final_summary === 'NET-KUBA / FP', 'already-correct Localization title is unchanged');
r = run(Object.assign({}, base, { summary: 'NET-KUBA / JP', engineer: 'jek', session_type: 'QC' }));
ok(r.final_summary === 'NET-KUBA / FP', 'QC counts as Localization, nickname resolved -> ' + r.final_summary);
r = run(Object.assign({}, base, { summary: 'EPIC / Jem Lim / DJ x PX', engineer: 'Daryl Reyes (Music Engineer)', session_type: 'Music Mixing',
                                  description: 'Engineer: Daryl Reyes (Music Engineer) | Arranger: Paolo Lim' }));
ok(r.final_summary === 'EPIC / Jem Lim / DR x PL', 'three-segment music title still corrected as before -> ' + r.final_summary);
r = run(Object.assign({}, base, { summary: 'SOMETHING / JP', engineer: 'Jek Panganiban (Loc Engineer)', session_type: 'Post Mixing' }));
ok(r.final_summary === 'SOMETHING / JP', 'a two-segment title outside Localization is left alone');
r = run(Object.assign({}, base, { summary: 'M5 - Howard', rooms: 'M5', session_type: '', engineer: '' }));
ok(r.final_summary === 'M5 - Howard', 'an internal-room title is untouched');
console.log(fails ? '\n' + fails + ' FAILED' : '\nall passed'); process.exit(fails ? 1 : 0);
