export interface Phone {
  areaCode: string;
  number: string;
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

export function splitPhone(digits: string): Phone {
  return { areaCode: digits.slice(0, 2), number: formatPhoneNumber(digits.slice(2)) };
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
