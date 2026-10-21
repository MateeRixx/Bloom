import ComparisonGrid from "./ComparisonGrid.jsx";
import ConcernBadges from "./ConcernBadges.jsx";
import MetricsTable from "./MetricsTable.jsx";
import ResetButton from "./ResetButton.jsx";

/**
 * Composes the full results view from the API result.
 * @param {object} result - the success AnalysisResult
 * @param {function():void} onReset
 */
function ResultsPanel({ result, onReset }) {
  return (
    <div className="mt-8 space-y-6">
      <ComparisonGrid images={result.images} />
      <ConcernBadges concerns={result.concerns} />
      <MetricsTable metrics={result.metrics} />
      <ResetButton onReset={onReset} />
    </div>
  );
}

export default ResultsPanel;
