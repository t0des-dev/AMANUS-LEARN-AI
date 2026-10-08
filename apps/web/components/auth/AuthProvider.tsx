"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { authStorage } from "../../lib/authTokens";
import { authService } from "../../services/authService";
import {
  AuthContextType,
  LoginPayload,
  RegisterPayload,
  UserProfile,
  UserUpdatePayload,
} from "../../types/auth";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize and validate session on mount
  useEffect(() => {
    async function initAuth() {
      const tokens = authStorage.getTokens();
      const cached = authStorage.getCachedUser();

      if (tokens) {
        setToken(tokens.access);
      }

      if (cached) {
        setUser(cached);
      }

      if (!tokens) {
        setIsLoading(false);
        return;
      }

      try {
        const profile = await authService.getMe(tokens.access);
        setUser(profile);
        setToken(tokens.access);
        authStorage.setCachedUser(profile);
      } catch {
        // Try refreshing access token
        try {
          const { access } = await authService.refresh(tokens.refresh);
          authStorage.setAccessToken(access);
          setToken(access);
          const profile = await authService.getMe(access);
          setUser(profile);
          authStorage.setCachedUser(profile);
        } catch {
          // Token invalid or expired, clear session
          authStorage.clear();
          setUser(null);
          setToken(null);
        }
      } finally {
        setIsLoading(false);
      }
    }

    initAuth();
  }, []);

  const login = useCallback(async (payload: LoginPayload) => {
    setIsLoading(true);
    try {
      const response = await authService.login(payload);
      authStorage.setTokens({
        access: response.access,
        refresh: response.refresh,
      });
      authStorage.setCachedUser(response.user);
      setUser(response.user);
      setToken(response.access);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    setIsLoading(true);
    try {
      const response = await authService.register(payload);
      authStorage.setTokens({
        access: response.access,
        refresh: response.refresh,
      });
      authStorage.setCachedUser(response.user);
      setUser(response.user);
      setToken(response.access);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    const tokens = authStorage.getTokens();
    if (tokens?.refresh) {
      await authService.logout(tokens.refresh).catch(() => {});
    }
    authStorage.clear();
    setUser(null);
    setToken(null);
  }, []);

  const updateProfile = useCallback(
    async (data: UserUpdatePayload): Promise<UserProfile> => {
      const currentToken = token || authStorage.getAccessToken();
      if (!currentToken) throw new Error("Non authentifié");

      const updated = await authService.updateMe(currentToken, data);
      setUser(updated);
      authStorage.setCachedUser(updated);
      return updated;
    },
    [token]
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    return {
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      login: async () => {},
      register: async () => {},
      logout: async () => {},
      updateProfile: async () => null as any,
    };
  }
  return context;
}
