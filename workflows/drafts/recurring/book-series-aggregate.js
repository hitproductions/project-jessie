// Book Series aggregate: zip the Expand Dates occurrences with the per-date Book Session
// results (same order), report booked / skipped / failed, and set a status Guard Probe
// recognizes as backing a "Booked" claim.
const occ = $('Expand Dates').all().map(i => i.json).filter(o => o._go);
const results = $input.all().map(i => i.json);
const DOW = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
const MON = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const wd  = d => DOW[new Date(d + 'T00:00:00Z').getUTCDay()];
const fmt = d => { const x = new Date(d + 'T00:00:00Z'); return MON[x.getUTCMonth()] + ' ' + x.getUTCDate() + ', ' + x.getUTCFullYear(); };
const booked = [], skipped = [], notConf = [], failed = [];
for (let i = 0; i < occ.length; i++) {
  const r = results[i] || {}, date = occ[i]._date;
  if (r.status === 'CREATED') booked.push(date);
  else if (r.reason === 'ROOM_OCCUPIED' || r.status === 'ROOM_DECLINED') skipped.push(date);
  else if (r.reason === 'NOT_CONFIRMED') notConf.push(date);
  else failed.push({ date: date, why: (r.reason || r.status || 'unknown') });
}
if (notConf.length && notConf.length === occ.length) {
  return [{ json: { status: 'NOT_CONFIRMED',
    human: 'This series is not approved yet. Present the full list of dates, end with the line "Confirm to book.", and stop - then book only after they reply yes.' } }];
}
const line = d => '- ' + fmt(d) + ' (' + wd(d) + ')';
const parts = [];
if (booked.length) parts.push('Booked ' + booked.length + ' session' + (booked.length === 1 ? '' : 's') + ':\n' + booked.map(line).join('\n'));
if (skipped.length) parts.push('Skipped - the room was already taken on:\n' + skipped.map(line).join('\n') + '\nWant these at a different time, or a nearby day?');
if (failed.length) parts.push('Could not book:\n' + failed.map(f => line(f.date) + ' - ' + f.why).join('\n'));
const human = parts.join('\n\n') || 'Nothing was booked.';
const status = booked.length ? 'BOOKED_SERIES' : ((skipped.length || failed.length) ? 'NONE_BOOKED' : 'EMPTY');
return [{ json: { status: status, booked: booked, skipped: skipped, failed: failed, human: human } }];
