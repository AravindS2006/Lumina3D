import { motion } from "framer-motion";

import GlassCard from "./ui/GlassCard";
import { stageState } from "../utils/progressMapper";

const stages = [
  { key: "waiting_gpu", label: "Waiting GPU Slot" },
  { key: "extracting_frames", label: "Extracting Frames" },
  { key: "loading_geometry", label: "Loading Geometry" },
  { key: "generating_geometry", label: "Generating Geometry" },
  { key: "cleanup_geometry", label: "VRAM Cleanup" },
  { key: "loading_texture", label: "Loading Texture" },
  { key: "applying_pbr", label: "Applying PBR" },
];

function profileBadge(profile) {
  if (profile === "quality") {
    return "Quality";
  }
  if (profile === "low_vram") {
    return "Low VRAM";
  }
  return "Balanced";
}

export default function ProcessTracer({ state }) {
  return (
    <GlassCard>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-display text-xl font-semibold text-white sm:text-2xl">ProcessTracer</h2>
        <span className="rounded-full border border-white/25 bg-white/10 px-3 py-1 text-[11px] font-semibold text-cyan-100 sm:text-xs">
          Profile: {profileBadge(state.profile)}
        </span>
      </div>

      <p className="mt-2 text-xs text-white/80 sm:text-sm">{state.message}</p>

      <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/15">
        <motion.div
          className="h-full bg-gradient-to-r from-cyan-300 to-blue-300"
          initial={{ width: 0 }}
          animate={{ width: `${state.progress}%` }}
          transition={{ type: "spring", damping: 20, stiffness: 120 }}
        />
      </div>

      <div className="mt-4 grid gap-2 sm:gap-3 md:grid-cols-3">
        {stages.map((stage) => {
          const s = stageState(state.stage, stage.key);
          return (
            <div
              key={stage.key}
              className={[
                "rounded-xl border px-3 py-2 text-xs sm:text-sm",
                s === "done" && "border-emerald-300/60 bg-emerald-300/20",
                s === "active" && "border-cyan-300/70 bg-cyan-300/20",
                s === "pending" && "border-white/20 bg-white/5",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              {stage.label}
            </div>
          );
        })}
      </div>

      {state.engineTier && (
        <p className="mt-3 text-[11px] text-emerald-200 sm:text-xs">Texture Tier: {state.engineTier}</p>
      )}

      {state.warnings?.length > 0 && (
        <div className="mt-3 rounded-lg border border-amber-300/30 bg-amber-300/10 px-3 py-2 text-[11px] text-amber-100 sm:text-xs">
          {state.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      )}

      {state.failureCode && (
        <p className="mt-3 text-[11px] text-rose-300 sm:text-xs">Failure Code: {state.failureCode}</p>
      )}

      {state.error && <p className="mt-2 text-xs text-rose-300 sm:text-sm">{state.error}</p>}

      <p className="mt-2 text-[11px] text-white/55 sm:text-xs">
        Tip: if you see 404, test the health endpoint on your API base URL and ensure the
        frontend was restarted after .env changes.
      </p>
    </GlassCard>
  );
}
