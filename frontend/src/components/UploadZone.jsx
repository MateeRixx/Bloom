import { useRef, useState } from "react";
import CameraCapture from "./CameraCapture.jsx";

/**
 * Drag-and-drop + file picker + live camera, with a preview of the selected image.
 * @param {File|null} selectedFile
 * @param {string|null} previewUrl
 * @param {function(File):void} onSelect
 * @param {function():void} onClear
 * @param {function():void} onAnalyse
 * @param {string|null} fileError
 */
function UploadZone({ selectedFile, previewUrl, onSelect, onClear, onAnalyse, fileError }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [cameraOn, setCameraOn] = useState(false);

  const handleDrop = (event) => {
    event.preventDefault();
    setDragOver(false);
    const file = event.dataTransfer.files?.[0];
    if (file) onSelect(file);
  };

  const handleCaptured = (file) => {
    setCameraOn(false);
    onSelect(file);
  };

  const sizeMb = selectedFile ? (selectedFile.size / (1024 * 1024)).toFixed(2) : null;

  return (
    <div className="mx-auto mt-16 max-w-md">
      <div
        onDragOver={(e) => { if (cameraOn) return; e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { if (cameraOn) return; handleDrop(e); }}
        className={`rounded-xl border-2 border-dashed p-12 text-center transition-colors ${
          dragOver ? "border-brand-500 bg-brand-50" : "border-surface-border bg-white hover:border-brand-500 hover:bg-brand-50"
        }`}
      >
        {cameraOn ? (
          <CameraCapture onCapture={handleCaptured} onCancel={() => setCameraOn(false)} />
        ) : !selectedFile ? (
          <>
            <div className="mb-4 text-5xl text-slate-300" aria-hidden="true">⬆</div>
            <p className="text-lg font-medium text-slate-700">Upload a skin photo</p>
            <p className="mt-1 text-sm text-slate-400">JPEG or PNG, up to 10MB</p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <button
                type="button"
                onClick={() => inputRef.current?.click()}
                className="rounded-lg bg-brand-500 px-6 py-2 text-white hover:bg-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                Choose file
              </button>
              <button
                type="button"
                onClick={() => setCameraOn(true)}
                className="rounded-lg border border-surface-border px-6 py-2 text-slate-600 hover:bg-surface-subtle focus:outline-none focus:ring-2 focus:ring-brand-500"
              >
                Take photo
              </button>
            </div>
            <p className="mt-3 text-sm text-slate-400">or drag and drop here</p>
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png"
              className="hidden"
              onChange={(e) => e.target.files?.[0] && onSelect(e.target.files[0])}
            />
          </>
        ) : (
          <>
            <img src={previewUrl} alt="Selected skin photo preview" className="mx-auto max-h-48 rounded-lg object-cover" />
            <p className="mt-4 text-sm text-slate-500">
              {selectedFile.name} · {sizeMb} MB
            </p>
            <button
              type="button"
              onClick={onAnalyse}
              className="mt-6 h-12 w-full rounded-lg bg-brand-500 text-white hover:bg-brand-600 active:scale-95 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              Analyse
            </button>
            <button
              type="button"
              onClick={onClear}
              className="mt-3 text-sm text-slate-400 underline hover:text-slate-600"
            >
              Remove
            </button>
          </>
        )}
      </div>
      {fileError && (
        <p role="alert" className="mt-4 text-center text-sm text-red-600">{fileError}</p>
      )}
    </div>
  );
}

export default UploadZone;
