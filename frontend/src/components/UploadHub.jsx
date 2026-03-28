import { Camera, Square, Upload } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import GlassCard from "./ui/GlassCard";
import { classifyFiles } from "../utils/fileValidation";

const viewSlots = ["front", "left", "back", "right"];

function defaultViewLabel(index) {
  return viewSlots[index] || "front";
}

export default function UploadHub({ onSubmit, disabled }) {
  const inputRef = useRef(null);
  const addImagesRef = useRef(null);
  const cameraCaptureRef = useRef(null);
  const videoRef = useRef(null);
  const [error, setError] = useState("");
  const [selection, setSelection] = useState(null);
  const [manualImages, setManualImages] = useState([]);
  const [viewLabels, setViewLabels] = useState({});
  const [capturedFiles, setCapturedFiles] = useState([]);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [cameraStream, setCameraStream] = useState(null);
  const [profile, setProfile] = useState("balanced");

  const processFiles = (fileList) => {
    const result = classifyFiles(fileList);
    if (!result.ok) {
      setSelection(null);
      setError(result.message);
      return;
    }
    setError("");
    setSelection(result);
  };

  const clearError = () => {
    if (error) {
      setError("");
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    clearError();
    processFiles(event.dataTransfer.files);
  };

  const handleInputChange = (event) => {
    clearError();
    processFiles(event.target.files);
    event.target.value = "";
  };

  const handleAddImages = (event) => {
    const picked = Array.from(event.target.files ?? []);
    if (picked.length === 0) {
      return;
    }

    const incoming = picked.filter((file) => file.type.startsWith("image/"));
    if (incoming.length === 0) {
      setError("Only image files are allowed for Add Images.");
      event.target.value = "";
      return;
    }

    const nextImages = [...manualImages, ...incoming];
    setManualImages(nextImages);
    setViewLabels((prev) => {
      const next = { ...prev };
      for (let i = 0; i < nextImages.length; i += 1) {
        const key = String(i);
        if (!next[key]) {
          next[key] = defaultViewLabel(i);
        }
      }
      return next;
    });
    processFiles(nextImages);
    event.target.value = "";
  };

  const handleCameraCaptureInput = (event) => {
    const picked = Array.from(event.target.files ?? []).filter((file) =>
      file.type.startsWith("image/")
    );
    if (picked.length === 0) {
      event.target.value = "";
      return;
    }

    const nextImages = [...manualImages, ...picked];
    setManualImages(nextImages);
    setCapturedFiles((prev) => [...prev, ...picked]);
    setViewLabels((prev) => {
      const next = { ...prev };
      for (let i = 0; i < nextImages.length; i += 1) {
        const key = String(i);
        if (!next[key]) {
          next[key] = defaultViewLabel(i);
        }
      }
      return next;
    });
    processFiles(nextImages);
    clearError();
    event.target.value = "";
  };

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
      setCameraStream(null);
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraOpen(false);
  };

  const startCamera = async () => {
    if (typeof navigator === "undefined") {
      setError("Camera is unavailable in this environment.");
      return;
    }

    const mediaDevices = navigator.mediaDevices;
    const hasLiveCamera = !!mediaDevices && typeof mediaDevices.getUserMedia === "function";

    if (!hasLiveCamera) {
      setError(
        "Live camera preview is not supported here. Opening direct camera capture instead."
      );
      cameraCaptureRef.current?.click();
      return;
    }

    if (!window.isSecureContext) {
      setError("Camera access requires HTTPS. Use the ngrok HTTPS URL on mobile.");
      cameraCaptureRef.current?.click();
      return;
    }

    try {
      const stream = await mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });
      setCameraStream(stream);
      setIsCameraOpen(true);
      setError("");
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (cameraError) {
      setError(cameraError?.message || "Unable to access camera.");
      cameraCaptureRef.current?.click();
    }
  };

  const captureFrame = async () => {
    if (!videoRef.current) {
      return;
    }

    const video = videoRef.current;
    if (!video.videoWidth || !video.videoHeight) {
      setError("Camera is not ready yet. Please wait a second and try again.");
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      setError("Could not capture frame.");
      return;
    }

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.95));
    if (!blob) {
      setError("Could not capture frame.");
      return;
    }

    const file = new File([blob], `capture-${Date.now()}.jpg`, { type: "image/jpeg" });
    setCapturedFiles((prev) => [...prev, file]);
    setManualImages((prev) => {
      const nextImages = [...prev, file];
      setViewLabels((existing) => {
        const next = { ...existing };
        for (let i = 0; i < nextImages.length; i += 1) {
          const key = String(i);
          if (!next[key]) {
            next[key] = defaultViewLabel(i);
          }
        }
        return next;
      });
      processFiles(nextImages);
      return nextImages;
    });

    clearError();
  };

  const resetCaptures = () => {
    setCapturedFiles([]);
    setManualImages([]);
    setViewLabels({});
    setSelection(null);
    setError("");
  };

  const updateViewLabel = (index, nextLabel) => {
    setViewLabels((prev) => ({ ...prev, [String(index)]: nextLabel }));
  };

  const preparedViewLabels = Object.fromEntries(
    Object.entries(viewLabels).filter(([, value]) => viewSlots.includes(value))
  );

  useEffect(() => {
    if (isCameraOpen && videoRef.current && cameraStream) {
      videoRef.current.srcObject = cameraStream;
    }
  }, [isCameraOpen, cameraStream]);

  useEffect(() => {
    return () => stopCamera();
  }, []);

  return (
    <GlassCard>
      <h2 className="font-display text-xl font-semibold text-white sm:text-2xl">UploadHub</h2>
      <p className="mt-2 text-xs text-white/80 sm:text-sm">
        Drop a 360 MP4, upload multi-view images, or capture views directly from your camera.
      </p>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="text-[11px] text-white/70 sm:text-xs">Runtime Profile</span>
        <select
          value={profile}
          onChange={(event) => setProfile(event.target.value)}
          className="rounded-lg border border-white/30 bg-black/40 px-2 py-1 text-[11px] text-white sm:text-xs"
        >
          <option value="balanced">Balanced (Recommended)</option>
          <option value="low_vram">Low VRAM</option>
          <option value="quality">Quality</option>
        </select>
      </div>

      <div
        onDrop={handleDrop}
        onDragOver={(event) => event.preventDefault()}
        className="mt-4 cursor-pointer rounded-xl border border-dashed border-white/30 bg-black/20 p-4 text-center sm:p-8"
      >
        <Upload className="mx-auto mb-2 h-7 w-7 text-cyan-200 sm:mb-3 sm:h-9 sm:w-9" />
        <p className="text-xs text-white/90 sm:text-sm">Drag and drop files here</p>
        <p className="mt-1 text-[11px] text-white/70 sm:text-xs">
          You can add images in multiple separate picks using Add Images below.
        </p>
        <div className="mt-3 flex flex-wrap items-center justify-center gap-2 sm:mt-4">
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="rounded-lg border border-white/30 bg-white/15 px-3 py-2 text-[11px] font-semibold text-white hover:bg-white/25 sm:text-xs"
          >
            Browse Media
          </button>
          <button
            type="button"
            onClick={() => addImagesRef.current?.click()}
            className="rounded-lg border border-cyan-300/60 bg-cyan-300/15 px-3 py-2 text-[11px] font-semibold text-cyan-100 hover:bg-cyan-300/25 sm:text-xs"
          >
            Add Images
          </button>
          {manualImages.length > 0 && (
            <span className="text-[11px] text-emerald-200 sm:text-xs">Image stack: {manualImages.length}</span>
          )}
        </div>
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept="video/mp4,image/png,image/jpeg,image/webp"
          multiple
          onChange={handleInputChange}
        />
        <input
          ref={addImagesRef}
          type="file"
          className="hidden"
          accept="image/png,image/jpeg,image/webp"
          multiple
          onChange={handleAddImages}
        />
        <input
          ref={cameraCaptureRef}
          type="file"
          className="hidden"
          accept="image/*"
          capture="environment"
          multiple
          onChange={handleCameraCaptureInput}
        />
      </div>
      {error && <p className="mt-3 text-xs text-rose-300 sm:text-sm">{error}</p>}
      <div className="mt-4 rounded-xl border border-white/20 bg-black/20 p-3">
        <div className="flex flex-wrap items-center gap-2">
          {!isCameraOpen ? (
            <button
              type="button"
              onClick={startCamera}
              disabled={disabled}
              className="inline-flex items-center gap-2 rounded-lg border border-white/30 bg-white/15 px-3 py-2 text-[11px] font-semibold text-white hover:bg-white/25 disabled:opacity-40 sm:text-xs"
            >
              <Camera className="h-4 w-4" /> Start Camera
            </button>
          ) : (
            <>
              <button
                type="button"
                onClick={captureFrame}
                disabled={disabled}
                className="inline-flex items-center gap-2 rounded-lg border border-cyan-300/60 bg-cyan-300/20 px-3 py-2 text-[11px] font-semibold text-cyan-100 hover:bg-cyan-300/30 disabled:opacity-40 sm:text-xs"
              >
                <Camera className="h-4 w-4" /> Capture View
              </button>
              <button
                type="button"
                onClick={stopCamera}
                className="inline-flex items-center gap-2 rounded-lg border border-white/30 bg-white/10 px-3 py-2 text-[11px] font-semibold text-white hover:bg-white/20 sm:text-xs"
              >
                <Square className="h-4 w-4" /> Stop Camera
              </button>
            </>
          )}
          {capturedFiles.length > 0 && (
            <button
              type="button"
              onClick={resetCaptures}
              className="rounded-lg border border-white/30 bg-white/10 px-3 py-2 text-[11px] font-semibold text-white hover:bg-white/20 sm:text-xs"
            >
              Reset Captures
            </button>
          )}
          <span className="text-[11px] text-white/70 sm:text-xs">Captured: {capturedFiles.length}</span>
        </div>

        {isCameraOpen && (
          <div className="mt-3 overflow-hidden rounded-lg border border-white/20 bg-black/50">
            <video ref={videoRef} autoPlay playsInline muted className="h-40 w-full object-cover sm:h-56" />
          </div>
        )}
      </div>

      {manualImages.length > 0 && (
        <div className="mt-4 rounded-xl border border-white/20 bg-black/20 p-3">
          <p className="text-[11px] text-white/75 sm:text-xs">Assign view labels for uploaded images</p>
          <div className="mt-2 grid gap-2">
            {manualImages.map((file, index) => (
              <div key={`${file.name}-${index}`} className="flex items-center gap-2">
                <span className="max-w-[50%] truncate text-[11px] text-white/75 sm:text-xs">{file.name}</span>
                <select
                  value={viewLabels[String(index)] || defaultViewLabel(index)}
                  onChange={(event) => updateViewLabel(index, event.target.value)}
                  className="rounded-lg border border-white/30 bg-black/40 px-2 py-1 text-[11px] text-white sm:text-xs"
                >
                  {viewSlots.map((slot) => (
                    <option key={slot} value={slot}>
                      {slot}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </div>
      )}

      {selection && (
        <p className="mt-3 text-xs text-emerald-200 sm:text-sm">
          Ready: {selection.mode} ({selection.files.length} file{selection.files.length > 1 ? "s" : ""})
        </p>
      )}
      <button
        type="button"
        disabled={!selection || disabled}
        onClick={() =>
          selection &&
          onSubmit({
            ...selection,
            profile,
            viewLabels: selection.mode === "images" ? preparedViewLabels : {},
          })
        }
        className="mt-4 w-full rounded-xl border border-white/30 bg-white/20 px-4 py-2 text-xs font-semibold text-white transition hover:bg-white/30 disabled:cursor-not-allowed disabled:opacity-40 sm:text-sm"
      >
        Launch Reconstruction
      </button>
    </GlassCard>
  );
}
