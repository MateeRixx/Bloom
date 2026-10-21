import ConcernBadges from "./ConcernBadges.jsx";

/**
 * ProgressTrend — shows recent scan history from localStorage.
 * Simplified version: list of last 5 scans with severity badges.
 */
function ProgressTrend({ history }) {
  if (!history || history.length === 0) {
    return (
      <div className="mt-8 p-6 rounded-xl bg-slate-50 border border-surface-border text-center">
        <p className="text-slate-500">No previous scans yet.</p>
        <p className="text-xs text-slate-400 mt-1">Your scan history will appear here (stored locally in this browser).</p>
      </div>
    );
  }

  const formatDate = (iso) => {
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case "Clear": return "bg-green-100 text-green-700";
      case "Mild": return "bg-yellow-100 text-yellow-700";
      case "Moderate": return "bg-orange-100 text-orange-700";
      case "Severe": return "bg-red-100 text-red-700";
      default: return "bg-slate-100 text-slate-700";
    }
  };

  return (
    <div className="mt-8" aria-live="polite">
      <h3 className="text-xl font-semibold text-slate-800 mb-4">Progress History</h3>
      <div className="space-y-3">
        {history.slice(0, 5).map((scan, idx) => (
          <div key={idx} className="p-4 rounded-xl bg-white border border-surface-border hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-slate-600">{formatDate(scan.date)}</span>
              <span className="text-xs text-slate-400">Scan #{idx + 1}</span>
            </div>
            <ConcernBadges concerns={scan.concerns} compact />
            {scan.images?.improved_annotated && (
              <div className="mt-3">
                <img
                  src={`data:image/jpeg;base64,${scan.images.improved_annotated}`}
                  alt="Previous scan result"
                  className="w-full max-h-40 object-cover rounded-lg border border-surface-border"
                  loading="lazy"
                />
              </div>
            )}
          </div>
        ))}
      </div>
      <p className="mt-3 text-xs text-slate-400 text-center">History stored locally in this browser. Clears on cache clear.</p>
    </div>
  );
}

export default ProgressTrend;