import { cn } from "../../utils/cn";

export default function GlassCard({ className, children }) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-white/20 bg-white/10 p-5 shadow-glass backdrop-blur-md",
        className
      )}
    >
      {children}
    </div>
  );
}
