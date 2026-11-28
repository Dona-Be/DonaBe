import { useEffect, useId, useRef } from "react";
import { PRIMARY_CLASS, SecondaryButton } from "./Button";
import { ErrorMessage } from "./ErrorMessage";

interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel: string;
  pending: boolean;
  errorMessage: string | null;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel,
  pending,
  errorMessage,
  onConfirm,
  onCancel,
}: Readonly<ConfirmDialogProps>) {
  const id = useId();
  const cancelRef = useRef<HTMLButtonElement>(null);
  const confirmRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const opener = document.activeElement;
    cancelRef.current?.focus();
    return () => {
      if (opener instanceof HTMLElement) opener.focus();
    };
  }, []);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !pending) onCancel();
      if (event.key !== "Tab") return;
      event.preventDefault();
      const next = event.target === cancelRef.current ? confirmRef : cancelRef;
      next.current?.focus();
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [pending, onCancel]);

  return (
    <div className="fixed inset-0 z-10 flex items-end justify-center bg-slate-900/40 p-4 sm:items-center">
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={`${id}-title`}
        aria-describedby={`${id}-message`}
        className="w-full max-w-md space-y-4 rounded-xl bg-white p-6 shadow-xl"
      >
        <h2 id={`${id}-title`} className="text-2xl font-extrabold">
          {title}
        </h2>
        <p id={`${id}-message`} className="text-slate-600 wrap-anywhere">
          {message}
        </p>
        {errorMessage && <ErrorMessage message={errorMessage} />}
        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <SecondaryButton ref={cancelRef} disabled={pending} onClick={onCancel}>
            Voltar
          </SecondaryButton>
          <button
            ref={confirmRef}
            type="button"
            disabled={pending}
            onClick={onConfirm}
            className={PRIMARY_CLASS}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
