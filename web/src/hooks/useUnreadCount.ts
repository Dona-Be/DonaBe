import { useCallback, useEffect, useRef, useState } from "react";
import { countUnreadNotifications } from "../api/notifications";

// Notifications are rows the API writes when an intent changes, so the bell asks for the count
// now and then instead of keeping a socket open.
export const UNREAD_POLL_INTERVAL_MS = 30_000;

function pageIsVisible(): boolean {
  return document.visibilityState === "visible";
}

export function useUnreadCount() {
  const [count, setCount] = useState(0);
  // Each check and each local change takes a new version, so an answer that left before a
  // "mark as read" cannot bring the old count back.
  const version = useRef(0);

  const refresh = useCallback(() => {
    const requested = ++version.current;
    // A failed check keeps the last count; the next one tries again.
    countUnreadNotifications()
      .then((latest) => {
        if (requested === version.current) setCount(latest);
      })
      .catch(() => undefined);
  }, []);

  const changeCount = useCallback((change: (count: number) => number) => {
    version.current++;
    setCount(change);
  }, []);

  useEffect(() => {
    refresh();
    const refreshIfVisible = () => {
      if (pageIsVisible()) refresh();
    };
    const timer = setInterval(refreshIfVisible, UNREAD_POLL_INTERVAL_MS);
    document.addEventListener("visibilitychange", refreshIfVisible);
    return () => {
      clearInterval(timer);
      document.removeEventListener("visibilitychange", refreshIfVisible);
    };
  }, [refresh]);

  return { count, changeCount, refresh };
}
