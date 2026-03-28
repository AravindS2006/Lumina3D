import { cn } from "../../utils/cn";

export default function GlassCard({ className, children }) {
  return (
    <div
      className={cn(
        "rounded-xl border border-white/20 bg-white/10 p-4 shadow-glass backdrop-blur-md sm:rounded-2xl sm:p-5",
        className
      )}
    >
      {children}
    </div>
  );
}
