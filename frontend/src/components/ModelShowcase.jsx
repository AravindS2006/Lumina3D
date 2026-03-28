import GlassCard from "./ui/GlassCard";
import ModelViewer from "../three/ModelViewer";

export default function ModelShowcase({ downloadUrl, isReady }) {
  return (
    <GlassCard className="h-full">
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-display text-2xl font-semibold text-white">ModelShowcase</h2>
        {isReady && (
          <a
            href={downloadUrl}
            className="rounded-lg border border-white/30 bg-white/20 px-3 py-2 text-xs font-semibold text-white hover:bg-white/30"
          >
            Download GLB
          </a>
        )}
      </div>
      <div className="mt-4 h-[420px] overflow-hidden rounded-2xl border border-white/20 bg-black/30">
        <ModelViewer modelUrl={downloadUrl} />
      </div>
    </GlassCard>
  );
}
