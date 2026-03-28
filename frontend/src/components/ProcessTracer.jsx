import { motion } from "framer-motion";

import GlassCard from "./ui/GlassCard";
import { stageState } from "../utils/progressMapper";

const stages = [
  { key: "extracting_frames", label: "Extracting Frames" },
  { key: "generating_geometry", label: "Generating Geometry" },
  { key: "applying_pbr", label: "Applying PBR Textures" },
];

export default function ProcessTracer({ state }) {
  return (
    <GlassCard>
      <h2 className="font-display text-2xl font-semibold text-white">ProcessTracer</h2>
      <p className="mt-2 text-sm text-white/80">{state.message}</p>

      <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/15">
        <motion.div
          className="h-full bg-gradient-to-r from-cyan-300 to-blue-300"
          initial={{ width: 0 }}
          animate={{ width: `${state.progress}%` }}
          transition={{ type: "spring", damping: 20, stiffness: 120 }}
        />
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {stages.map((stage) => {
          const s = stageState(state.stage, stage.key);
          return (
            <div
              key={stage.key}
              className={[
                "rounded-xl border px-3 py-2 text-sm",
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
      {state.error && <p className="mt-3 text-sm text-rose-300">{state.error}</p>}
    </GlassCard>
  );
}
