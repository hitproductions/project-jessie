// The three "Build Log Row" Code-node bodies, one per mutation sub-workflow, plus a mock
// harness so they unit-test offline before being pasted into the workflows. Each body reads
// its sub-workflow's nodes via $('Name').first().json and returns [{ json: <row> }] whose keys
// match the sheet headers exactly (the append node maps by header). Draft — see
// docs/design/booking-log.md.

const HELPERS = `
function manila(iso){ const d=iso?new Date(iso):new Date();
  const p=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Manila',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(d).reduce((o,x)=>(o[x.type]=x.value,o),{});
  return p.year+'-'+p.month+'-'+p.day+' '+p.hour+':'+p.minute; }
function dateOnly(iso){ try{ return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Manila',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(iso)); }catch(e){ return ''; } }
function timeRange(a,b){ const f=iso=>{ try{ return new Date(iso).toLocaleTimeString('en-US',{timeZone:'Asia/Manila',hour:'numeric',minute:'2-digit'}); }catch(e){ return ''; } };
  const s=f(a),e=f(b); return (s&&e)?(s+' \\u2013 '+e):''; }
`;

const BOOK = HELPERS + `
const V = $('Verify').first().json || {};
const REQ = $('When Executed by Another Workflow').first().json || {};
const desc = String(REQ.description || '');
const booker = ((desc.match(/Booked by:\\s*([^|]+)/) || [])[1] || '').trim();
const rooms = Array.isArray(REQ.rooms) ? REQ.rooms.join(', ') : String(REQ.rooms || '');
return [{ json: {
  'Timestamp': manila(),
  'Action': 'BOOKED',
  'Title': String(V.title || REQ.summary || ''),
  'Room(s)': rooms,
  'Date': dateOnly(REQ.start_iso),
  'Time': REQ.all_day ? 'all day' : timeRange(REQ.start_iso, REQ.end_iso),
  'Department': String(REQ.department || ''),
  'Booker': booker,
  'Done by': booker,
  'Event ID': String(V.event_id || ''),
  'Note': String(REQ.bookingType || '')
} }];
`;

const CANCEL = HELPERS + `
const CO = $('Check Ownership').first().json || {};
const REQ = $('When Executed by Another Workflow').first().json || {};
return [{ json: {
  'Timestamp': manila(),
  'Action': 'CANCELLED',
  'Title': String(CO.title || ''),
  'Room(s)': '',
  'Date': String(REQ.booking_date || ''),
  'Time': timeRange(CO.start, ''),
  'Department': '',
  'Booker': String(CO.bookerName || ''),
  'Done by': String(REQ.requester_name || CO.bookerName || ''),
  'Event ID': String(CO.event_id || ''),
  'Note': ''
} }];
`;

const MOVE = HELPERS + `
const RB = $('Resolve Booking').first().json || {};
const CR = $('Create Replacement').first().json || {};
const REQ = $('When Executed by Another Workflow').first().json || {};
return [{ json: {
  'Timestamp': manila(),
  'Action': 'MOVED',
  'Title': String(RB.title || ''),
  'Room(s)': String(RB.location || ''),
  'Date': dateOnly(RB.new_start),
  'Time': timeRange(RB.new_start, RB.new_end),
  'Department': '',
  'Booker': String(RB.bookerName || ''),
  'Done by': String(REQ.requester_name || RB.bookerName || ''),
  'Event ID': String(CR.id || ''),
  'Note': RB.roomNote ? ('moved' + RB.roomNote) : 'rescheduled'
} }];
`;

module.exports = { BOOK, CANCEL, MOVE };
