import {
  InviteMemberPayload,
  Organization,
  OrganizationCreatePayload,
  OrganizationMember,
  OrganizationRole,
  OrganizationUpdatePayload,
} from "../types/organization";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

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
  const url = `${API_BASE_URL.replace(/\/$/, "")}/${endpoint.replace(/^\//, "")}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    let errorMessage = "Une erreur est survenue.";
    if (typeof data.detail === "string") {
      errorMessage = data.detail;
    } else if (typeof data.message === "string") {
      errorMessage = data.message;
    } else if (typeof data === "object" && data !== null) {
      const firstKey = Object.keys(data)[0];
      if (firstKey && Array.isArray(data[firstKey])) {
        errorMessage = `${firstKey}: ${data[firstKey].join(" ")}`;
      }
    }
    throw new Error(errorMessage);
  }

  return data as T;
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
    const url = `${API_BASE_URL.replace(/\/$/, "")}/organizations/${id}`;
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
    const url = `${API_BASE_URL.replace(/\/$/, "")}/organizations/${orgId}/members/${memberId}`;
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
