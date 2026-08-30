"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Timer } from "lucide-react";
import { api } from "@/lib/api";
import { usePolling } from "@/lib/hooks";
import { decisionLabel, formatRelativeTime } from "@/lib/format";
import { Badge, Button, Card, FlagList, PageHeader, SectionLabel } from "@/components/ui";
import ModelOutput from "@/components/ModelOutput";
import type { ReviewQueueItem } from "@/lib/types";

type QueueItemWithDeadline = ReviewQueueItem & { deadlineMs: number | null };

function Countdown({ deadlineMs }: { deadlineMs: number | null }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  if (deadlineMs == null) return null;
  const remaining = Math.max(0, Math.round((deadlineMs - now) / 1000));
  const urgent = remaining <= 15;
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-mono ${urgent ? "text-rose-600" : "text-amber-700"}`}>
      <Timer size={12} className={urgent ? "pulse-dot" : ""} />
      {remaining > 0 ? `${remaining}s until safe default` : "SLA expired — safe default applying"}
    </span>
  );
}

export default function ReviewQueuePage() {
  const [items, setItems] = useState<QueueItemWithDeadline[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editText, setEditText] = useState("");

  function refresh() {
    const fetchedAt = Date.now();
    api
      .listReviewQueue()
      .then((rows) =>
        setItems(
          rows.map((r) => ({
            ...r,
            deadlineMs: r.seconds_remaining != null ? fetchedAt + r.seconds_remaining * 1000 : null,
          }))
        )
      )
      .catch(console.error);
  }

  usePolling(refresh, 5000);

  const pending = items.filter((i) => i.status === "pending");
  const resolved = items.filter((i) => i.status !== "pending");

  async function act(id: number, action: "approve" | "reject" | "edit") {
    if (action === "edit") {
      const item = items.find((i) => i.id === id);
      setEditingId(id);
      setEditText(item?.response ?? "");
      return;
    }
    await api.decideReview(id, action);
    refresh();
  }

  async function submitEdit(id: number) {
    await api.decideReview(id, "edit", "reviewer-edited response", editText);
    setEditingId(null);
    refresh();
  }

  return (
    <div>
      <PageHeader
        title="Human Review Queue"
        description="Confidence-based escalation, not binary block/allow — flagged responses wait here for a human decision before the SLA-timed safe default kicks in."
      />

      <div className="mb-8">
        <SectionLabel>Awaiting Decision ({pending.length})</SectionLabel>
        {pending.length === 0 && (
          <Card>
            <div className="text-sm text-muted-2">Nothing pending review right now — send a live risky prompt from Try It Live to populate this queue.</div>
          </Card>
        )}
        <AnimatePresence initial={false}>
          <div className="space-y-4">
            {pending.map((item) => (
              <motion.div
                key={item.id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.25 }}
              >
                <Card>
                  <div className="flex items-start justify-between gap-4 mb-3">
                    <div>
                      <div className="text-xs text-muted-2">{item.app_name}</div>
                      <div className="text-sm font-medium mt-0.5">{item.prompt}</div>
                    </div>
                    <div className="text-right shrink-0">
                      <Badge
                        className={
                          item.decision === "auto_block_alert"
                            ? "text-rose-600 bg-rose-50 border-rose-200"
                            : "text-amber-700 bg-amber-50 border-amber-200"
                        }
                      >
                        {decisionLabel(item.decision)}
                      </Badge>
                      <div className="mt-1.5">
                        <Countdown deadlineMs={item.deadlineMs} />
                      </div>
                    </div>
                  </div>
                  <div className="text-sm bg-surface-2 rounded-xl p-3 mb-3 max-h-56 overflow-y-auto">
                    <ModelOutput text={item.response ?? ""} />
                  </div>
                  <div className="mb-3">
                    <FlagList flags={item.flags} />
                  </div>
                  {editingId === item.id ? (
                    <div className="space-y-2">
                      <textarea
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        rows={3}
                        className="w-full bg-surface-2 border border-border rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-accent/50"
                      />
                      <div className="flex gap-2">
                        <Button onClick={() => submitEdit(item.id)}>Save edited response</Button>
                        <Button variant="ghost" onClick={() => setEditingId(null)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex gap-2">
                      <Button onClick={() => act(item.id, "approve")}>Approve</Button>
                      <Button variant="secondary" onClick={() => act(item.id, "edit")}>
                        Edit & Approve
                      </Button>
                      <Button variant="danger" onClick={() => act(item.id, "reject")}>
                        Reject
                      </Button>
                    </div>
                  )}
                </Card>
              </motion.div>
            ))}
          </div>
        </AnimatePresence>
      </div>

      <div>
        <SectionLabel>Recently Resolved ({resolved.length})</SectionLabel>
        <Card className="p-0 overflow-hidden">
          <div className="max-h-96 overflow-y-auto divide-y divide-border">
            {resolved.map((item) => (
              <div key={item.id} className="p-3.5 flex items-center justify-between text-sm">
                <div className="min-w-0">
                  <div className="truncate">{item.prompt}</div>
                  <div className="text-xs text-muted-2">{item.app_name}</div>
                </div>
                <div className="text-right shrink-0 ml-3">
                  <Badge className="text-muted bg-surface-2 border-border">{item.status.replace(/_/g, " ")}</Badge>
                  <div className="text-xs text-muted-2 mt-0.5">{formatRelativeTime(item.created_at)}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
