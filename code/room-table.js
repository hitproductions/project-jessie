// Builds the room-ranking reference the system prompt interpolates. The lists
// live in Airtable as record ids the model cannot read, and it will not call a
// tool to resolve them - so they are resolved here and handed to it as text.
const nameOf = {};
// Conference rooms are read out of Airtable rather than named here, so adding
// one does not need a code change. Room Type carries "Conference Room" for
// Salin, Likha and Katha.
const isConference = {};
// Vocal booths come from the `Vocal Booth` checkbox, never from Room Type.
// Room Type marks Studio E as a Recording Booth, but E is the video and colour
// grading room - on 2026-09-01 she was offering it as a go-to booth pairing
// because Room Type was the only booth signal reaching her. The checkbox is
// already correct in Airtable (A, B and D); nothing was reading it. Tick the
// box on another room and it appears here with no code change.
const vocalBooths = [];
const otherBooths = [];
try {
  for (const it of $('All Rooms').all()) {
    const r = (it && it.json) || {};
    const f = r.fields || {};
    if (!r.id) continue;
    const nm = String(f['Room Name'] || '').trim();
    nameOf[r.id] = nm;
    const kinds = [].concat(f['Room Type'] || []).map(x => String(x).toLowerCase());
    if (kinds.indexOf('conference room') !== -1) isConference[nm.toLowerCase()] = true;
    if (f['Vocal Booth'] === true) vocalBooths.push(nm);
    else if (kinds.indexOf('recording booth') !== -1) otherBooths.push(nm);
  }
} catch (e) {}

const lines = [];
try {
  for (const it of $('All Session Types').all()) {
    const f = ((it && it.json) || {}).fields || {};
    const type = String(f['Type'] || '').trim();
    if (!type) continue;
    const names = ids => [].concat(ids || []).map(i => nameOf[i]).filter(Boolean);
    const pri = names(f['Priority']), last = names(f['Last Resort']);
    if (!pri.length && !last.length) continue;
    // "Priority" and "Last Resort" are the Airtable column names, not words a
    // requester should ever hear - Tara, 2026-08-30. She read them straight out
    // of this table and told someone a room was "a last-resort choice", which
    // sounds like a rule when it is a preference. The distinction still drives
    // the guards; only the wording changed.
    // A conference room is never Jessie's to pick - the requester has to ask for
    // one and say which. That rule used to live only in a distant paragraph of
    // the prompt, and on 2026-08-30 she offered Likha, Katha and Salin for a
    // Celebrity Recording unprompted. Book Session cannot catch it either,
    // because they are legitimately on that session type's list. So the
    // constraint travels with the names instead.
    const conf = c => c.filter(r => isConference[r.toLowerCase()]);
    const plain = c => c.filter(r => !isConference[r.toLowerCase()]);
    const confRooms = conf(pri.concat(last)).filter((r, i, a) => a.indexOf(r) === i);
    const priPlain = plain(pri);
    // Four session types list the same room as both Priority and Last Resort -
    // VO Recording and Event have identical lists - which produced
    // "Lobby · also possible: Lobby". A room already offered is not an
    // alternative to itself.
    const lastPlain = plain(last).filter(r => priPlain.indexOf(r) === -1);
    const parts = [];
    if (priPlain.length)  parts.push('normally: ' + priPlain.join(', '));
    if (lastPlain.length) parts.push('also possible: ' + lastPlain.join(', '));
    // For a Meeting every room is a conference room, so this is the whole list
    // rather than a caveat on it - saying "normally: none on file" would read
    // as though Meetings have nowhere to go.
    if (confRooms.length) parts.push('conference rooms, ask which before booking: ' + confRooms.join(', '));
    if (!parts.length) parts.push('no rooms on file');
    lines.push('- ' + type + ' — ' + parts.join(' · '));
  }
} catch (e) {}

lines.sort();

// The session types, read live, so the list she offers cannot go stale when Tel
// adds one - which had already happened: Localization Atmos Mixing existed in
// Airtable and appeared nowhere in the prompt.
const typeNames = [];
try {
  for (const it of $('All Session Types').all()) {
    const t = String((((it && it.json) || {}).fields || {})['Type'] || '').trim();
    if (t && typeNames.indexOf(t) === -1) typeNames.push(t);
  }
} catch (e) {}
typeNames.sort();

// A department-flavoured e.g. for the session-type question. Not a filter -
// bookers routinely book outside their own department, and eight of the eleven
// departments map to no session type at all. The full list stays available.
const DEPT_ROLES = {
  'audio post':   ['post engineer'],
  'localization': ['loc engineer'],
  'music':        ['music engineer', 'music arranger']
};
const bookerFields = (function(){ try { return ($('Get Booker').first().json || {}).fields || {}; }
                                  catch (e) { return {}; } })();
const myRoles = [];
for (const d of [].concat(bookerFields['Department'] || [])) {
  for (const r of (DEPT_ROLES[String(d).trim().toLowerCase()] || [])) myRoles.push(r);
}
const suggested = [];
if (myRoles.length) {
  try {
    for (const it of $('All Session Types').all()) {
      const f = ((it && it.json) || {}).fields || {};
      const t = String(f['Type'] || '').trim();
      if (!t) continue;
      const roles = [].concat(f['Engineer Role Required'] || []).map(r => String(r).trim().toLowerCase());
      if (roles.some(r => myRoles.indexOf(r) !== -1) && suggested.indexOf(t) === -1) suggested.push(t);
    }
  } catch (e) {}
}
suggested.sort();
const sessionTypeHint = suggested.length ? suggested.join(', ') : '';
const sessionTypes = typeNames.length
  ? typeNames.join(' · ')
  : '(session type list unavailable this run - ask Session Types before offering any)';
let text = lines.length
  ? lines.join('\n')
  : '(room ranking unavailable this run - ask Rooms and Studios before naming any room)';
// The booth line rides on the ranking block rather than a new prompt variable,
// so the system prompt needs no change and the two cannot drift apart.
if (vocalBooths.length) {
  let boothLine = '- Vocal booths - normally: ' + vocalBooths.sort().join(' \u00b7 ') + '.';
  if (otherBooths.length) {
    boothLine += ' ' + otherBooths.sort().join(' and ')
      + (otherBooths.length > 1 ? ' are Recording Booths but not vocal booths' : ' is a Recording Booth but not a vocal booth')
      + ' - pair ' + (otherBooths.length > 1 ? 'one' : 'it')
      + ' only when the requester asks for it by name, and when you do, say the vocal booths we normally use are '
      + vocalBooths.sort().join(', ') + ' and name which of those are free.';
  }
  text += '\n' + boothLine;
}
// Reference data for the sub-workflows. Both used to re-read these two tables
// on every call, so on a booking turn the same tables were fetched three times.
// Passed down instead - resolved once, here.
const refRooms = [];
try {
  for (const it of $('All Rooms').all()) {
    const r = (it && it.json) || {}; const f = r.fields || {};
    if (r.id && f['Room Name']) refRooms.push({ id: r.id, name: String(f['Room Name']).trim(), vocalBooth: f['Vocal Booth'] === true });
  }
} catch (e) {}
const refTypes = [];
try {
  for (const it of $('All Session Types').all()) {
    const r = (it && it.json) || {}; const f = r.fields || {};
    const t = String(f['Type'] || '').trim();
    if (!t) continue;
    refTypes.push({ type: t, min: f['Min Duration (mins)'] || null, max: f['Max Duration (mins)'] || null,
                    priority: [].concat(f['Priority'] || []), last: [].concat(f['Last Resort'] || []) });
  }
} catch (e) {}
// --- "book Studio F for Howard" ------------------------------------------
// A name after "for" is not the client, and on 2026-08-30 she put one in the
// client field without asking: "Book Studio F for Howard" produced the title
// ORION / Howard / TL, with no lookup and no question. Howard is staff.
//
// Detected here rather than in Gate Context because only this node can see the
// session-type list, and "for Post Mixing" looks identical to "for Howard".
// Room names are excluded for the same reason. It does not try to work out what
// the name is - it only stops the client field being filled from a guess.
let forNameNotice = '';
try {
  const msg = String(($('Slack Trigger').first().json || {}).text || '')
    .replace(/\*sent using\*[\s\S]*$/i, '');
  const saidClient = /\bclients?\b/i.test(msg);
  const known = []
    .concat(typeNames.map(t => t.toLowerCase()))
    .concat(refRooms.map(r => r.name.toLowerCase()));
  const hits = [];
  const re = /\bfor\s+([A-Z][\w.'-]*(?:\s+[A-Z][\w.'-]*){0,3})/g;
  let m;
  while ((m = re.exec(msg)) !== null) {
    const phrase = m[1].trim();
    const low = phrase.toLowerCase();
    if (known.some(k => k && (low === k || low.indexOf(k) === 0 || k.indexOf(low) === 0))) continue;
    hits.push(phrase);
  }
  if (!saidClient && hits.length) {
    forNameNotice = 'THEY WROTE "for ' + hits[0] + '" AND HAVE NOT SAID WHO THE CLIENT IS. A name after '
      + '"for" is not the client - it is as likely to be the person you are booking on behalf of, or the '
      + 'project. Do not put it in the client field or the title on that basis. Ask who the client is, and '
      + 'ask what ' + hits[0] + ' is if it is still unclear, before you present any summary. Internal rooms '
      + '- M Booth, Lobby and Conference Room - have no client, so ignore this if the booking is one of those.';
  }
} catch (e) {}

// The prompt used to carry a written-out room list. Rooms come from Airtable
// already, so it is built here instead - one less list that can go stale, and
// no extra call, since All Rooms was read this turn anyway.
const roomNames = refRooms.length
  ? refRooms.map(r => r.name).join(' · ')
  : '(room list unavailable this run - ask Rooms and Studios)';

const referenceData = (refRooms.length && refTypes.length)
  ? JSON.stringify({ rooms: refRooms, types: refTypes }) : '';

return [{ json: Object.assign({}, $('Gate Context').first().json, { referenceData: referenceData, roomTable: text, sessionTypes: sessionTypes, sessionTypeHint: sessionTypeHint, forNameNotice: forNameNotice, roomNames: roomNames }) }];
