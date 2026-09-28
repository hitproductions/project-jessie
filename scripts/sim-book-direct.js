// Renders every Book Session input two ways - the agent tool's expression (prepared branch) and the
// Book Direct node's expression - with the same prepared booking, and requires them to be identical.
// v169 failed this for `description` (dropped "| Booked by: ... | ref: ...") and went live anyway.
//   node scripts/sim-book-direct.js [main.json]
const fs = require('fs');
const wf = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/project-jessie-v170.json', 'utf8'));
const node = n => wf.nodes.find(x => x.name === n);
const toolV = node('Book Session').parameters.workflowInputs.value;
const directV = node('Book Direct').parameters.workflowInputs.value;
const render = (tpl, ctx) => {
  let s = String(tpl); if (s.startsWith('=')) s = s.slice(1); else return s;
  return s.replace(/\{\{([\s\S]*?)\}\}/g, (_, expr) => {
    const v = new Function('$', '$fromAI', 'return (' + expr + ');')(ctx.$, () => { throw new Error('$fromAI reached - the prepared branch was not taken'); });
    return typeof v === 'object' ? JSON.stringify(v) : String(v);
  });
};
const mk = p => {
  const data = {
    'Prepared Booking': { use: true, ok: true, p },
    'Gate Context': { confirmed: true, datesUnderDiscussion: '2027-10-08' },
    'Get Booker': { fields: { Name: 'Tara Lim', Authority: ['Standard'] } },
    'Slack Trigger': { user: 'U026N6E1R' },
    'Room Table': { referenceData: '{"rooms":[],"types":[]}' },
    'Booked For': { requesterText: 'book studio 8', bookedFor: '' },
  };
  const $ = n => ({ first: () => ({ json: data[n] || {} }),
                    all: () => n === 'All Bookers' ? [{ json: { fields: { Name: 'Tara Lim', Initials: 'TL', Info: 'x', Department: ['Audio Post'] } } }] : [] });
  return { $ };
};
const cases = [
  { summary: 'QATESTORBIT / Jem Lim / TL', start_iso: '2027-10-08T14:00:00+08:00', end_iso: '2027-10-08T16:00:00+08:00', all_day: false,
    rooms: 'Studio 8', session_type: 'VO Recording', client: 'Jem Lim', engineer: 'Tara Lim (Post Engineer)',
    engineer_desc: 'Engineer: Tara Lim (Post Engineer)', department: 'Audio Post', bookingType: 'External', booked_for: '', room_override: false },
  { summary: 'EPIC / Jem Lim / DR x PL', start_iso: '2027-10-09T10:00:00+08:00', end_iso: '2027-10-09T12:00:00+08:00', all_day: false,
    rooms: 'Studio F', session_type: 'Music Mixing', client: 'Jem Lim', engineer: 'Daryl Reyes (Music Engineer)',
    engineer_desc: 'Engineer: Daryl Reyes (Music Engineer) | Arranger: Paolo Lim', department: 'Music', bookingType: 'External', booked_for: 'Japs Concepcion', room_override: true },
];
let fails = 0;
for (const p of cases) {
  const ctx = mk(p);
  for (const k of Object.keys(toolV)) {
    if (!(k in directV)) { console.log('  FAIL  missing in Book Direct:', k); fails++; continue; }
    let t, d;
    try { t = render(toolV[k], ctx); } catch (e) { t = 'TOOL-ERR ' + e.message; }
    try { d = render(directV[k], ctx); } catch (e) { d = 'DIRECT-ERR ' + e.message; }
    const skip = (k === 'exclude_event_id' || k === 'series');   // model-only in the tool; fixed '' / false in Book Direct
    if (t !== d && !skip) { console.log('  FAIL  ' + k + '\n        tool:   ' + t + '\n        direct: ' + d); fails++; }
  }
}
console.log(fails ? '\n' + fails + ' MISMATCH(ES)' : 'all ' + Object.keys(toolV).length + ' inputs identical on both paths, ' + cases.length + ' cases');
process.exit(fails ? 1 : 0);
