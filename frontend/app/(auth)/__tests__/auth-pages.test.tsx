import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import LoginPage from "../login/page";
import RegisterPage from "../register/page";
import { api, ApiError } from "@/lib/api";

const push = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace: push }),
  usePathname: () => "/login",
  useSearchParams: () => new URLSearchParams(),
}));

afterEach(() => {
  vi.restoreAllMocks();
  push.mockClear();
  window.localStorage.clear();
});

describe("Login page", () => {
  it("lets any non-empty password through to the server (legacy short passwords must still sign in)", async () => {
    const login = vi.spyOn(api, "login").mockRejectedValue(new ApiError("Incorrect email or password", 401));
    render(<LoginPage />);
    await userEvent.type(screen.getByPlaceholderText("alex.morgan@university.edu"), "old@example.com");
    await userEvent.type(screen.getByPlaceholderText("••••••••"), "abc");
    await userEvent.click(screen.getByRole("button", { name: /Sign In to CareerOS/i }));
    await waitFor(() => expect(login).toHaveBeenCalledWith("old@example.com", "abc"));
    expect(await screen.findByText("Incorrect email or password")).toBeInTheDocument();
  });

  it("shows the server's throttling message", async () => {
    vi.spyOn(api, "login").mockRejectedValue(new ApiError("Too many failed login attempts. Please wait before trying again.", 429));
    render(<LoginPage />);
    await userEvent.type(screen.getByPlaceholderText("alex.morgan@university.edu"), "a@example.com");
    await userEvent.type(screen.getByPlaceholderText("••••••••"), "whatever1");
    await userEvent.click(screen.getByRole("button", { name: /Sign In to CareerOS/i }));
    expect(await screen.findByText(/Too many failed login attempts/)).toBeInTheDocument();
  });

  it("social sign-in buttons are inert, labelled as unavailable, and cannot submit the form", async () => {
    const login = vi.spyOn(api, "login");
    render(<LoginPage />);
    for (const name of ["Google", "GitHub", "Microsoft"]) {
      const b = screen.getByRole("button", { name: `${name} sign-in is not available yet` });
      expect(b).toBeDisabled();
      expect(b).toHaveAttribute("type", "button");
      await userEvent.click(b);
    }
    expect(login).not.toHaveBeenCalled();
  });
});

describe("Register page", () => {
  const fill = async (password: string) => {
    await userEvent.type(screen.getByPlaceholderText("Alex Morgan"), "Test Student");
    await userEvent.type(screen.getByPlaceholderText("alex.morgan@university.edu"), "new@example.com");
    const [pw, confirm] = screen.getAllByPlaceholderText("••••••••");
    await userEvent.type(pw, password);
    await userEvent.type(confirm, password);
    await userEvent.click(screen.getByRole("button", { name: /Create Account/i }));
  };

  it("rejects a 7-character password in the browser, before any request is sent", async () => {
    const register = vi.spyOn(api, "register");
    render(<RegisterPage />);
    await fill("short12");
    expect(await screen.findByText("Password must be at least 8 characters")).toBeInTheDocument();
    expect(register).not.toHaveBeenCalled();
  });

  it("sends an 8-character password to the server", async () => {
    const register = vi.spyOn(api, "register").mockRejectedValue(new ApiError("Email already registered", 400));
    render(<RegisterPage />);
    await fill("12345678");
    await waitFor(() => expect(register).toHaveBeenCalledWith("new@example.com", "12345678"));
    expect(await screen.findByText("Email already registered")).toBeInTheDocument();
  });
});
