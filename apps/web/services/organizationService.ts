import {
  InviteMemberPayload,
  Organization,
  OrganizationCreatePayload,
  OrganizationMember,
  OrganizationRole,
  OrganizationUpdatePayload,
} from "../types/organization";

import { getApiBaseUrl, authedRequest } from "./apiClient";

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

async function orgFetch<T>(
  endpoint: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  return authedRequest<T>(endpoint, options, token, "Une erreur est survenue.");
}

export const organizationService = {
  async list(token: string): Promise<Organization[]> {
    const data = await orgFetch<PaginatedResponse<Organization> | Organization[]>(
      "organizations/",
      token
    );
    if ("results" in data && Array.isArray(data.results)) {
      return data.results;
    }
    return Array.isArray(data) ? data : [];
  },

  async create(
    token: string,
    payload: OrganizationCreatePayload
  ): Promise<Organization> {
    return orgFetch<Organization>("organizations/", token, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async get(token: string, id: string): Promise<Organization> {
    return orgFetch<Organization>(`organizations/${id}`, token);
  },

  async update(
    token: string,
    id: string,
    payload: OrganizationUpdatePayload
  ): Promise<Organization> {
    return orgFetch<Organization>(`organizations/${id}`, token, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  async delete(token: string, id: string): Promise<void> {
    const baseUrl = getApiBaseUrl();
    const url = `${baseUrl.replace(/\/$/, "")}/organizations/${id}`;
    const response = await fetch(url, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(
        data.detail || `Échec de suppression (code ${response.status})`
      );
    }
  },

  async listMembers(
    token: string,
    orgId: string
  ): Promise<OrganizationMember[]> {
    return orgFetch<OrganizationMember[]>(
      `organizations/${orgId}/members`,
      token
    );
  },

  async addMember(
    token: string,
    orgId: string,
    payload: InviteMemberPayload
  ): Promise<OrganizationMember> {
    return orgFetch<OrganizationMember>(
      `organizations/${orgId}/members`,
      token,
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  },

  async updateMemberRole(
    token: string,
    orgId: string,
    memberId: string,
    role: OrganizationRole
  ): Promise<OrganizationMember> {
    return orgFetch<OrganizationMember>(
      `organizations/${orgId}/members/${memberId}`,
      token,
      {
        method: "PATCH",
        body: JSON.stringify({ role }),
      }
    );
  },

  async removeMember(
    token: string,
    orgId: string,
    memberId: string
  ): Promise<void> {
    const baseUrl = getApiBaseUrl();
    const url = `${baseUrl.replace(/\/$/, "")}/organizations/${orgId}/members/${memberId}`;
    const response = await fetch(url, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(
        data.detail || `Échec de suppression du membre (${response.status})`
      );
    }
  },
};
