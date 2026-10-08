"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { authStorage } from "../../lib/authTokens";
import { organizationService } from "../../services/organizationService";
import { Organization, OrganizationContextType } from "../../types/organization";
import { useAuth } from "../auth/AuthProvider";

const ACTIVE_ORG_KEY = "amanus_active_org_id";

const OrganizationContext = createContext<OrganizationContextType | undefined>(
  undefined
);

export function OrganizationProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated } = useAuth();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentOrg, setCurrentOrgState] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshOrganizations = useCallback(async () => {
    const token = authStorage.getAccessToken();
    if (!token || !isAuthenticated) {
      setOrganizations([]);
      setCurrentOrgState(null);
      setIsLoading(false);
      return;
    }

    try {
      const list = await organizationService.list(token);
      setOrganizations(list);

      const savedOrgId = typeof window !== "undefined" ? localStorage.getItem(ACTIVE_ORG_KEY) : null;
      const matched = list.find((org) => org.id === savedOrgId);

      if (matched) {
        setCurrentOrgState(matched);
      } else if (list.length > 0) {
        setCurrentOrgState(list[0]);
        if (typeof window !== "undefined") {
          localStorage.setItem(ACTIVE_ORG_KEY, list[0].id);
        }
      } else {
        setCurrentOrgState(null);
      }
    } catch {
      setOrganizations([]);
      setCurrentOrgState(null);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    refreshOrganizations();
  }, [refreshOrganizations]);

  const setCurrentOrg = (org: Organization | null) => {
    setCurrentOrgState(org);
    if (typeof window !== "undefined") {
      if (org) {
        localStorage.setItem(ACTIVE_ORG_KEY, org.id);
      } else {
        localStorage.removeItem(ACTIVE_ORG_KEY);
      }
    }
  };

  return (
    <OrganizationContext.Provider
      value={{
        currentOrg,
        organizations,
        isLoading,
        setCurrentOrg,
        refreshOrganizations,
      }}
    >
      {children}
    </OrganizationContext.Provider>
  );
}

export function useOrganization(): OrganizationContextType {
  const context = useContext(OrganizationContext);
  if (!context) {
    return {
      currentOrg: null,
      organizations: [],
      isLoading: false,
      setCurrentOrg: () => {},
      refreshOrganizations: async () => {},
    };
  }
  return context;
}
