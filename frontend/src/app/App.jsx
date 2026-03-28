import { motion } from "framer-motion";

import ModelShowcase from "../components/ModelShowcase";
import ProcessTracer from "../components/ProcessTracer";
import UploadHub from "../components/UploadHub";
import GradientBackdrop from "../components/ui/GradientBackdrop";
import { useGenerationJob } from "../hooks/useGenerationJob";

export default function App() {
  const { state, startJob, download } = useGenerationJob();
  const busy = ["queued", "running"].includes(state.phase) || state.stage === "waiting_gpu";

  return (
    <main className="relative min-h-screen overflow-hidden bg-shell px-3 py-4 text-white sm:px-6 sm:py-8 lg:px-8">
      <GradientBackdrop />
      <div className="relative mx-auto grid w-full max-w-7xl gap-4 sm:gap-6 lg:grid-cols-[1.05fr_1.35fr]">
        <motion.section
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="space-y-4 sm:space-y-6"
        >
          <div>
            <p className="font-display text-xs uppercase tracking-[0.24em] text-cyan-200/90 sm:text-sm sm:tracking-[0.32em]">
              Lumina3D
            </p>
            <h1 className="mt-2 max-w-lg font-display text-3xl font-bold leading-tight sm:mt-3 sm:text-5xl">
              Video-to-3D cinematic reconstruction with dual Hunyuan3D engines.
            </h1>
            <p className="mt-2 max-w-xl text-sm text-white/80 sm:mt-3 sm:text-base">
              Generate high-fidelity geometry and physically-based textures from a 360 video or
              multi-view images, optimized for constrained T4 VRAM.
            </p>
          </div>

          <UploadHub onSubmit={startJob} disabled={busy} />
          <ProcessTracer state={state} />
        </motion.section>

        <motion.section
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.12, duration: 0.65, ease: "easeOut" }}
          className="h-full"
        >
          <ModelShowcase
            modelUrl={state.modelUrl}
            isReady={state.phase === "complete"}
            onDownload={download}
            message={state.message}
          />
        </motion.section>
      </div>
    </main>
  );
}
