// Answers "what is free" with set arithmetic instead of asking the model to do it.
// Without this the agent called List Events ten times for one window and gave up
// on max iterations - it cannot reliably subtract busy rooms from all rooms.
// Model output occasionally carries invisible characters. On 2026-08-30 a
// variation selector (U+FE0F) glued to the end of an ISO timestamp made Room
// Availability answer BAD_WINDOW, and the model then presented a booking
// summary as though the room were free. Every string the model hands this
// workflow is scrubbed once, here, rather than at each place one is read.
// Tabs and newlines survive - a description is allowed to contain them.
const clean = s => String(s == null ? '' : s)
  .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F\u200B-\u200F\u2028\u2029\u202A-\u202E\u2060-\u2064\uFE00-\uFE0F\uFEFF]/g, '')
  .trim();
const REQ = (function (o) {
  const out = {};
  for (const k in o) out[k] = (typeof o[k] === 'string') ? clean(o[k]) : o[k];
  return out;
})($('When Executed by Another Workflow').first().json || {});

const ROOMS = {
  'Studio 1':'hitproductions.net_3737303833303637363538@resource.calendar.google.com',
  'Studio 2':'c_18871bprki2umhrkjc4qcaldse1f8@resource.calendar.google.com',
  'Studio 3':'c_1886me03bdcrki5bhu8vddknl472k@resource.calendar.google.com',
  'Studio 4':'c_188e94dapvbp8jvrjmuga6qbof826@resource.calendar.google.com',
  'Studio 5':'c_18889v3glj9cqiotg8j95jaqmdhmm@resource.calendar.google.com',
  'Studio 6':'c_18838qt2ru30ein7gcefjiarplkre@resource.calendar.google.com',
  'Studio 7':'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com',
  'Studio 8':'c_18863v8hd6f42isegdh9i30psuo9q@resource.calendar.google.com',
  'Studio A':'c_18843dclutqm6hl9nbeg002phapfu@resource.calendar.google.com',
  'Studio B':'c_1881vgb66tkpujjelnn3rniugd9pk@resource.calendar.google.com',
  'Studio C':'c_188797f37eu9ujs6ldpf3smn78joc@resource.calendar.google.com',
  'Studio D':'c_18801gc6ck77gho7jl0e1fug94u92@resource.calendar.google.com',
  'Studio E':'c_18807te03d2sqh0lmtal9sbb04gao@resource.calendar.google.com',
  'Studio F':'c_188em7d58podeju3i8q6juqlufkls@resource.calendar.google.com',
  'Studio M':'c_1885k4adm87fqjd2j3j2usqftph5c@resource.calendar.google.com',
  'M1':'c_1889v46vd62fkjk3i7r1hsfem7tcm@resource.calendar.google.com',
  'M2':'c_1883ui6lnfc9ogt2hrmg57a30n72q@resource.calendar.google.com',
  'M3':'c_188d7dkqgnfs6hu4iunlu5ogftct0@resource.calendar.google.com',
  'M4':'c_18869nhmsj2uki8mljoi48v1cj7l4@resource.calendar.google.com',
  'M5':'c_1889h30ci9noqjcbnoogad9qk75vq@resource.calendar.google.com',
  'M6':'c_188f9gnq0a9tehf4g9ja57l83c0ts@resource.calendar.google.com',
  'M7':'c_1880r9hhk9c2agpbko87o7fojosh0@resource.calendar.google.com',
  'M8':'c_1884cu2cc84iujsjnu03s21f0ct9q@resource.calendar.google.com',
  'Salin':'c_1887hh5rsv6q4gt8hnu6ered170lg@resource.calendar.google.com',
  'Katha':'c_1881169pcpn12gsnm6i7sc0gjk7gk@resource.calendar.google.com',
  'Likha':'c_1886t6cjgrq0ihgpime01uibcqsg6@resource.calendar.google.com',
  'Lobby':'c_188227mpeagjuhi7gqlgns1di14be@resource.calendar.google.com'
};
const keys = Object.keys(ROOMS);

const events = (function(){
  const out = [], seen = {};
  for (const it of $input.all()) {
    const j = (it && it.json) || {};
    const list = Array.isArray(j.items) ? j.items : (j && j.id ? [j] : []);
    for (const ev of list) if (ev && ev.id && !seen[ev.id]) { seen[ev.id] = 1; out.push(ev); }
  }
  return out;
})();

const ms = v => new Date(v).getTime();
const reqStart = ms(REQ.start_iso), reqEnd = ms(REQ.end_iso);
const nowShifted = new Date(Date.now() + 8 * 3600 * 1000);
const manilaMidnight = Date.UTC(nowShifted.getUTCFullYear(), nowShifted.getUTCMonth(),
                                nowShifted.getUTCDate()) - 8 * 3600 * 1000;
if (reqStart && reqStart < manilaMidnight) {
  return [{ json: { status:'PAST_DATE', window: { start: REQ.start_iso, end: REQ.end_iso },
    human: String(REQ.start_iso).slice(0, 10) + ' has already passed, so there is nothing to check. '
         + 'Tell the requester the date is in the past and ask for the right one.' } }];
}
if (!(reqStart && reqEnd) || reqEnd <= reqStart) {
  return [{ json: { status:'BAD_WINDOW',
    human:'I need a start and an end time to check availability. Ask the requester for the window. '
         + 'Nothing was checked, so do not present a booking summary and do not tell them a room is free.' } }];
}

const busy = {}, unidentified = [];
for (const ev of events) {
  const s0 = ms(ev.start && (ev.start.dateTime || ev.start.date));
  const e0 = ms(ev.end   && (ev.end.dateTime   || ev.end.date));
  if (!(s0 < reqEnd && e0 > reqStart)) continue;
  const emails = (ev.attendees || []).map(a => String(a.email || '').toLowerCase());
  const loc = String(ev.location || '').toLowerCase();
  const firstSeg = String(ev.summary || '').split(' - ')[0].trim().toLowerCase();
  let matched = false;
  for (const k of keys) {
    const lk = k.toLowerCase();
    if (emails.indexOf(ROOMS[k].toLowerCase()) !== -1 || (loc && loc.indexOf(lk) !== -1) || firstSeg === lk) {
      busy[k] = ev.summary || '(no title)'; matched = true;
    }
  }
  if (!matched) unidentified.push(ev.summary || '(no title)');
}

// Rooms and session types come from Room Table, which already read them this
// turn. Reading Airtable again here cost about 2.2 seconds per call.
const REF = (function(){
  try { return JSON.parse(String(REQ.reference_data || '') || '{}'); } catch (e) { return {}; }
})();
const refRooms = REF.rooms || [], refTypes = REF.types || [];
if (!refRooms.length) {
  return [{ json: { status:'NO_REFERENCE_DATA',
    human:'The room data did not reach the availability check, so nothing can be confirmed as free. '
        + 'Tell the requester it failed and to try again.' } }];
}
const nameOf = {}, active = {};
// `vocalBooth` arrives from Room Table, which reads the Airtable checkbox. Room
// Type is not a substitute: it marks Studio E as a Recording Booth, and E is the
// video and colour grading room. If the flag is missing from reference data -
// an older main workflow paired with this one - isBooth stays empty and every
// booth line below is simply omitted rather than guessed at.
const isBooth = {};
for (const r of refRooms) {
  nameOf[r.id] = r.name;
  active[r.name] = true;
  if (r.vocalBooth === true) isBooth[r.name] = true;
}
const boothNames = Object.keys(isBooth).sort();

const st = String(REQ.session_type || '').trim().toLowerCase();
let priority = [], lastResort = [];
for (const t of refTypes) {
  if (String(t.type || '').trim().toLowerCase() !== st) continue;
  priority   = [].concat(t.priority || []).map(i => nameOf[i]).filter(Boolean);
  lastResort = [].concat(t.last     || []).map(i => nameOf[i]).filter(Boolean);
}

const free = n => !busy[n];

// If they named a room, answer about THAT room. Without this the tool returns
// free priority rooms and the agent has to work out why the room they asked for
// is missing - it got that wrong and reported Studio 3 as busy when Studio 7 was.
const askedRaw = String(REQ.room || '').trim();
let askedAnswer = null;
if (askedRaw) {
  const hit = keys.find(k => k.toLowerCase() === askedRaw.toLowerCase());
  if (!hit) {
    askedAnswer = { room: askedRaw, status: 'UNKNOWN_ROOM',
      human: 'There is no room called "' + askedRaw + '".' };
  } else if (busy[hit]) {
    askedAnswer = { room: hit, status: 'BUSY', taken_by: busy[hit],
      human: hit + ' is taken in that window by "' + busy[hit] + '".' };
  } else if (st && (priority.length || lastResort.length)) {
    const inPri = priority.some(r => r.toLowerCase() === hit.toLowerCase());
    const inLast = lastResort.some(r => r.toLowerCase() === hit.toLowerCase());
    if (inPri) {
      askedAnswer = { room: hit, status: 'FREE', human: hit + ' is free in that window.' };
    } else if (inLast) {
      const freePri = priority.filter(free);
      askedAnswer = freePri.length
        ? { room: hit, status: 'FREE_BUT_LAST_RESORT', free_priority: freePri,
            human: hit + ' is free, but it is a last-resort room for ' + st + ' and these priority rooms are also free: '
                 + freePri.join(', ') + '. Offer one of those first; book ' + hit + ' only if they still want it.' }
        : { room: hit, status: 'FREE', human: hit + ' is free, and every priority room for ' + st + ' is taken, so it is the right choice.' };
    } else {
      askedAnswer = { room: hit, status: 'NOT_RUN_HERE', human: st + ' is not run in ' + hit + '.' };
    }
  } else {
    askedAnswer = { room: hit, status: 'FREE', human: hit + ' is free in that window.' };
  }
}
const out = { status:'OK', window: { start: REQ.start_iso, end: REQ.end_iso }, asked: askedAnswer,
  busy: Object.keys(busy).map(k => k + ' (' + busy[k] + ')') };

if (st && (priority.length || lastResort.length)) {
  out.session_type = st;
  out.free_priority    = priority.filter(free);
  out.free_last_resort = lastResort.filter(free);
  out.human = out.free_priority.length
    ? 'Free for ' + st + ': ' + out.free_priority.join(', ') + '. Offer one of these.'
    : (out.free_last_resort.length
       ? 'Every priority room is taken. Last-resort rooms free: ' + out.free_last_resort.join(', ') + '. Say that is why.'
       : 'Nothing that runs ' + st + ' is free in that window. Offer a different time.');
} else {
  out.free_rooms = Object.keys(active).filter(free).sort();
  out.human = out.free_rooms.length
    ? 'Free in that window: ' + out.free_rooms.join(', ') + '. List exactly these and no others.'
    : 'Nothing is free in that window.';
}
// Booth availability is computed here rather than left to the model to work out
// from the busy list - subtracting busy rooms from all rooms is exactly what it
// gets wrong (see the note at the top of this node). One call already covers
// every room, so this costs nothing extra.
if (boothNames.length) {
  out.vocal_booths = { free: boothNames.filter(free), busy: boothNames.filter(n => !free(n)) };
  out.human += out.vocal_booths.free.length
    ? ' Vocal booths free in that window: ' + out.vocal_booths.free.join(', ')
      + '. If a booth is being paired, these are the ones we normally use.'
    : ' No vocal booth is free in that window (' + boothNames.join(', ') + ' are all taken).';
}
if (askedAnswer) { out.human = askedAnswer.human + ' ' + out.human; }
if (unidentified.length) {
  out.unidentified = unidentified;
  out.human += ' Note: ' + unidentified.length + ' event(s) in that window have no identifiable room, so treat this as incomplete.';
}
return [{ json: out }];
