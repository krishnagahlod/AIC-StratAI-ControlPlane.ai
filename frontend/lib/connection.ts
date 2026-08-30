"use client";

import { useEffect, useState } from "react";

/**
 * Backend reachability, tracked in one place.
 *
 * Every page in this app polls on an interval and previously ended each call in
 * `.catch(console.error)` — so when the backend went away, the dashboard degraded
 * into a fully-styled, entirely empty product with no on-screen sign anything was
 * wrong. The console is invisible to anyone watching a screen recording.
 *
 * Rather than adding error handling to every caller, this hooks into the single
 * `request()` choke point in `api.ts`, so any page gets connectivity awareness for
 * free — including ones added later.
 */

export type ConnectionStatus = "connecting" | "online" | "offline";

// One transient failure is noise (a poll landing during a backend restart).
// Two consecutive failures is a real outage worth telling the user about.
const FAILURE_THRESHOLD = 2;

let consecutiveFailures = 0;
let status: ConnectionStatus = "connecting";
let lastErrorMessage: string | null = null;

const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

function setStatus(next: ConnectionStatus) {
  if (status === next) return;
  status = next;
  emit();
}

export function markSuccess() {
  consecutiveFailures = 0;
  lastErrorMessage = null;
  setStatus("online");
}

export function markFailure(message: string) {
  consecutiveFailures += 1;
  lastErrorMessage = message;
  if (consecutiveFailures >= FAILURE_THRESHOLD) setStatus("offline");
}

export function getConnectionState() {
  return { status, lastErrorMessage };
}

export function useConnection() {
  const [state, setState] = useState(getConnectionState);

  useEffect(() => {
    const listener = () => setState(getConnectionState());
    listeners.add(listener);
    listener();
    return () => {
      listeners.delete(listener);
    };
  }, []);

  return state;
}

/** True when a thrown error came from the network layer rather than the API itself. */
export function isNetworkError(error: unknown): boolean {
  return error instanceof TypeError || (error instanceof Error && error.name === "AbortError");
}
