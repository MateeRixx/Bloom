import { useState } from "react";
import UploadZone from "./components/UploadZone.jsx";
import ProcessingView from "./components/ProcessingView.jsx";
import ResultsPanel from "./components/ResultsPanel.jsx";
import ErrorView from "./components/ErrorView.jsx";
import { analyseImage } from "./api.js";

const MAX_MB = 10;
const ALLOWED_TYPES = ["image/jpeg", "image/png"];

const INITIAL_STATE = {
  view: "upload",       // "upload" | "processing" | "results" | "error"
  selectedFile: null,
  previewUrl: null,
  result: null,
  errorMessage: null,
  fileError: null,
};

/**
 * Root component — owns all app state and controls which view is shown.
 */
function App() {
  const [state, setState] = useState(INITIAL_STATE);
  const update = (patch) => setState((prev) => ({ ...prev, ...patch }));

  const handleSelect = (file) => {
    // client-side validation (server re-checks)
    if (!ALLOWED_TYPES.includes(file.type)) {
      update({ fileError: "Please upload a JPEG or PNG image." });
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      update({ fileError: `Image is too large. Maximum size is ${MAX_MB}MB.` });
      return;
    }
    update({ selectedFile: file, previewUrl: URL.createObjectURL(file), fileError: null });
  };

  const handleClear = () => {
    if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
    update({ selectedFile: null, previewUrl: null, fileError: null });
  };

  const handleAnalyse = async () => {
    update({ view: "processing", errorMessage: null });
    const data = await analyseImage(state.selectedFile);

    if (data.status === "success") {
      update({ view: "results", result: data });
    } else if (data.status === "quality_error") {
      update({ view: "error", result: data, errorMessage: data.quality?.issues || [] });
    } else {
      update({ view: "error", result: data, errorMessage: [data.message || "Something went wrong."] });
    }
  };

  const handleReset = () => {
    if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
    setState(INITIAL_STATE);
  };

  return (
    <div className="min-h-screen bg-surface-subtle font-sans text-slate-800">
      <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-surface-border bg-white px-4 sm:px-8">
        <span className="text-xl font-semibold text-brand-700">Bloom</span>
        <span className="text-xs text-slate-400">Not medical advice</span>
      </header>

      <main className="mx-auto max-w-4xl px-4 pb-16 sm:px-8">
        {state.view === "upload" && (
          <UploadZone
            selectedFile={state.selectedFile}
            previewUrl={state.previewUrl}
            fileError={state.fileError}
            onSelect={handleSelect}
            onClear={handleClear}
            onAnalyse={handleAnalyse}
          />
        )}

        {state.view === "processing" && <ProcessingView />}

        {state.view === "results" && (
          <>
            {state.result.mediapipe_mode === "fallback" && (
              <p className="mt-6 rounded-lg border border-yellow-200 bg-yellow-50 px-4 py-2 text-sm text-yellow-800">
                No face detected — analysed the central region instead.
              </p>
            )}
            <ResultsPanel result={state.result} onReset={handleReset} />
          </>
        )}

        {state.view === "error" && (
          <ErrorView
            issues={state.errorMessage}
            isQuality={state.result?.status === "quality_error"}
            onReset={handleReset}
          />
        )}
      </main>

      <footer className="border-t border-surface-border py-8 text-center text-xs text-slate-400">
        Bloom is for educational purposes only and does not constitute medical advice. Consult a dermatologist for skin concerns.
      </footer>
    </div>
  );
}

export default App;
