import type { ComponentProps } from "react";

type ButtonProps = Readonly<Omit<ComponentProps<"button">, "type">>;

const BUTTON_CLASS =
  "h-14 rounded-full px-6 font-bold focus-visible:outline-2 focus-visible:outline-offset-2 " +
  "focus-visible:outline-sky-700 disabled:cursor-not-allowed disabled:opacity-60 sm:px-8";
const PRIMARY_CLASS = `${BUTTON_CLASS} bg-sky-300 text-sky-950 hover:bg-sky-400`;
export const SECONDARY_CLASS = `${BUTTON_CLASS} border border-slate-500 bg-white hover:bg-slate-50`;

export function PrimaryButton({ className = "", ...props }: ButtonProps) {
  return <button type="submit" {...props} className={`${PRIMARY_CLASS} ${className}`} />;
}

export function SecondaryButton({ className = "", ...props }: ButtonProps) {
  return <button type="button" {...props} className={`${SECONDARY_CLASS} ${className}`} />;
}
