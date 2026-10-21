const TIPS = [
  "Face a window or natural light source",
  "Hold phone at arm's length",
  "Keep face centred and fully visible",
  "Avoid heavy filters or flash",
];

/**
 * Error / quality-gate failure view with guidance.
 * @param {string[]} issues - human-readable problem messages
 * @param {boolean} isQuality - true when the failure was a quality-gate rejection
 * @param {function():void} onReset
 */
function ErrorView({ issues, isQuality, onReset }) {
  return (
    <div className="mx-auto mt-16 max-w-md" role="alert">
      <div className="rounded-xl border border-red-200 bg-red-50 p-8">
        <div className="text-4xl text-red-400" aria-hidden="true">⚠</div>
        <h2 className="mt-4 text-lg font-medium text-red-900">We couldn't analyse this image</h2>

        {isQuality ? (
          <ul className="mt-3 space-y-1 text-sm text-red-700">
            {issues.map((issue) => (
              <li key={issue}>• {issue}</li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-red-700">
            {issues?.[0] || "Something went wrong. Please try again."}
          </p>
        )}

        {isQuality && (
          <div className="mt-4">
            <p className="text-sm font-medium text-slate-600">Tips for a better photo:</p>
            <ul className="mt-1 space-y-1 text-sm text-slate-500">
              {TIPS.map((tip) => (
                <li key={tip}>✓ {tip}</li>
              ))}
            </ul>
          </div>
        )}

        <button
          type="button"
          onClick={onReset}
          className="mt-6 w-full rounded-lg bg-brand-500 py-3 text-white hover:bg-brand-600 active:scale-95 focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          Try another image
        </button>
      </div>
    </div>
  );
}

export default ErrorView;
