"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Building2,
  PlusCircle,
  Users,
  Shield,
  Layers,
  ArrowRight,
  Loader2,
  X,
  AlertCircle,
} from "lucide-react";
import { ProtectedRoute } from "../../components/auth/ProtectedRoute";
import { useOrganization } from "../../components/organization/OrganizationContext";
import { authStorage } from "../../lib/authTokens";
import { organizationService } from "../../services/organizationService";
import { OrganizationPlan } from "../../types/organization";
import { useTranslation } from "../../lib/i18n/LanguageContext";

function OrganizationsContent() {
  const { t } = useTranslation();
  const router = useRouter();
  const { organizations, currentOrg, setCurrentOrg, refreshOrganizations, isLoading } =
    useOrganization();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newOrgName, setNewOrgName] = useState("");
  const [newOrgPlan, setNewOrgPlan] = useState<OrganizationPlan>("FREE");
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setIsCreating(true);

    const token = authStorage.getAccessToken();
    if (!token) return;

    try {
      const created = await organizationService.create(token, {
        name: newOrgName,
        plan: newOrgPlan,
      });
      await refreshOrganizations();
      setCurrentOrg(created);
      setIsModalOpen(false);
      setNewOrgName("");
      router.push(`/organizations/${created.id}`);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setCreateError(err.message);
      } else {
        setCreateError("Impossible de créer l'organisation.");
      }
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-8 border-b border-slate-800">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">
            {t("org.multiTenantTitle", "Organisations Multi-Tenant")}
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            {t("org.multiTenantSub", "Gérez vos espaces d'organisations, équipes pédagogiques et apprenants.")}
          </p>
        </div>

        <button
          type="button"
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition"
        >
          <PlusCircle className="h-4 w-4" />
          <span>{t("org.newOrg", "Nouvelle organisation")}</span>
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
        </div>
      ) : organizations.length === 0 ? (
        <div className="mt-12 rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 p-12 text-center">
          <Building2 className="mx-auto h-12 w-12 text-slate-600" />
          <h3 className="mt-4 text-base font-semibold text-white">
            {t("org.noOrgsTitle", "Aucune organisation trouvée")}
          </h3>
          <p className="mt-2 text-xs text-slate-400 max-w-sm mx-auto">
            {t("org.noOrgsDesc", "Vous ne faites actuellement partie d'aucune organisation. Créez votre première organisation pour commencer à collaborer.")}
          </p>
          <div className="mt-6">
            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white hover:bg-indigo-500 transition"
            >
              <PlusCircle className="h-4 w-4" />
              <span>{t("org.createFirst", "Créer une première organisation")}</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {organizations.map((org) => {
            const isCurrent = currentOrg?.id === org.id;
            return (
              <div
                key={org.id}
                className={`flex flex-col justify-between rounded-2xl border p-6 backdrop-blur-xl transition ${
                  isCurrent
                    ? "border-indigo-500/50 bg-slate-900/80 shadow-lg shadow-indigo-500/10"
                    : "border-slate-800 bg-slate-900/40 hover:border-slate-700 hover:bg-slate-900/60"
                }`}
              >
                <div>
                  <div className="flex items-start justify-between">
                    <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600/30 to-violet-500/20 text-indigo-400 border border-indigo-500/30 font-bold">
                      {org.name.slice(0, 2).toUpperCase()}
                    </div>
                    {org.user_role && (
                      <span className="rounded-md border border-slate-700 bg-slate-800/80 px-2 py-0.5 text-[10px] font-semibold text-slate-300 uppercase">
                        {org.user_role}
                      </span>
                    )}
                  </div>

                  <h3 className="mt-4 text-lg font-bold text-white truncate">
                    {org.name}
                  </h3>
                  <p className="text-xs text-slate-500 font-mono mt-0.5 truncate">
                    /{org.slug}
                  </p>

                  <div className="mt-4 flex items-center gap-4 text-xs text-slate-400">
                    <div className="flex items-center gap-1.5">
                      <Users className="h-3.5 w-3.5 text-slate-500" />
                      <span>{org.members_count || 1} membre(s)</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Layers className="h-3.5 w-3.5 text-slate-500" />
                      <span className="capitalize">{org.plan.toLowerCase()}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-6 flex items-center gap-2 pt-4 border-t border-slate-850">
                  <button
                    type="button"
                    onClick={() => {
                      setCurrentOrg(org);
                      router.push(`/organizations/${org.id}`);
                    }}
                    className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-xl bg-slate-800 py-2 text-xs font-semibold text-slate-200 hover:bg-indigo-600 hover:text-white transition"
                  >
                    <span>Ouvrir</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </button>

                  <Link
                    href={`/organizations/${org.id}`}
                    className="rounded-xl p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition"
                    title="Voir l'organisation"
                  >
                    <Building2 className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <h3 className="text-base font-semibold text-white">
                Créer une nouvelle organisation
              </h3>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {createError && (
              <div className="mt-4 flex items-center gap-2.5 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-300">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                <span>{createError}</span>
              </div>
            )}

            <form onSubmit={handleCreate} className="mt-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300">
                  Nom de l&apos;organisation
                </label>
                <input
                  type="text"
                  required
                  value={newOrgName}
                  onChange={(e) => setNewOrgName(e.target.value)}
                  placeholder="Ex : Faculté de Médecine ou Alpha Corp"
                  className="mt-1.5 w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300">
                  Formule
                </label>
                <select
                  value={newOrgPlan}
                  onChange={(e) =>
                    setNewOrgPlan(e.target.value as OrganizationPlan)
                  }
                  className="mt-1.5 w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-2 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="FREE">Gratuit (FREE)</option>
                  <option value="PRO">Professionnel (PRO)</option>
                  <option value="ENTERPRISE">Entreprise (ENTERPRISE)</option>
                </select>
              </div>

              <div className="mt-6 flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-xl px-4 py-2 text-xs font-medium text-slate-400 hover:bg-slate-800 hover:text-white"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={isCreating}
                  className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-600/30 hover:bg-indigo-500 disabled:opacity-50"
                >
                  {isCreating ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      <span>Création...</span>
                    </>
                  ) : (
                    <span>Créer l&apos;organisation</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default function OrganizationsPage() {
  return (
    <ProtectedRoute>
      <OrganizationsContent />
    </ProtectedRoute>
  );
}
