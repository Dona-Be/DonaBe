import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DONOR, MANAGER, openProfile } from "./helpers";

describe("MyProfile", () => {
  it("shows the role, the e-mail and the photo, with no field to edit them", async () => {
    await openProfile(DONOR);

    expect(screen.getByText("Doador")).toBeTruthy();
    expect(screen.getByText("maria@exemplo.com")).toBeTruthy();
    expect(document.querySelector("img")?.getAttribute("src")).toBe(DONOR.picture_url);
    expect(screen.queryByDisplayValue("maria@exemplo.com")).toBeNull();
  });

  it("shows the role of a manager and no photo when the account has none", async () => {
    await openProfile(MANAGER);

    expect(screen.getByText("Gestor de instituição")).toBeTruthy();
    expect(document.querySelector("img")).toBeNull();
  });
});
