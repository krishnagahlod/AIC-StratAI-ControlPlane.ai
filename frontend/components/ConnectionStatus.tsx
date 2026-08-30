"use client";

import { AnimatePresence, motion } from "framer-motion";
import { WifiOff } from "lucide-react";
import { useConnection } from "@/lib/connection";

/**
 * Sidebar health dot. Deliberately visible in the healthy state too — an indicator
 * that only ever appears when something is broken teaches a viewer nothing about
 * what "normal" looks like.
 */
export function ConnectionDot() {
  const { status } = useConnection();
  const config = {
    online: { dot: "bg-emerald-500", text: "text-muted-2", label: "Backend connected" },
    connecting: { dot: "bg-slate-300", text: "text-muted-2", label: "Connecting…" },
    offline: { dot: "bg-amber-500 pulse-dot", text: "text-amber-700 font-medium", label: "Reconnecting…" },
  }[status];

  return (
    <div className="flex items-center gap-2 mb-2.5">
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${config.dot}`} />
      <span className={`text-[11px] ${config.text}`}>{config.label}</span>
    </div>
  );
}

/**
 * Global outage banner. Without this, killing the backend leaves the dashboard
 * looking like a working product that genuinely has no data — the worst possible
 * reading, and completely silent.
 */
export function ConnectionBanner() {
  const { status } = useConnection();

  return (
    <AnimatePresence>
      {status === "offline" && (
        <motion.div
          initial={{ opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={{ duration: 0.2 }}
          className="fixed top-4 right-5 z-50 flex items-center gap-2.5 px-4 py-2.5 rounded-xl max-w-[min(92vw,26rem)]
                     bg-amber-50 border border-amber-200 text-amber-800 text-sm font-medium
                     shadow-[0_8px_24px_-8px_rgba(10,0,17,0.18)]"
          role="status"
        >
          <WifiOff size={15} className="shrink-0" />
          <span>Backend unreachable — figures below may be stale. Retrying automatically…</span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
