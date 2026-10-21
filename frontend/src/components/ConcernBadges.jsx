const SEVERITY_COLOURS = {
  Mild: "bg-green-100 text-green-800",
  Moderate: "bg-yellow-100 text-yellow-800",
  Severe: "bg-red-100 text-red-800",
};

const CONCERN_DOT = {
  Acne: "text-blue-500",
  Redness: "text-red-500",
  Blemishes: "text-yellow-500",
};

/** One concern card: name, severity pill, count/area, confidence. */
function ConcernCard({ name, concern }) {
  const count = typeof concern.count === "number" ? `${concern.count} regions` : "—";

  return (
    <div className="rounded-lg border border-surface-border p-4">
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-2 font-medium text-slate-700">
          <span className={CONCERN_DOT[name]} aria-hidden="true">●</span>
          {name}
        </span>
        <span className={`rounded-full px-3 py-1 text-sm font-medium ${SEVERITY_COLOURS[concern.severity]}`}>
          {concern.severity}
        </span>
      </div>
      <p className="mt-2 text-sm text-slate-500">
        {count} · {concern.area_pct}% of skin area
      </p>
      <p className="text-sm text-slate-400">Confidence: {concern.confidence}</p>
    </div>
  );
}

/**
 * Severity pills for acne, redness and blemishes.
 * @param {object} concerns - { acne, redness, blemishes }
 */
function ConcernBadges({ concerns }) {
  const items = [
    { name: "Acne", concern: concerns.acne },
    { name: "Redness", concern: concerns.redness },
    { name: "Blemishes", concern: concerns.blemishes },
  ];

  return (
    <section className="rounded-xl border border-surface-border bg-white p-6">
      <h2 className="mb-4 text-lg font-semibold text-slate-800">Detected Concerns</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {items.map((item) => (
          <ConcernCard key={item.name} {...item} />
        ))}
      </div>
    </section>
  );
}

export default ConcernBadges;
