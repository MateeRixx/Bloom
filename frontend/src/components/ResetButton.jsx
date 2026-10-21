/**
 * Full-width button that clears results and returns to the upload view.
 * @param {function():void} onReset
 */
function ResetButton({ onReset }) {
  return (
    <button
      type="button"
      onClick={onReset}
      className="w-full rounded-lg border border-surface-border py-3 text-sm text-slate-600 hover:bg-surface-subtle focus:outline-none focus:ring-2 focus:ring-brand-500"
    >
      Analyse another image
    </button>
  );
}

export default ResetButton;
