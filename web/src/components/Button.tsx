import type { ComponentProps } from "react";

export const BUTTON_CLASS =
  "inline-block rounded bg-emerald-700 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-50";

export function Button(props: Readonly<Omit<ComponentProps<"button">, "className">>) {
  return <button type="button" {...props} className={BUTTON_CLASS} />;
}
