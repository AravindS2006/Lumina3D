import GlassCard from "./ui/GlassCard";
import ModelViewer from "../three/ModelViewer";

export default function ModelShowcase({ modelUrl, isReady, onDownload, message }) {
  return (
    <GlassCard className="h-full">
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-display text-2xl font-semibold text-white">ModelShowcase</h2>
        {isReady && (
          <button
            type="button"
            onClick={onDownload}
            className="rounded-lg border border-white/30 bg-white/20 px-3 py-2 text-xs font-semibold text-white hover:bg-white/30"
          >
            Download GLB
          </button>
        )}
      </div>
      <p className="mt-2 text-xs text-white/70">
        {isReady
          ? "Previewing generated GLB from API response blob."
          : message || "Model preview appears here after pipeline completes."}
      </p>
      <div className="mt-4 h-[420px] overflow-hidden rounded-2xl border border-white/20 bg-black/30">
        <ModelViewer modelUrl={modelUrl} />
      </div>
    </GlassCard>
  );
}
