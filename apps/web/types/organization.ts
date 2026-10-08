import { UserProfile } from "./auth";

export type OrganizationRole = "OWNER" | "ADMIN" | "TEACHER" | "STUDENT";
export type OrganizationPlan = "FREE" | "PRO" | "ENTERPRISE";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  logo?: string | null;
  plan: OrganizationPlan;
  user_role?: OrganizationRole | null;
  members_count: number;
  created_at: string;
  updated_at: string;
}

export interface OrganizationMember {
  id: string;
  organization: string;
  user: UserProfile;
  role: OrganizationRole;
  created_at: string;
}

export interface OrganizationCreatePayload {
  name: string;
  plan?: OrganizationPlan;
}

export interface OrganizationUpdatePayload {
  name?: string;
  plan?: OrganizationPlan;
}

export interface InviteMemberPayload {
  email: string;
  role: "ADMIN" | "TEACHER" | "STUDENT";
}

export interface OrganizationContextType {
  currentOrg: Organization | null;
  organizations: Organization[];
  isLoading: boolean;
  setCurrentOrg: (org: Organization | null) => void;
  refreshOrganizations: () => Promise<void>;
}
