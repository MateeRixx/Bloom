import { useEffect, useState } from "react";
import ComparisonGrid from "./ComparisonGrid.jsx";
import ConcernBadges from "./ConcernBadges.jsx";
import RoutineCard from "./RoutineCard.jsx";
import ProgressTrend from "./ProgressTrend.jsx";
import ResetButton from "./ResetButton.jsx";
import { apiRequest } from "../api.js";

/**
 * Composes the full results view from the API result.
 * @param {object} result - the success AnalysisResult
 * @param {Array} history - localStorage scan history
 * @param {function():void} onReset
 */
function ResultsPanel({ result, history = [], onReset }) {
  const [routine, setRoutine] = useState(null);

  useEffect(() => {
    let cancelled = false;
    apiRequest("/api/routine", {
      method: "POST",
      body: JSON.stringify(result.concerns),
    })
      .then((data) => {
        if (!cancelled) setRoutine(data);
      })
      .catch(() => {
        if (!cancelled) setRoutine(null);
      });
    return () => { cancelled = true; };
  }, [result.concerns]);

  return (
    <div className="mt-8 space-y-6">
      <ComparisonGrid images={result.images} />
      <ConcernBadges concerns={result.concerns} />
      {routine && <RoutineCard routine={routine} />}
      <ProgressTrend history={history} />
      <p className="rounded-lg border border-surface-border bg-white px-4 py-3 text-sm text-slate-500">
        Detection results only. Accuracy metrics are available in the offline evaluation
        workflow, where both pipelines are scored against independent ground truth.
      </p>
      <ResetButton onReset={onReset} />
    </div>
  );
}

export default ResultsPanel;