const { BOOK, CANCEL, MOVE } = require('./rowbuilders');
let pass=0, fail=0;
const ok=(l,c,d)=>{ if(c){pass++;console.log('  ok    '+l);} else {fail++;console.log('  FAIL  '+l+(d?'  :: '+d:''));} };
const mk = nodes => name => ({ first: () => ({ json: nodes[name] || {} }) });
const run = (body, nodes) => new Function('$', body)(mk(nodes))[0].json;

console.log('Book row');
const b = run(BOOK, {
  'Verify': { status:'CREATED', event_id:'ev1', title:'AUTHTEST / Sasa Abella / VA' },
  'When Executed by Another Workflow': { summary:'AUTHTEST / Sasa Abella / VA', rooms:'Studio 7',
    start_iso:'2027-10-20T15:00:00+08:00', end_iso:'2027-10-20T17:00:00+08:00',
    department:'Audio Post', bookingType:'External',
    description:'Engineer: Vener (Post Engineer) | Booked by: Howard Luistro | ref: U08V3CKDGJF | Type: External | Dept: Audio Post' }
});
ok('action BOOKED', b.Action==='BOOKED');
ok('title from Verify', b.Title==='AUTHTEST / Sasa Abella / VA');
ok('booker parsed from description', b.Booker==='Howard Luistro' && b['Done by']==='Howard Luistro', b.Booker);
ok('room + dept + eventid', b['Room(s)']==='Studio 7' && b.Department==='Audio Post' && b['Event ID']==='ev1');
ok('date is Manila', b.Date==='2027-10-20', b.Date);
ok('time is a range', /\d.*–.*\d/.test(b.Time), b.Time);
ok('all 11 columns', Object.keys(b).length===11);

console.log('\nCancel row');
const c = run(CANCEL, {
  'Check Ownership': { title:'M4 / Peter / PL', event_id:'ev2', bookerName:'Peter Legaste', start:'2027-10-08T16:00:00+08:00' },
  'When Executed by Another Workflow': { booking_date:'2027-10-08', requester_name:'Howard Luistro' }
});
ok('action CANCELLED', c.Action==='CANCELLED');
ok('booker vs done-by (coordinator cancel)', c.Booker==='Peter Legaste' && c['Done by']==='Howard Luistro');
ok('date + eventid', c.Date==='2027-10-08' && c['Event ID']==='ev2');

console.log('\nMove row');
const m = run(MOVE, {
  'Resolve Booking': { title:'X / Y / TL', location:'Studio 7', new_start:'2027-10-15T14:00:00+08:00',
    new_end:'2027-10-15T16:00:00+08:00', bookerName:'Vener Ariston', roomNote:' to Studio 7' },
  'Create Replacement': { id:'ev3' },
  'When Executed by Another Workflow': { requester_name:'Howard Luistro', booking_date:'2027-10-15' }
});
ok('action MOVED', m.Action==='MOVED');
ok('new room + new event id', m['Room(s)']==='Studio 7' && m['Event ID']==='ev3');
ok('note carries relocation', m.Note==='moved to Studio 7', m.Note);
ok('done-by is the actor', m['Done by']==='Howard Luistro' && m.Booker==='Vener Ariston');

console.log('\n'+(fail? fail+' failing, '+pass+' passing' : 'all '+pass+' checks pass'));
process.exit(fail?1:0);
