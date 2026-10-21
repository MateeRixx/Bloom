const ROWS = [
  ["IoU", "iou"],
  ["Dice", "dice"],
  ["Precision", "precision"],
  ["Recall", "recall"],
  ["F1-Score", "f1"],
];

/** Returns percentage delta string between baseline and improved values. */
function deltaPct(baselineValue, improvedValue) {
  if (!baselineValue) return "—";
  return `${(((improvedValue - baselineValue) / baselineValue) * 100).toFixed(1)}%`;
}

/**
 * Baseline vs improved metric comparison with deltas.
 * @param {object} metrics - { baseline: {...}, improved: {...} }
 */
function MetricsTable({ metrics }) {
  return (
    <section className="rounded-xl border border-surface-border bg-white p-6">
      <h2 className="text-lg font-semibold text-slate-800">Pipeline Comparison</h2>
      <p className="mb-4 text-sm text-slate-500">Baseline (naive) vs Improved (frequency-aware)</p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-subtle text-xs font-semibold uppercase text-slate-500">
              <th className="px-3 py-2 text-left">Metric</th>
              <th className="px-3 py-2 text-right">Baseline</th>
              <th className="px-3 py-2 text-right">Improved</th>
              <th className="px-3 py-2 text-right">Delta</th>
            </tr>
          </thead>
          <tbody>
            {ROWS.map(([label, key], i) => (
              <tr key={key} className={i % 2 === 1 ? "bg-surface-subtle" : ""}>
                <td className="px-3 py-2 text-slate-700">{label}</td>
                <td className="px-3 py-2 text-right font-mono text-slate-500">
                  {metrics.baseline[key].toFixed(2)}
                </td>
                <td className="px-3 py-2 text-right font-mono font-medium text-slate-900">
                  {metrics.improved[key].toFixed(2)}
                </td>
                <td className="px-3 py-2 text-right font-mono font-medium text-green-700">
                  {deltaPct(metrics.baseline[key], metrics.improved[key])} ▲
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default MetricsTable;
