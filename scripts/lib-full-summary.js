// The summary as the old tests knew it, from what Render Summary returns. Book Session v73 (PENDING 69) shows only the
// title, Date, Time and Room and stores every other field in prep_payload; this puts those lines back in the old order
// (and the old note wording), so a test that checks a Client / Engineer / Department line still checks the same data.
// A REJECTED Check Conflicts result becomes "REJECTED <reason>".
module.exports = (o, c) => {
  if (c && c.verdict === 'REJECTED') return 'REJECTED ' + (c.reason || '');
  o = o || {};
  if (!o.prep_payload) return o.summary_text || '';
  let F = {}; try { F = JSON.parse(o.prep_payload).F || {}; } catch (e) {}
  const L = ['*' + F.Title + '*'];
  for (const k of ['Client', 'Project', 'Session Type', 'Date', 'Time', 'Room', 'Engineer', 'Arranger', 'Department', 'Booking Type', 'Booked by'])
    if (F[k]) L.push('*' + k + ':* ' + F[k]);
  const notes = String(o.summary_text || '').split(/\n\s*\n/).slice(1).filter(b => !/^Confirm to book\.$/.test(b.trim()))
    .map(b => b.replace(/You’re down as the engineer\./, "No engineer was named, so you're down as the engineer. If someone else is engineering, tell me who."));
  return L.join('\n') + (notes.length ? '\n\n' + notes.map(n => n.split('\n').map(x => '*Note:* ' + x).join('\n')).join('\n') : '') + '\n\nConfirm to book.';
};
