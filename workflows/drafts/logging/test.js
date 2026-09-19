// Offline tests for the booking-log row-builder. Run: node workflows/drafts/logging/test.js
const { buildLogRow, manila } = require('./logrow');
let pass = 0, fail = 0;
const ok = (label, cond, detail) => { if (cond) { pass++; console.log('  ok    ' + label); }
  else { fail++; console.log('  FAIL  ' + label + (detail ? '  :: ' + detail : '')); } };

const COLS = ['Timestamp','Action','Title','Room(s)','Date','Time','Department','Booker','Done by','Event ID','Note'];

const booked = buildLogRow({ action:'BOOKED', title:'AUTHTEST / Sasa Abella / VA', rooms:'Studio 7',
  date:'2027-10-20', time:'3:00 PM – 5:00 PM', department:'Audio Post', booker:'Howard Luistro',
  eventId:'abc123', nowISO:'2027-10-20T09:05:00+08:00' });
ok('all columns present in order', COLS.every(k => k in booked) && Object.keys(booked).length === COLS.length, Object.keys(booked).join(','));
ok('timestamp is Manila, sortable', booked.Timestamp === '2027-10-20 09:05', booked.Timestamp);
ok('done-by defaults to booker on a self-booking', booked['Done by'] === 'Howard Luistro');

const moved = buildLogRow({ action:'MOVED', title:'X / Y / TL', rooms:['Studio 7'], date:'2027-10-15',
  time:'2:00 PM – 4:00 PM', department:'Audio Post', booker:'Vener Ariston', actor:'Howard Luistro',
  eventId:'new1', note:'Studio F → Studio 7', nowISO:'2027-10-15T10:00:00+08:00' });
ok('rooms array is joined', moved['Room(s)'] === 'Studio 7');
ok('done-by is the actor when it differs from booker', moved['Done by'] === 'Howard Luistro');
ok('note carries the relocation', moved.Note === 'Studio F → Studio 7');

const cancelled = buildLogRow({ action:'CANCELLED', title:'M4 / Peter / PL', date:'2027-10-08',
  booker:'Peter Legaste', actor:'Howard Luistro' });
ok('missing fields become empty strings, not undefined', cancelled['Event ID'] === '' && cancelled['Room(s)'] === '');
ok('cancel records who did it', cancelled['Done by'] === 'Howard Luistro' && cancelled.Action === 'CANCELLED');

console.log('\n' + (fail ? fail + ' failing, ' + pass + ' passing' : 'all ' + pass + ' checks pass'));
process.exit(fail ? 1 : 0);
