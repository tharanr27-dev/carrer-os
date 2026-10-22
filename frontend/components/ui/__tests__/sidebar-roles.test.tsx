import React from "react";
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Sidebar } from "../sidebar";
import { useAuthStore, User, UserRole } from "@/store/useAuthStore";

vi.mock("next/navigation", () => ({
  usePathname: () => "/student",
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

const asRole = (role: UserRole) =>
  useAuthStore.setState({
    user: { id: "u1", name: "T", email: "t@example.com", role, permissions: [], companyId: null, collegeId: null, needsOrgSetup: false } as User,
    isAuthenticated: true,
  });

describe("Sidebar role-based navigation", () => {
  afterEach(() => useAuthStore.setState({ user: null, isAuthenticated: false }));

  it("students keep every existing link and gain Interview Prep", () => {
    asRole("student");
    render(<Sidebar />);
    for (const [name, href] of [["Dashboard", "/student"], ["Workspace", "/workspace"], ["Jobs", "/jobs"], ["Analytics", "/analytics"], ["Settings", "/settings"], ["Interview Prep", "/interview-prep"]]) {
      expect(screen.getAllByRole("link", { name: new RegExp(name) })[0]).toHaveAttribute("href", href);
    }
  });

  it.each<[UserRole, string]>([["recruiter", "/recruiter"], ["officer", "/officer"], ["admin", "/admin"]])(
    "%s sees its own dashboard link and no student-only Interview Prep link",
    (role, dash) => {
      asRole(role);
      render(<Sidebar />);
      expect(screen.getAllByRole("link", { name: /Dashboard/ })[0]).toHaveAttribute("href", dash);
      expect(screen.getAllByRole("link", { name: /Jobs/ })[0]).toHaveAttribute("href", "/jobs");
      expect(screen.queryByRole("link", { name: /Interview Prep/ })).toBeNull();
    }
  );

  it("renders nothing for a signed-out visitor", () => {
    const { container } = render(<Sidebar />);
    expect(container).toBeEmptyDOMElement();
  });
});
