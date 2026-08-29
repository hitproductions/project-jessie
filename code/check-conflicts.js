const REQ = $('When Executed by Another Workflow').first().json;

// Get Events In Window is an HTTP Request against the Calendar API and returns
// one item holding an `items` array. Older shape - one n8n item per event - is
// still accepted so this node works either way.
const EVENTS = (function(){
  // Get Events In Window is an HTTP Request. If it ever runs more than once it
  // emits one copy of the whole response per input item, so flatten every
  // `items` array found and de-duplicate by event id. A bare event object per
  // item is accepted too, so the old calendar node still works here.
  const out = [], seen = {};
  for (const it of $input.all()) {
    const j = (it && it.json) || {};
    const list = Array.isArray(j.items) ? j.items : (j && j.id ? [j] : []);
    for (const ev of list) { if (ev && ev.id && !seen[ev.id]) { seen[ev.id] = 1; out.push(ev); } }
  }
  return out;
})();


const ROOMS = {
  'Studio 1': 'hitproductions.net_3737303833303637363538@resource.calendar.google.com',
  'Studio 2': 'c_18871bprki2umhrkjc4qcaldse1f8@resource.calendar.google.com',
  'Studio 3': 'c_1886me03bdcrki5bhu8vddknl472k@resource.calendar.google.com',
  'Studio 4': 'c_188e94dapvbp8jvrjmuga6qbof826@resource.calendar.google.com',
  'Studio 5': 'c_18889v3glj9cqiotg8j95jaqmdhmm@resource.calendar.google.com',
  'Studio 6': 'c_18838qt2ru30ein7gcefjiarplkre@resource.calendar.google.com',
  'Studio 7': 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com',
  'Studio 8': 'c_18863v8hd6f42isegdh9i30psuo9q@resource.calendar.google.com',
  'Studio A': 'c_18843dclutqm6hl9nbeg002phapfu@resource.calendar.google.com',
  'Studio B': 'c_1881vgb66tkpujjelnn3rniugd9pk@resource.calendar.google.com',
  'Studio C': 'c_188797f37eu9ujs6ldpf3smn78joc@resource.calendar.google.com',
  'Studio D': 'c_18801gc6ck77gho7jl0e1fug94u92@resource.calendar.google.com',
  'Studio E': 'c_18807te03d2sqh0lmtal9sbb04gao@resource.calendar.google.com',
  'Studio F': 'c_188em7d58podeju3i8q6juqlufkls@resource.calendar.google.com',
  'Studio M': 'c_1885k4adm87fqjd2j3j2usqftph5c@resource.calendar.google.com',
  'M1': 'c_1889v46vd62fkjk3i7r1hsfem7tcm@resource.calendar.google.com',
  'M2': 'c_1883ui6lnfc9ogt2hrmg57a30n72q@resource.calendar.google.com',
  'M3': 'c_188d7dkqgnfs6hu4iunlu5ogftct0@resource.calendar.google.com',
  'M4': 'c_18869nhmsj2uki8mljoi48v1cj7l4@resource.calendar.google.com',
  'M5': 'c_1889h30ci9noqjcbnoogad9qk75vq@resource.calendar.google.com',
  'M6': 'c_188f9gnq0a9tehf4g9ja57l83c0ts@resource.calendar.google.com',
  'M7': 'c_1880r9hhk9c2agpbko87o7fojosh0@resource.calendar.google.com',
  'M8': 'c_1884cu2cc84iujsjnu03s21f0ct9q@resource.calendar.google.com',
  'Salin': 'c_1887hh5rsv6q4gt8hnu6ered170lg@resource.calendar.google.com',
  'Katha': 'c_1881169pcpn12gsnm6i7sc0gjk7gk@resource.calendar.google.com',
  'Likha': 'c_1886t6cjgrq0ihgpime01uibcqsg6@resource.calendar.google.com',
  'Lobby': 'c_188227mpeagjuhi7gqlgns1di14be@resource.calendar.google.com'
};

// --- required fields ----------------------------------------------------
// $fromAI inputs carry defaults so a partial tool call reaches this node instead
// of failing n8n's schema validation, which killed the whole turn and dropped the
// conversation into the error branch. Missing pieces are answered, not crashed.
const missing = [];
if (!String(REQ.summary || '').trim())   missing.push('a title');
if (!String(REQ.start_iso || '').trim()) missing.push('a start time');
if (!String(REQ.end_iso || '').trim())   missing.push('an end time');
if (!String(REQ.rooms || '').trim())     missing.push('a room');
if (missing.length) {
  return [{ json: { verdict:'REJECTED', reason:'MISSING_DETAILS', missing,
    human:'Nothing was booked - the booking is still missing ' + missing.join(', ')
        + '. Ask the requester for what is missing, then present the summary again.' } }];
}

// --- confirmation gate -------------------------------------------------
// `confirmed` is computed by Gate Context in the calling workflow from real
// Slack history: the last thing Jessie said must be a summary ending in the
// marker line, and the requester must have replied after it. Send Reply runs
// after the agent, so a summary written in THIS turn is not in Slack yet and
// cannot satisfy this. The model never supplies this value.
const confirmed = REQ.confirmed === true || String(REQ.confirmed).toLowerCase() === 'true';
const roomList = String(REQ.rooms || '').split(',').map(r => r.trim()).filter(r => r.length);
const mBoothOnly = roomList.length > 0 && roomList.every(r => /^M[1-8]$/i.test(r));
if (!confirmed && !mBoothOnly) {
  return [{ json: { verdict:'REJECTED', reason:'NOT_CONFIRMED',
    human:'Nothing was booked, because the requester has not approved this booking yet. '
        + 'Present the complete booking summary now, end it with the line "Confirm to book.", '
        + 'and stop. Book it only after they reply approving it. Do not call this tool again '
        + 'in this response.' } }];
}

// --- duration limits ---------------------------------------------------
// Session Types holds Min/Max Duration (mins). Enforced here because this is
// the only path that creates a booking. Silent when the session type was not
// supplied or not found - an internal room has no session type, and a lookup
// failure must not block a booking that is otherwise fine.
const ST = (function(){ try { return ($('Get Session Type').first().json || {}).fields || {}; }
                        catch (e) { return {}; } })();
const minD = Number(ST['Min Duration (mins)']);
const maxD = Number(ST['Max Duration (mins)']);
const override = REQ.duration_override === true || String(REQ.duration_override).toLowerCase() === 'true';
const allDay = REQ.all_day === true || String(REQ.all_day).toLowerCase() === 'true';
if (!allDay && !override && (Number.isFinite(minD) || Number.isFinite(maxD))) {
  const mins = Math.round((new Date(REQ.end_iso).getTime() - new Date(REQ.start_iso).getTime()) / 60000);
  const tooShort = Number.isFinite(minD) && mins < minD;
  const tooLong  = Number.isFinite(maxD) && mins > maxD;
  if (mins > 0 && (tooShort || tooLong)) {
    const range = (Number.isFinite(minD) ? minD : '?') + '-' + (Number.isFinite(maxD) ? maxD : '?');
    return [{ json: { verdict:'REJECTED', reason:'DURATION_OUT_OF_RANGE',
      requested_mins: mins, min_mins: Number.isFinite(minD) ? minD : null,
      max_mins: Number.isFinite(maxD) ? maxD : null,
      human: 'Nothing was booked. A ' + (ST['Type'] || 'session') + ' runs ' + range
           + ' minutes and this one is ' + mins + '. Tell the requester the length they asked for and the '
           + 'allowed range, and ask whether they want to adjust it. If they say to book it anyway, they '
           + 'must say so in their own message first - only then book it again as an override.' } }];
  }
}

// --- room ranking ------------------------------------------------------
// Session Types ranks rooms per type: Priority first, Last Resort only when
// every Priority room is taken. Both lists are record ids, so Get Rooms
// returns every bookable room and the ids are resolved here. The model is not
// consulted and cannot skip this.
const stRec = (function(){ try { return $('Get Session Type').first().json || {}; }
                           catch (e) { return {}; } })();
const stF = stRec.fields || {};
const priorityIds = [].concat(stF['Priority'] || []);
const lastIds     = [].concat(stF['Last Resort'] || []);

if ((priorityIds.length || lastIds.length) && !allDay) {
  let allRooms = [];
  try { allRooms = $('Get Rooms').all().map(i => (i && i.json) || {}); } catch (e) { allRooms = []; }
  const nameOf = {};
  for (const r of allRooms) { if (r.id) nameOf[r.id] = String((r.fields || {})['Room Name'] || '').trim(); }
  const priorityNames = priorityIds.map(id => nameOf[id]).filter(Boolean);
  const lastNames     = lastIds.map(id => nameOf[id]).filter(Boolean);
  const asked = String(REQ.rooms || '').split(',').map(r => r.trim()).filter(r => r.length);
  const lower = a => a.map(x => x.toLowerCase());

  // a room in neither list is not run for this session type at all
  if (priorityNames.length || lastNames.length) {
    const known = lower(priorityNames.concat(lastNames));
    const notRun = asked.filter(r => known.indexOf(r.toLowerCase()) === -1);
    if (notRun.length) {
      return [{ json: { verdict:'REJECTED', reason:'ROOM_UNSUITABLE', unsuitable: notRun,
        priority: priorityNames, last_resort: lastNames,
        human: (stF['Type'] || 'That session type') + ' is not run in ' + notRun.join(', ')
             + '. Nothing was booked. Offer these instead: ' + priorityNames.join(', ') + '.' } }];
    }
  }

  // a Last Resort room is only allowed when every Priority room is busy
  const askedLastResort = asked.filter(r => lower(lastNames).indexOf(r.toLowerCase()) !== -1
                                         && lower(priorityNames).indexOf(r.toLowerCase()) === -1);
  if (askedLastResort.length && priorityNames.length) {
    // occupancy computed inline: roomsOf() is declared below and closes over
    // `keys`, which is not initialised yet at this point in the script.
    const roomKeys = Object.keys(ROOMS);
    const exclude = String(REQ.exclude_event_id || '').trim();
    const busy = {};
    for (const ev of EVENTS) {
      if (!ev || !ev.id) continue;
      if (exclude && ev.id === exclude) continue;
      const s0 = new Date(ev.start && (ev.start.dateTime || ev.start.date)).getTime();
      const e0 = new Date(ev.end   && (ev.end.dateTime   || ev.end.date)).getTime();
      if (!(s0 < new Date(REQ.end_iso).getTime() && e0 > new Date(REQ.start_iso).getTime())) continue;
      const emails = (ev.attendees || []).map(a => String(a.email || '').toLowerCase());
      const loc = String(ev.location || '').toLowerCase();
      const firstSeg = String(ev.summary || '').split(' - ')[0].trim().toLowerCase();
      for (const k of roomKeys) {
        const lk = k.toLowerCase();
        if (emails.indexOf(ROOMS[k].toLowerCase()) !== -1 || (loc && loc.indexOf(lk) !== -1) || firstSeg === lk) {
          busy[lk] = true;
        }
      }
    }
    const freePriority = priorityNames.filter(r => !busy[r.toLowerCase()]);
    if (freePriority.length) {
      return [{ json: { verdict:'REJECTED', reason:'ROOM_NOT_PRIORITY',
        requested: askedLastResort, free_priority: freePriority, last_resort: lastNames,
        human: askedLastResort.join(', ') + ' is a last-resort room for '
             + (stF['Type'] || 'this session type') + ', and these priority rooms are free at that time: '
             + freePriority.join(', ') + '. Nothing was booked. Offer one of those. Only use a '
             + 'last-resort room when every priority room is taken.' } }];
    }
  }
}

const wantedNames = String(REQ.rooms || '').split(',').map(r => r.trim()).filter(r => r.length);
if (!wantedNames.length) {
  return [{ json: { verdict:'REJECTED', reason:'NO_ROOM', human:'No room was given, so nothing was booked.' } }];
}
const keys = Object.keys(ROOMS);
const wanted = [];
for (const name of wantedNames) {
  const hit = keys.find(k => k.toLowerCase() === name.toLowerCase());
  if (!hit) {
    return [{ json: { verdict:'REJECTED', reason:'UNKNOWN_ROOM',
      human:'I do not recognise the room "' + name + '", so nothing was booked.' } }];
  }
  wanted.push({ name: hit, id: ROOMS[hit].toLowerCase() });
}

// Work out which room an event occupies, from strongest signal to weakest.
// 1. resource attendee  2. location string  3. title's first segment, because
// internal-room bookings are titled "M2 - Peemo", "Lobby - Party", "KATHA - ...".
function roomsOf(ev) {
  const found = [];
  const emails = (ev.attendees || []).map(a => String(a.email || '').toLowerCase());
  const loc = String(ev.location || '').toLowerCase();
  const firstSeg = String(ev.summary || '').split(' - ')[0].trim().toLowerCase();
  for (const k of keys) {
    const lk = k.toLowerCase();
    if (emails.indexOf(ROOMS[k].toLowerCase()) !== -1) { found.push(k); continue; }
    if (loc && loc.indexOf(lk) !== -1) { found.push(k); continue; }
    if (firstSeg && firstSeg === lk) { found.push(k); }
  }
  return found;
}

const ms = v => new Date(v).getTime();
const reqStart = ms(REQ.start_iso), reqEnd = ms(REQ.end_iso);
const exclude = String(REQ.exclude_event_id || '').trim();
const conflicts = [], unverifiable = [];

for (const ev of EVENTS) {
  if (!ev || !ev.id) continue;
  if (exclude && ev.id === exclude) continue;

  const evStart = ms(ev.start && (ev.start.dateTime || ev.start.date));
  const evEnd   = ms(ev.end   && (ev.end.dateTime   || ev.end.date));
  if (!(evStart < reqEnd && evEnd > reqStart)) continue;

  const evRooms = roomsOf(ev);
  if (!evRooms.length) {
    unverifiable.push({ summary: ev.summary || '(no title)',
      start: ev.start && (ev.start.dateTime || ev.start.date) });
    continue;
  }
  for (const w of wanted) {
    if (evRooms.indexOf(w.name) !== -1) {
      conflicts.push({ room: w.name, summary: ev.summary || '(no title)',
        start: ev.start && (ev.start.dateTime || ev.start.date),
        end: ev.end && (ev.end.dateTime || ev.end.date) });
      break;
    }
  }
}

if (conflicts.length) {
  const lines = conflicts.map(c => c.room + ' is taken by "' + c.summary + '"').join('; ');
  return [{ json: { verdict:'REJECTED', reason:'ROOM_OCCUPIED', conflicts,
    human: lines + '. Nothing was booked - tell the requester and offer 2-3 alternative slots.' } }];
}
if (unverifiable.length) {
  const names = unverifiable.map(u => '"' + u.summary + '"').join(', ');
  return [{ json: { verdict:'REJECTED', reason:'UNVERIFIABLE', unverifiable,
    human:'There is an event in that window I cannot identify a room for (' + names + '), so I could not '
        + 'confirm the room is free. Nothing was booked - ask the requester to check Google Calendar.' } }];
}
return [{ json: { verdict:'CLEAR' } }];
