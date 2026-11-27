export interface Phone {
  areaCode: string;
  number: string;
}

interface Address {
  street: string | null;
  number: string | null;
  complement: string | null;
  neighborhood: string | null;
  city: string;
  state: string;
  postal_code: string | null;
}

function onlyDigits(text: string): string {
  return text.replace(/\D/g, "");
}

function formatPhoneNumber(digits: string): string {
  return digits.replace(/^(\d{4,5})(\d{4})$/, "$1-$2");
}

export function formatPostalCode(text: string): string {
  return onlyDigits(text).replace(/^(\d{5})(\d{3})$/, "$1-$2");
}

export function formatAddress(address: Address): string {
  const { street, number, complement, neighborhood, city, state, postal_code } = address;
  const postalCode = formatPostalCode(postal_code ?? "");
  return [street, number, complement, neighborhood, city, state, postalCode]
    .filter(Boolean)
    .join(", ");
}

export function splitPhone(digits: string): Phone {
  return { areaCode: digits.slice(0, 2), number: formatPhoneNumber(digits.slice(2)) };
}

export function formatPhone(digits: string): string {
  const { areaCode, number } = splitPhone(digits);
  return `(${areaCode}) ${number}`;
}

export function tidyPhone(phone: Phone): Phone {
  const digits = onlyDigits(phone.number);
  // A whole phone in the number field brings its own area code.
  if (/^\d{10,11}$/.test(digits)) return splitPhone(digits);
  return { areaCode: onlyDigits(phone.areaCode), number: formatPhoneNumber(digits) };
}

export function joinPhone(phone: Phone): string | null {
  const { areaCode, number } = tidyPhone(phone);
  return onlyDigits(areaCode + number) || null;
}

const RELATIVE_TIME = new Intl.RelativeTimeFormat("pt-BR", { numeric: "auto" });
const DATE = new Intl.DateTimeFormat("pt-BR");
const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;
const DAYS_IN_WEEK = 7;

function midnight(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

export function formatRelativeTime(isoDate: string, now: Date = new Date()): string {
  const date = new Date(isoDate);
  const elapsed = Math.max(0, now.getTime() - date.getTime());
  if (elapsed < MINUTE) return "agora";
  if (elapsed < HOUR) return RELATIVE_TIME.format(-Math.floor(elapsed / MINUTE), "minute");
  if (elapsed < DAY) return RELATIVE_TIME.format(-Math.floor(elapsed / HOUR), "hour");
  const days = Math.round((midnight(now) - midnight(date)) / DAY);
  if (days < DAYS_IN_WEEK) return RELATIVE_TIME.format(-days, "day");
  return DATE.format(date);
}
