import { useEffect, useRef, useState } from "react";

/**
 * Live in-app camera: shows a video preview and snaps a frame into a JPEG File.
 * @param {function(File):void} onCapture
 * @param {function():void} onCancel
 */
function CameraCapture({ onCapture, onCancel }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    // camera stream ko component jindagi se bandho (unmount par tracks stop)
    navigator.mediaDevices
      ?.getUserMedia({ video: { facingMode: "user" }, audio: false })
      .then((stream) => {
        if (!active) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
      })
      .catch(() => setError("Could not access the camera. Check permissions."));

    return () => {
      active = false;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    };
  }, []);

  const handleCapture = () => {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return;
    // current frame ko canvas par draw karke JPEG File banao
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => blob && onCapture(new File([blob], "camera-capture.jpg", { type: "image/jpeg" })),
      "image/jpeg",
      0.92
    );
  };

  return (
    <div>
      {error ? (
        <p role="alert" className="mb-4 text-sm text-red-600">{error}</p>
      ) : (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="mx-auto max-h-64 w-full rounded-lg bg-black object-cover"
        />
      )}
      <div className="mt-4 flex gap-3">
        <button
          type="button"
          onClick={handleCapture}
          disabled={!!error}
          className="h-12 flex-1 rounded-lg bg-brand-500 text-white hover:bg-brand-600 active:scale-95 focus:outline-none focus:ring-2 focus:ring-brand-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Capture
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="h-12 rounded-lg border border-surface-border px-4 text-slate-600 hover:bg-surface-subtle focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

export default CameraCapture;
