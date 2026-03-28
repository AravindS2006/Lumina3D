import { Upload } from "lucide-react";
import { useRef, useState } from "react";

import GlassCard from "./ui/GlassCard";
import { classifyFiles } from "../utils/fileValidation";

export default function UploadHub({ onSubmit, disabled }) {
  const inputRef = useRef(null);
  const [error, setError] = useState("");
  const [selection, setSelection] = useState(null);

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

  const handleDrop = (event) => {
    event.preventDefault();
    processFiles(event.dataTransfer.files);
  };

  const handleInputChange = (event) => {
    processFiles(event.target.files);
  };

  return (
    <GlassCard>
      <h2 className="font-display text-2xl font-semibold text-white">UploadHub</h2>
      <p className="mt-2 text-sm text-white/80">
        Drop a 360 MP4 or multi-view image set to start the dual-engine reconstruction.
      </p>
      <div
        onDrop={handleDrop}
        onDragOver={(event) => event.preventDefault()}
        onClick={() => inputRef.current?.click()}
        className="mt-4 cursor-pointer rounded-xl border border-dashed border-white/30 bg-black/20 p-8 text-center"
      >
        <Upload className="mx-auto mb-3 h-9 w-9 text-cyan-200" />
        <p className="text-sm text-white/90">Drag and drop files here or click to browse</p>
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept="video/mp4,image/png,image/jpeg,image/webp"
          multiple
          onChange={handleInputChange}
        />
      </div>
      {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}
      {selection && (
        <p className="mt-3 text-sm text-emerald-200">
          Ready: {selection.mode} ({selection.files.length} file{selection.files.length > 1 ? "s" : ""})
        </p>
      )}
      <button
        type="button"
        disabled={!selection || disabled}
        onClick={() => selection && onSubmit(selection)}
        className="mt-4 w-full rounded-xl border border-white/30 bg-white/20 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/30 disabled:cursor-not-allowed disabled:opacity-40"
      >
        Launch Reconstruction
      </button>
    </GlassCard>
  );
}
