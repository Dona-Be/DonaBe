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

const DATE_FORMAT = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short" });

export function formatDate(isoDate: string): string {
  return DATE_FORMAT.format(new Date(isoDate));
}
