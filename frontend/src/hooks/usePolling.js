import { useEffect, useRef } from "react";

export function usePolling(callback, enabled, intervalMs = 2200) {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled) {
      return undefined;
    }

    const interval = setInterval(() => {
      savedCallback.current();
    }, intervalMs);

    return () => clearInterval(interval);
  }, [enabled, intervalMs]);
}
