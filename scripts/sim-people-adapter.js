// Slack Interactions v70 (6 Nov) made Engineer / Arranger multi-selects outside Localization. Older sims read those fields as single
// dropdowns (element.initial_option). This adapter gives a people multi-select with exactly one pick a (non-enumerable)
// initial_option too, so those checks still read the one person picked; nothing else changes and JSON output is untouched.
// What v70 changed on purpose (no "No engineer" option, empty = none) is checked in sim-several-engineers.js.
const IDS = new Set(['engineer_pick', 'arranger_pick', 'det_engineer_pick', 'det_arranger_pick']);
function adapt(x) {
  if (Array.isArray(x)) { x.forEach(adapt); return x; }
  if (x && typeof x === 'object') {
    if (x.type === 'multi_static_select' && IDS.has(x.action_id) && Array.isArray(x.initial_options) && x.initial_options.length === 1 && !('initial_option' in x))
      Object.defineProperty(x, 'initial_option', { value: x.initial_options[0], enumerable: false, configurable: true });
    for (const k of Object.keys(x)) adapt(x[k]);
  }
  return x;
}
module.exports = { adapt };
