import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it } from "vitest";
import { AuthProvider } from "../src/auth/AuthProvider";
import { ProtectedRoute } from "../src/auth/ProtectedRoute";
import type { Role } from "../src/types/user";
import { mockFetch, USER } from "./helpers";

function renderManagersOnlyPage(role: Role) {
  mockFetch({ "GET /api/profiles/me": { body: { ...USER, role } } });
  render(
    <MemoryRouter initialEntries={["/gestores"]}>
      <AuthProvider>
        <Routes>
          <Route element={<ProtectedRoute only="manager" />}>
            <Route path="/gestores" element={<p>Somente gestores</p>} />
          </Route>
          <Route path="/" element={<p>Painel</p>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute", () => {
  it("opens a restricted route for the role it is restricted to", async () => {
    renderManagersOnlyPage("manager");

    expect(await screen.findByText("Somente gestores")).toBeTruthy();
  });

  it("sends a user with another role to the dashboard", async () => {
    renderManagersOnlyPage("donor");

    expect(await screen.findByText("Painel")).toBeTruthy();
    expect(screen.queryByText("Somente gestores")).toBeNull();
  });
});
