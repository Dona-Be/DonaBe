import { causeLabels, causes, type Cause } from "../causes";
import { formatPostalCode, tidyPhone, type Phone } from "../format";
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
      onBlur={() => onChange(formatPostalCode(value))}
    />
  );
}

type PhoneFieldProps = Readonly<FieldProps<Phone> & { optional?: boolean }>;

export function PhoneField({ value, onChange, optional }: PhoneFieldProps) {
  const required = !optional || value.areaCode + value.number !== "";
  const tidy = () => onChange(tidyPhone(value));

  return (
    <div className="grid grid-cols-[5rem_1fr] gap-3">
      <TextField
        label="DDD"
        required={required}
        pattern="\d{2}"
        title="Dois dígitos"
        inputMode="numeric"
        autoComplete="tel-area-code"
        value={value.areaCode}
        onChange={(event) => onChange({ ...value, areaCode: event.target.value })}
        onBlur={tidy}
      />
      <TextField
        label="Telefone"
        optional={optional}
        required={required}
        hint="Só os números."
        inputMode="numeric"
        autoComplete="tel-local"
        value={value.number}
        onChange={(event) => onChange({ ...value, number: event.target.value })}
        onBlur={tidy}
      />
    </div>
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
