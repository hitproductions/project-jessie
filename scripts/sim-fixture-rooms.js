// The reference cache as Airtable had it on 15 Oct (Rooms & Studios, Session Types, three Bookers) - shared by the round 4 / 5 sims.
// ---- the reference cache: Rooms & Studios and Session Types as Airtable has them (15 Oct)
const R = (id, name, f) => ({ id, fields: Object.assign({ 'Room Name': name }, f || {}) });
const CR = { 'Room Type': ['Recording Control Room'] };
const rooms = [
  R('r1', 'Studio 1', Object.assign({ 'Paired with': 'Studio A, Can change using Dante' }, CR)),
  R('r2', 'Studio 2', Object.assign({ 'Paired with': 'Studio B, Can change using Dante' }, CR)),
  R('r3', 'Studio 3', Object.assign({ 'Paired with': 'Studio A, B, or D, Can change using Dante' }, CR)),
  R('r5', 'Studio 5', Object.assign({ 'Paired with': 'Studio A, B, or D, Can change using Dante' }, CR)),
  R('r6', 'Studio 6', Object.assign({ 'Paired with': 'Studio A, B, or D, Can change using Dante' }, CR)),
  R('r7', 'Studio 7', Object.assign({ 'Paired with': 'Studio A, B, or D, Can change using Dante', 'Records Vocals In-Room': true }, CR)),
  R('r8', 'Studio 8', Object.assign({ 'Records Vocals In-Room': true }, CR)),
  R('rf', 'Studio F', Object.assign({ 'Records Vocals In-Room': true }, CR)),
  R('rc', 'Studio C', Object.assign({ 'Records Vocals In-Room': true }, CR)),
  R('re', 'Studio E', { 'Room Type': ['Editing', 'Color Grading', 'Video Editing'], 'Paired with': 'Studio 7, Can change using Dante' }),
  R('ra', 'Studio A', { 'Room Type': ['Recording Booth'], 'Vocal Booth': true }),
  R('rb', 'Studio B', { 'Room Type': ['Recording Booth'], 'Vocal Booth': true }),
  R('rd', 'Studio D', { 'Room Type': ['Recording Booth', 'Editing'], 'Vocal Booth': true, 'Paired with': 'Studio 6, Can change using Dante', 'Records Vocals In-Room': true }),
  R('lk', 'Likha', { 'Room Type': ['Conference Room'] }), R('ka', 'Katha', { 'Room Type': ['Conference Room'] }), R('sa', 'Salin', { 'Room Type': ['Conference Room'] }),
  R('lo', 'Lobby', { 'Room Type': ['Lobby'] }), R('m1', 'M1', { 'Room Type': ['M Booth'] }), R('m2', 'M2', { 'Room Type': ['M Booth'] })];
const ST = (t, req, pri, last, role) => ({ id: 'st-' + t, fields: { Type: t, 'Room Requirements': req, Priority: pri, 'Last Resort': last || [], 'Engineer Role Required': role ? [role] : [] } });
const sessionTypes = [
  ST('Celebrity Recording', 'Large, pair with one or more conference room as holding areas', ['rf', 'lk', 'ka', 'sa', 'rc'], ['r7', 'r8'], 'Music Engineer'),
  ST('Localization Dubbing', 'Separate vocal booth', ['r1', 'ra', 'rb', 'r2', 'rd', 'r6'], ['re', 'r7'], 'Loc Engineer'),
  ST('QC', 'Medium to large', ['r3', 'r5', 'r7', 'm1'], ['r6'], 'Loc Engineer'),
  ST('Post Processing', 'Medium to large', ['re'], [], 'Multimedia Specialist'),
  ST('VO Recording', 'Stereo Mixing', ['r7', 'r8', 'rf', 'rc'], ['r5', 'r6'], 'Post Engineer'),
  ST('Music Mixing', 'Small to medium', ['rf'], ['rc', 'r7', 'r8'], 'Music Engineer'), ST('Meeting', 'Small to large', ['lk', 'sa', 'ka'])];
const bookers = [{ id: 'b1', fields: { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Post Engineer, Goes by Howard.' } },
  { id: 'b2', fields: { Name: 'Jetrho Ty', Initials: 'JT', 'Slack User ID': 'U3', Info: 'Loc Engineer, Goes by Jetrho.' } },
  { id: 'b3', fields: { Name: 'Dylan Diaz', Initials: 'DD', 'Slack User ID': 'U0BQ77XKWA3', Info: 'Multimedia Specialist, Goes by Dilan, Dylan, DD.' } }];
const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];
module.exports = { rooms, sessionTypes, bookers, cacheRow };
