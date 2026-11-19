import { causeLabels, causes, type Cause } from "../causes";
import { TextField } from "./TextField";

interface FieldProps<Value> {
  value: Value;
  onChange: (value: Value) => void;
}

const CAUSE_CLASS =
  "cursor-pointer rounded-full border border-slate-500 px-4 py-2 has-checked:border-sky-700 " +
  "has-checked:bg-sky-100 has-checked:ring-1 has-checked:ring-sky-700 " +
  "has-focus-visible:outline-2 has-focus-visible:outline-offset-2 " +
  "has-focus-visible:outline-sky-700";

export function PostalCodeField({ value, onChange }: Readonly<FieldProps<string>>) {
  return (
    <TextField
      label="CEP"
      hint="Usamos o CEP para mostrar instituições perto de você."
      inputMode="numeric"
      autoComplete="postal-code"
      value={value}
      onChange={(event) => onChange(event.target.value)}
    />
  );
}

type PhoneFieldProps = Readonly<FieldProps<string> & { optional?: boolean }>;

export function PhoneField({ value, onChange, optional }: PhoneFieldProps) {
  return (
    <TextField
      label="Telefone"
      optional={optional}
      hint="Com DDD, por exemplo (11) 99999-0000."
      type="tel"
      autoComplete="tel-national"
      value={value}
      onChange={(event) => onChange(event.target.value)}
    />
  );
}

export function CausesField({ value, onChange }: Readonly<FieldProps<Cause[]>>) {
  function toggle(cause: Cause) {
    const others = value.filter((preferred) => preferred !== cause);
    onChange(others.length < value.length ? others : [...others, cause]);
  }

  return (
    <fieldset>
      <legend className="mb-2 font-bold">
        Causas preferidas<span className="font-normal"> (escolha quantas quiser)</span>
      </legend>
      <div className="flex flex-wrap gap-2">
        {causes.map((cause) => (
          <label key={cause} className={CAUSE_CLASS}>
            <input
              type="checkbox"
              className="sr-only"
              checked={value.includes(cause)}
              onChange={() => toggle(cause)}
            />
            {causeLabels[cause]}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
