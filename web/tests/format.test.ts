import { describe, expect, it } from "vitest";
import { formatPostalCode, joinPhone, splitPhone, tidyPhone } from "../src/format";

describe("formatPostalCode", () => {
  it.each([
    ["01310200", "01310-200"],
    [" 01.310-200 ", "01310-200"],
    ["0131020", "0131020"],
    ["013102009", "013102009"],
  ])("shows %s as %s", (typed, shown) => {
    expect(formatPostalCode(typed)).toBe(shown);
  });
});

describe("splitPhone", () => {
  it.each([
    ["11999990000", { areaCode: "11", number: "99999-0000" }],
    ["1120000000", { areaCode: "11", number: "2000-0000" }],
    ["", { areaCode: "", number: "" }],
  ])("separates the area code of %s from its number", (saved, parts) => {
    expect(splitPhone(saved)).toEqual(parts);
  });
});

describe("tidyPhone", () => {
  it.each([
    [
      { areaCode: "(11)", number: "99999 0000" },
      { areaCode: "11", number: "99999-0000" },
    ],
    [
      { areaCode: "", number: "(91) 98888-7777" },
      { areaCode: "91", number: "98888-7777" },
    ],
    [
      { areaCode: "11", number: "9120000000" },
      { areaCode: "91", number: "2000-0000" },
    ],
    [
      { areaCode: "11", number: "9999-000" },
      { areaCode: "11", number: "9999000" },
    ],
    [
      { areaCode: "11", number: "5591988887777" },
      { areaCode: "11", number: "5591988887777" },
    ],
  ])("turns %o into %o", (typed, tidy) => {
    expect(tidyPhone(typed)).toEqual(tidy);
  });
});

describe("joinPhone", () => {
  it.each([
    [{ areaCode: "11", number: "99999-0000" }, "11999990000"],
    [{ areaCode: "11", number: "(11) 99999-0000" }, "11999990000"],
    [{ areaCode: "11", number: "" }, "11"],
    [{ areaCode: "", number: "9999-000" }, "9999000"],
    [{ areaCode: "", number: "" }, null],
  ])("sends %o as %s", (phone, sent) => {
    expect(joinPhone(phone)).toBe(sent);
  });
});
