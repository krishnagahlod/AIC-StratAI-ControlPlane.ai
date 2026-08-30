"use client";

import { useEffect, useState } from "react";
import { Clapperboard, Check, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

/**
 * Re-arms the Human Review Queue before a recording take.
 *
 * The queue's real SLA windows are 30-120 seconds, which is correct product
 * behaviour and impossible to film — an item can expire between takes. This
 * re-opens the most recent human-review escalations with a 10-minute window.
 *
 * Renders only when the backend reports demo mode is on, so it cannot appear in a
 * screenshot of a normal instance and be mistaken for a fabricate-data button.
 */
export default function DemoControls() {
  const [enabled, setEnabled] = useState(false);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string | null>(null);

  useEffect(() => {
    api
      .demoStatus()
      .then((s) => setEnabled(s.demo_mode))
      .catch(() => setEnabled(false));
  }, []);

  if (!enabled) return null;

  async function arm() {
    setBusy(true);
    setDone(null);
    try {
      const res = await api.armReviewQueue();
      setDone(`${res.armed} item(s) armed · ${res.sla_seconds / 60} min`);
    } catch (e) {
      setDone(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
      setTimeout(() => setDone(null), 6000);
    }
  }

  return (
    <div className="mb-3">
      <button
        onClick={arm}
        disabled={busy}
        className="w-full inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-dashed border-border-strong
                   text-[11px] font-medium text-muted hover:text-foreground hover:bg-surface-2
                   transition-colors duration-150 disabled:opacity-50"
        title="Re-open recent review items with a 10-minute SLA so a recording take can't lose them"
      >
        {busy ? <Loader2 size={13} className="animate-spin shrink-0" /> : done ? <Check size={13} className="shrink-0" /> : <Clapperboard size={13} className="shrink-0" />}
        <span className="truncate">{done ?? "Arm review queue"}</span>
      </button>
    </div>
  );
}
