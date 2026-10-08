import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProtectedRoute } from "../components/auth/ProtectedRoute";
import { authStorage } from "../lib/authTokens";
import * as AuthProviderModule from "../components/auth/AuthProvider";

// Mock router
const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: pushMock,
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  useParams: () => ({ id: "1" }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/test",
}));

describe("Authentication & ProtectedRoute", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it("stores, retrieves, and clears auth tokens in localStorage", () => {
    const tokens = { access: "access-token-123", refresh: "refresh-token-456" };
    authStorage.setTokens(tokens);

    expect(authStorage.getTokens()).toEqual(tokens);
    expect(authStorage.getAccessToken()).toBe("access-token-123");

    authStorage.clear();
    expect(authStorage.getTokens()).toBeNull();
    expect(authStorage.getAccessToken()).toBeNull();
  });

  it("renders loader when session verification is in progress", () => {
    vi.spyOn(AuthProviderModule, "useAuth").mockReturnValue({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: true,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: vi.fn(),
    });

    render(
      <ProtectedRoute>
        <div>Private Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText("Vérification de la session...")).toBeInTheDocument();
    expect(screen.queryByText("Private Content")).not.toBeInTheDocument();
  });

  it("redirects unauthenticated users to /login", () => {
    vi.spyOn(AuthProviderModule, "useAuth").mockReturnValue({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: vi.fn(),
    });

    render(
      <ProtectedRoute>
        <div>Private Content</div>
      </ProtectedRoute>
    );

    expect(pushMock).toHaveBeenCalledWith("/login");
    expect(screen.queryByText("Private Content")).not.toBeInTheDocument();
  });

  it("renders protected content when user is authenticated", () => {
    vi.spyOn(AuthProviderModule, "useAuth").mockReturnValue({
      user: {
        id: "u-1",
        email: "alice@amanus.ai",
        first_name: "Alice",
        last_name: "Dupont",
        language: "fr",
        is_active: true,
        created_at: "2026-01-01",
        updated_at: "2026-01-01",
      },
      token: "valid-token",
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      updateProfile: vi.fn(),
    });

    render(
      <ProtectedRoute>
        <div>Welcome Alice! Protected Area</div>
      </ProtectedRoute>
    );

    expect(screen.getByText("Welcome Alice! Protected Area")).toBeInTheDocument();
    expect(pushMock).not.toHaveBeenCalled();
  });
});
