import { useCallback, useEffect, useRef, useState } from "react";
import { countUnreadNotifications } from "../api/notifications";

export function useUnreadCount() {
  const [count, setCount] = useState(0);
  // Only the answer to the latest check may set the count.
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

  useEffect(refresh, [refresh]);

  return { count, refresh };
}
