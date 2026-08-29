"use client";

import { useEffect, useRef } from "react";

export function usePolling(callback: () => void, intervalMs: number, deps: unknown[] = []) {
  const savedCallback = useRef(callback);
  savedCallback.current = callback;

  useEffect(() => {
    savedCallback.current();
    const id = setInterval(() => savedCallback.current(), intervalMs);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
