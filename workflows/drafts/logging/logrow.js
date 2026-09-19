// Booking event log — the shared row-builder. Every mutation (Book Session, Cancel, Move,
// Book Series) composes a context object and calls this to produce one Google Sheets row,
// so the columns and formatting are identical across all four and unit-testable offline.
// Draft — not wired. See docs/design/booking-log.md.
//
// In the real nodes each sub-workflow fills `ctx` from its own node outputs (the row is
// written at the mutation point, deterministically, never by the model), then a Google
// Sheets "append" node maps these keys to columns by header name.

function manila(nowISO) {
  const d = nowISO ? new Date(nowISO) : new Date();
  // "2027-10-20 14:05" in Asia/Manila, sortable.
  const p = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: false,
  }).formatToParts(d).reduce((o, x) => (o[x.type] = x.value, o), {});
  return `${p.year}-${p.month}-${p.day} ${p.hour}:${p.minute}`;
}

// ctx: { action, title, rooms, date, time, department, booker, actor, eventId, note, nowISO }
// action is one of BOOKED / CANCELLED / MOVED / UPDATED / SERIES.
function buildLogRow(ctx) {
  const c = ctx || {};
  const s = v => (v == null ? '' : String(v)).trim();
  const rooms = Array.isArray(c.rooms) ? c.rooms.join(', ') : s(c.rooms);
  return {
    'Timestamp':  manila(c.nowISO),
    'Action':     s(c.action),
    'Title':      s(c.title),
    'Room(s)':    rooms,
    'Date':       s(c.date),
    'Time':       s(c.time),
    'Department': s(c.department),
    'Booker':     s(c.booker),
    'Done by':    s(c.actor) || s(c.booker),   // actor defaults to the booker on a self-action
    'Event ID':   s(c.eventId),
    'Note':       s(c.note),
  };
}

module.exports = { buildLogRow, manila };
