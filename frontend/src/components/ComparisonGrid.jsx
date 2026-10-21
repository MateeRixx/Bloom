import { useState } from "react";

/** Single image tile with loading placeholder, fade-in and error fallback. */
function ImageCell({ label, src, highlight }) {
  const [status, setStatus] = useState("loading");

  return (
    <div
      className={`min-w-[70%] overflow-hidden rounded-lg bg-white md:min-w-0 ${
        highlight ? "border-2 border-brand-500" : "border border-surface-border"
      }`}
    >
      {status === "error" ? (
        <div className="flex aspect-square items-center justify-center bg-slate-100 text-xs text-slate-400">
          Image unavailable
        </div>
      ) : (
        <div className="relative aspect-square">
          {status === "loading" && <div className="absolute inset-0 animate-pulse bg-slate-100" />}
          <img
            src={src}
            alt={label}
            onLoad={() => setStatus("loaded")}
            onError={() => setStatus("error")}
            className={`h-full w-full object-cover transition-opacity duration-300 ${
              status === "loaded" ? "opacity-100" : "opacity-0"
            }`}
          />
        </div>
      )}
      <p className={`py-2 text-center text-xs ${highlight ? "font-medium text-brand-600" : "text-slate-500"}`}>
        {label}
      </p>
    </div>
  );
}

/**
 * Side-by-side comparison of the pipeline stages.
 * @param {object} images - base64 strings keyed by stage name
 */
function ComparisonGrid({ images }) {
  // backend base64 bhejta hai; browser <img> ke liye data-URI prefix chahiye
  const dataUri = (b64) => `data:image/jpeg;base64,${b64}`;
  const cells = [
    { label: "Original", src: dataUri(images.original) },
    { label: "Enhanced", src: dataUri(images.enhanced) },
    { label: "Skin Mask", src: dataUri(images.skin_mask) },
    { label: "Baseline Detection", src: dataUri(images.baseline_annotated) },
    { label: "Improved Detection ★", src: dataUri(images.improved_annotated), highlight: true },
  ];

  return (
    <section>
      <h2 className="mb-4 text-lg font-semibold text-slate-800">Analysis Results</h2>
      <div className="flex gap-4 overflow-x-auto pb-2 md:grid md:grid-cols-3 md:overflow-visible">
        {cells.map((cell) => (
          <ImageCell key={cell.label} {...cell} />
        ))}
      </div>
    </section>
  );
}

export default ComparisonGrid;
