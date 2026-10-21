import { useEffect, useState } from "react";

const STAGES = [
  "Enhancing image quality…",
  "Detecting skin region…",
  "Analysing frequency patterns…",
  "Identifying concerns…",
  "Computing metrics…",
];

// Tailwind width classes per stage (no inline styles); last stage caps below 100%.
const STAGE_WIDTHS = ["w-1/5", "w-2/5", "w-3/5", "w-4/5", "w-11/12"];

/**
 * Spinner + stage label + determinate progress bar shown while awaiting the API.
 */
function ProcessingView() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setIndex((prev) => Math.min(prev + 1, STAGES.length - 1));
    }, 1500);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="mx-auto mt-24 max-w-md text-center" aria-live="polite">
      <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
      <p className="mt-6 text-lg font-medium text-slate-700">Analysing your image…</p>
      <p className="mt-2 text-sm text-slate-500">{STAGES[index]}</p>

      <div
        className="mt-6 h-2 w-full overflow-hidden rounded-full bg-slate-200"
        role="progressbar"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow={index + 1}
        aria-valuetext={STAGES[index]}
      >
        <div className={`h-full rounded-full bg-brand-500 transition-all duration-1000 ease-out ${STAGE_WIDTHS[index]}`} />
      </div>
      <p className="mt-2 text-xs text-slate-400">Step {index + 1} of {STAGES.length}</p>
    </div>
  );
}

export default ProcessingView;
