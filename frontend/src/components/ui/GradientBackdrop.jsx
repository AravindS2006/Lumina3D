import { motion } from "framer-motion";

export default function GradientBackdrop() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <motion.div
        className="mesh-bg absolute inset-0"
        animate={{ opacity: [0.8, 1, 0.85] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
      />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_8%,rgba(255,255,255,0.16),transparent_42%)]" />
    </div>
  );
}
