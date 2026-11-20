"""The booking colour rule (PENDING 151, Howard 4 Nov) - one JS function, shared by the Book Session and Move builders.
JC is the current rule (Book Session v134 / Move v48: meetings and conference rooms Sage); JC_V1 the 4 Nov one (v127-v133 / v43-v47)."""
JC_V1 = r"""// v127 / Move v43 (PENDING 151, Howard 4 Nov): the calendar colour of a booking (Google event colorId). Localization Peacock (7, for
// cobalt), Audio Post Blueberry (9), Music Grape (3, for amethyst), M booths Basil (10), celebrity bookings Tomato (11); by booking
// type: Meeting Banana (5), Event Tangerine (6), Van Recording Flamingo (4), Post Processing Lavender (1); several departments Sage (2);
// no department or any other Graphite (8). New bookings and changes only - nothing is recoloured in bulk.
function __jColour(type, dept, rooms) {
  const t = String(type || '').trim().toLowerCase(), d = String(dept || '').trim().toLowerCase();
  const rs = [].concat(rooms || []).map(r => String(r).trim()).filter(Boolean);
  if (/celeb/.test(t)) return '11';
  if (t === '__booth' || /^m ?booth/.test(t) || (rs.length && rs.every(r => /^M[1-8]$/i.test(r)))) return '10';
  if (t === 'meeting') return '5';
  if (t === 'event') return '6';
  if (t === 'van recording') return '4';
  if (t === 'post processing' || t === 'multimedia post') return '1';
  if (/[,&\/+]|\band\b/.test(d)) return '2';
  if (/locali[sz]ation/.test(d)) return '7';
  if (/audio post|post production|^post$/.test(d)) return '9';
  if (/music/.test(d)) return '3';
  return '8';
}
"""

JC = r"""// v127 / Move v43 (PENDING 151, Howard 4 Nov): the calendar colour of a booking (Google event colorId). Localization Peacock (7, for
// cobalt), Audio Post Blueberry (9), Music Grape (3, for amethyst), M booths Basil (10), celebrity bookings Tomato (11); by booking
// type: Meeting Banana (5; Sage since Book Session v134 / Move v48), Event Tangerine (6), Van Recording Flamingo (4), Post Processing Lavender (1); several departments Sage (2);
// no department or any other Graphite (8). New bookings and changes only - nothing is recoloured in bulk.
// Book Session v134 / Move v48 (Howard, 20 Nov): meetings and bookings in a conference room (Salin, Katha, Likha as the main room) Sage (2).
function __jColour(type, dept, rooms) {
  const t = String(type || '').trim().toLowerCase(), d = String(dept || '').trim().toLowerCase();
  const rs = [].concat(rooms || []).map(r => String(r).trim()).filter(Boolean);
  if (/celeb/.test(t)) return '11';
  if (t === '__booth' || /^m ?booth/.test(t) || (rs.length && rs.every(r => /^M[1-8]$/i.test(r)))) return '10';
  if (t === 'meeting') return '2';   // v134 / v48: Sage (was Banana)
  if (t === 'event') return '6';
  if (rs.length && /^(?:salin|katha|likha)$/i.test(rs[0])) return '2';   // v134 / v48: a conference room booking - Sage
  if (t === 'van recording') return '4';
  if (t === 'post processing' || t === 'multimedia post') return '1';
  if (/[,&\/+]|\band\b/.test(d)) return '2';
  if (/locali[sz]ation/.test(d)) return '7';
  if (/audio post|post production|^post$/.test(d)) return '9';
  if (/music/.test(d)) return '3';
  return '8';
}
"""
