// Slack Interactions v72 (6 Nov) put "+ Multiple studios" / "+ Multiple rooms" behind a tick ("Multiple studios"; ticked, the list opens).
// Older sims check the list itself. This adapter shows them the v71 shape: the tick replaced by the list (unticked: the list from the tick's
// value, nothing picked; ticked: the list that follows it), labelled "+ Multiple studios" / "+ Multiple rooms". The tick itself is checked
// in sim-several-engineers.js (v72 part).
const dec = x => /^S[0-9A-Z]$/.test(x) ? 'Studio ' + x.slice(1) : x;
function fix(blocks) {
  for (let i = blocks.length - 1; i >= 0; i--) {
    const b = blocks[i] || {}, id = String(b.block_id || '');
    if (id !== 'more_rooms_toggle' && id !== 'more_rooms_c_toggle') continue;
    const o = (((b.elements || [])[0] || {}).options || [])[0] || {}, meet = /^mm:/.test(String(o.value || ''));
    const label = { type: 'plain_text', text: meet ? '+ Multiple rooms' : '+ Multiple studios' };
    const next = blocks[i + 1] || {};
    if (/^(more_rooms|studios_c|rooms_c)$/.test(String(next.block_id || ''))) { next.label = label; blocks.splice(i, 1); continue; }
    const rooms = String(o.value || '').replace(/^m[mr]:/, '').split(',').filter(Boolean).map(dec);
    blocks[i] = { type: 'input', dispatch_action: true, block_id: id === 'more_rooms_toggle' ? 'more_rooms' : (meet ? 'rooms_c' : 'studios_c'), optional: true, label,
      element: { type: 'multi_static_select', action_id: id === 'more_rooms_toggle' ? 'more_rooms_pick' : 'more_c_pick',
        placeholder: { type: 'plain_text', text: meet ? 'Select more rooms' : 'Select more studios' }, options: rooms.map(n => ({ text: { type: 'plain_text', text: n }, value: n })) } };
  }
}
function adapt(x) {
  if (Array.isArray(x)) { x.forEach(adapt); return x; }
  if (x && typeof x === 'object') { if (Array.isArray(x.blocks)) fix(x.blocks); for (const k of Object.keys(x)) adapt(x[k]); }
  return x;
}
module.exports = { adapt };
