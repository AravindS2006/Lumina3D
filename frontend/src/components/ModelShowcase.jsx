import GlassCard from "./ui/GlassCard";
import ModelViewer from "../three/ModelViewer";

export default function ModelShowcase({ modelUrl, isReady, onDownload, message }) {
  return (
    <GlassCard className="h-full">
      <div className="flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-center sm:gap-3">
        <h2 className="font-display text-xl font-semibold text-white sm:text-2xl">ModelShowcase</h2>
        {isReady && (
          <button
            type="button"
            onClick={onDownload}
            className="w-full rounded-lg border border-white/30 bg-white/20 px-3 py-2 text-xs font-semibold text-white hover:bg-white/30 sm:w-auto"
          >
            Download GLB
          </button>
        )}
      </div>
      <p className="mt-2 text-[11px] text-white/70 sm:text-xs">
        {isReady
          ? "Previewing generated GLB from API response blob."
          : message || "Model preview appears here after pipeline completes."}
      </p>
      <div className="mt-4 h-[320px] overflow-hidden rounded-xl border border-white/20 bg-black/30 sm:h-[420px] sm:rounded-2xl">
        <ModelViewer modelUrl={modelUrl} />
      </div>
    </GlassCard>
  );
}
