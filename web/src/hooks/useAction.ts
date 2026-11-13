import { useState } from "react";
import { friendlyMessage } from "../errors";

export function useAction() {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  function run(action: () => Promise<void>) {
    setErrorMessage(null);
    setPending(true);
    action()
      .catch((error: unknown) => setErrorMessage(friendlyMessage(error)))
      .finally(() => setPending(false));
  }

  return { errorMessage, setErrorMessage, pending, run };
}
