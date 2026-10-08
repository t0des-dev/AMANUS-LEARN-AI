"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  Building2,
  Users,
  Settings,
  Shield,
  Layers,
  ArrowLeft,
  Loader2,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { ProtectedRoute } from "../../../components/auth/ProtectedRoute";
import { MemberList } from "../../../features/organization/MemberList";
import { authStorage } from "../../../lib/authTokens";
import { organizationService } from "../../../services/organizationService";
import { Organization } from "../../../types/organization";
import { useOrganization } from "../../../components/organization/OrganizationContext";

function OrganizationDetailContent() {
  const params = useParams();
  const router = useRouter();
  const orgId = params?.id as string;
  const { setCurrentOrg, currentOrg } = useOrganization();

  const [organization, setOrganization] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOrganization = useCallback(async () => {
    if (!orgId) return;
    setIsLoading(true);
    setError(null);

    const token = authStorage.getAccessToken();
    if (!token) return;

    try {
      const data = await organizationService.get(token, orgId);
      setOrganization(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Impossible de charger les détails de l'organisation.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    fetchOrganization();
  }, [fetchOrganization]);

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
      </div>
    );
  }

  if (error || !organization) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-12">
        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-6 text-center">
          <AlertCircle className="mx-auto h-8 w-8 text-rose-400" />
          <h3 className="mt-3 text-base font-semibold text-white">Accès refusé ou introuvable</h3>
          <p className="mt-2 text-xs text-rose-300">
            {error || "Cette organisation n'existe pas ou vous n'en êtes pas membre."}
          </p>
          <div className="mt-6">
            <Link
              href="/organizations"
              className="inline-flex items-center gap-2 rounded-xl bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Retour à mes organisations</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const isCurrentActive = currentOrg?.id === organization.id;

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-slate-800">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-xl font-bold text-white shadow-xl shadow-indigo-600/20">
            {organization.name.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-bold tracking-tight text-white">
                {organization.name}
              </h1>
              {organization.user_role && (
                <span className="rounded-md border border-indigo-500/30 bg-indigo-500/10 px-2 py-0.5 text-[10px] font-semibold text-indigo-300 uppercase">
                  {organization.user_role}
                </span>
              )}
            </div>
            <p className="mt-1 text-xs text-slate-400 font-mono">
              Slug: /{organization.slug} • Plan: {organization.plan}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {!isCurrentActive && (
            <button
              type="button"
              onClick={() => setCurrentOrg(organization)}
              className="inline-flex items-center gap-2 rounded-xl border border-indigo-500/30 bg-indigo-600/20 px-4 py-2 text-xs font-semibold text-indigo-200 hover:bg-indigo-600 hover:text-white transition"
            >
              <CheckCircle2 className="h-3.5 w-3.5 text-indigo-400" />
              <span>Définir comme actif</span>
            </button>
          )}

          <Link
            href="/settings/organization"
            className="inline-flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800 hover:text-white transition"
          >
            <Settings className="h-3.5 w-3.5 text-slate-400" />
            <span>Paramètres</span>
          </Link>
        </div>
      </div>

      {/* Members Section */}
      <MemberList organization={organization} />
    </div>
  );
}

export default function OrganizationDetailPage() {
  return (
    <ProtectedRoute>
      <OrganizationDetailContent />
    </ProtectedRoute>
  );
}
