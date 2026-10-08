"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Users,
  Shield,
  Trash2,
  UserPlus,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { authStorage } from "../../lib/authTokens";
import { organizationService } from "../../services/organizationService";
import {
  Organization,
  OrganizationMember,
  OrganizationRole,
} from "../../types/organization";
import { InviteMemberDialog } from "./InviteMemberDialog";

interface MemberListProps {
  organization: Organization;
}

export function MemberList({ organization }: MemberListProps) {
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [updatingMemberId, setUpdatingMemberId] = useState<string | null>(null);

  const canManage =
    organization.user_role === "OWNER" || organization.user_role === "ADMIN";

  const fetchMembers = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    const token = authStorage.getAccessToken();
    if (!token) return;

    try {
      const list = await organizationService.listMembers(token, organization.id);
      setMembers(list);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Impossible de charger les membres.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [organization.id]);

  useEffect(() => {
    fetchMembers();
  }, [fetchMembers]);

  const handleRoleChange = async (
    memberId: string,
    newRole: OrganizationRole
  ) => {
    const token = authStorage.getAccessToken();
    if (!token) return;

    setUpdatingMemberId(memberId);
    try {
      await organizationService.updateMemberRole(
        token,
        organization.id,
        memberId,
        newRole
      );
      await fetchMembers();
    } catch (err: unknown) {
      if (err instanceof Error) {
        alert(err.message);
      }
    } finally {
      setUpdatingMemberId(null);
    }
  };

  const handleRemoveMember = async (member: OrganizationMember) => {
    if (
      !confirm(
        `Êtes-vous sûr de vouloir retirer ${member.user.email} de l'organisation ?`
      )
    ) {
      return;
    }

    const token = authStorage.getAccessToken();
    if (!token) return;

    try {
      await organizationService.removeMember(
        token,
        organization.id,
        member.id
      );
      await fetchMembers();
    } catch (err: unknown) {
      if (err instanceof Error) {
        alert(err.message);
      }
    }
  };

  const getRoleBadge = (role: OrganizationRole) => {
    switch (role) {
      case "OWNER":
        return "bg-amber-500/10 text-amber-300 border-amber-500/30";
      case "ADMIN":
        return "bg-indigo-500/10 text-indigo-300 border-indigo-500/30";
      case "TEACHER":
        return "bg-emerald-500/10 text-emerald-300 border-emerald-500/30";
      case "STUDENT":
      default:
        return "bg-slate-500/10 text-slate-300 border-slate-500/30";
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-xl">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5 text-indigo-400" />
            <h3 className="text-base font-semibold text-white">
              Membres de l'organisation ({members.length})
            </h3>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Gérez les rôles et l'accès des collaborateurs et apprenants.
          </p>
        </div>

        {canManage && (
          <button
            type="button"
            onClick={() => setIsInviteOpen(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-600/30 hover:bg-indigo-500 transition"
          >
            <UserPlus className="h-3.5 w-3.5" />
            <span>Ajouter un membre</span>
          </button>
        )}
      </div>

      {error && (
        <div className="mt-4 flex items-center gap-2 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-300">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-indigo-500" />
        </div>
      ) : members.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-400">
          Aucun membre trouvé.
        </div>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="pb-3 font-medium">Utilisateur</th>
                <th className="pb-3 font-medium">Rôle</th>
                <th className="pb-3 font-medium hidden sm:table-cell">
                  Date d'adhésion
                </th>
                {canManage && <th className="pb-3 text-right font-medium">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-850">
              {members.map((member) => (
                <tr key={member.id} className="hover:bg-slate-900/40 transition">
                  <td className="py-3.5 pr-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 font-bold text-white text-xs">
                        {member.user.first_name && member.user.last_name
                          ? `${member.user.first_name[0]}${member.user.last_name[0]}`.toUpperCase()
                          : member.user.email.slice(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium text-white truncate max-w-[160px] sm:max-w-none">
                          {member.user.first_name && member.user.last_name
                            ? `${member.user.first_name} ${member.user.last_name}`
                            : member.user.email}
                        </p>
                        <p className="text-[11px] text-slate-400">{member.user.email}</p>
                      </div>
                    </div>
                  </td>

                  <td className="py-3.5 pr-4">
                    {canManage && member.role !== "OWNER" ? (
                      <select
                        disabled={updatingMemberId === member.id}
                        value={member.role}
                        onChange={(e) =>
                          handleRoleChange(
                            member.id,
                            e.target.value as OrganizationRole
                          )
                        }
                        className="rounded-lg border border-slate-800 bg-slate-950 px-2 py-1 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
                      >
                        <option value="ADMIN">ADMIN</option>
                        <option value="TEACHER">TEACHER</option>
                        <option value="STUDENT">STUDENT</option>
                      </select>
                    ) : (
                      <span
                        className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase ${getRoleBadge(
                          member.role
                        )}`}
                      >
                        {member.role}
                      </span>
                    )}
                  </td>

                  <td className="py-3.5 pr-4 text-slate-400 hidden sm:table-cell">
                    {new Date(member.created_at).toLocaleDateString()}
                  </td>

                  {canManage && (
                    <td className="py-3.5 text-right">
                      {member.role !== "OWNER" && (
                        <button
                          type="button"
                          onClick={() => handleRemoveMember(member)}
                          className="rounded-lg p-1.5 text-slate-500 hover:bg-rose-500/10 hover:text-rose-400 transition"
                          title="Retirer le membre"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <InviteMemberDialog
        organizationId={organization.id}
        isOpen={isInviteOpen}
        onClose={() => setIsInviteOpen(false)}
        onMemberAdded={fetchMembers}
      />
    </div>
  );
}
