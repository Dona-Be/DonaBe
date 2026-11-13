import { useId, type ComponentProps } from "react";

interface TextFieldProps extends Omit<ComponentProps<"input">, "className" | "id" | "required"> {
  label: string;
  optional?: boolean;
  hint?: string;
}

const INPUT_CLASS =
  "h-14 w-full rounded-lg border border-slate-500 px-4 focus:border-sky-700 focus:outline-1 " +
  "focus:outline-sky-700";

export function TextField({ label, optional, hint, ...inputProps }: Readonly<TextFieldProps>) {
  const id = useId();
  const hintId = `${id}-hint`;

  return (
    <div>
      <label htmlFor={id} className="mb-2 block font-bold">
        {label}
        {optional && <span className="font-normal"> (opcional)</span>}
      </label>
      <input
        {...inputProps}
        id={id}
        required={!optional}
        aria-describedby={hint ? hintId : undefined}
        className={INPUT_CLASS}
      />
      {hint && (
        <p id={hintId} className="mt-2 text-slate-600">
          {hint}
        </p>
      )}
    </div>
  );
}
