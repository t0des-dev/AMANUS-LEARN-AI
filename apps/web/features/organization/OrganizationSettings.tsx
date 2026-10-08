"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Building2,
  Save,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { authStorage } from "../../lib/authTokens";
import { organizationService } from "../../services/organizationService";
import { Organization, OrganizationPlan } from "../../types/organization";
import { useOrganization } from "../../components/organization/OrganizationContext";

interface OrganizationSettingsProps {
  organization: Organization;
  onUpdated: (org: Organization) => void;
}

export function OrganizationSettings({
  organization,
  onUpdated,
}: OrganizationSettingsProps) {
  const router = useRouter();
  const { refreshOrganizations, setCurrentOrg } = useOrganization();

  const [name, setName] = useState(organization.name);
  const [plan, setPlan] = useState<OrganizationPlan>(organization.plan);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isOwner = organization.user_role === "OWNER";
  const canEdit = isOwner || organization.user_role === "ADMIN";

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setErrorMessage(null);
    setIsSaving(true);

    const token = authStorage.getAccessToken();
    if (!token) return;

    try {
      const updated = await organizationService.update(token, organization.id, {
        name,
        plan,
      });
      setSuccessMessage("Organisation mise à jour avec succès.");
      onUpdated(updated);
      await refreshOrganizations();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Erreur lors de la mise à jour.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    const confirmation = prompt(
      `Pour confirmer la suppression définitive de l'organisation et de toutes ses données, tapez le nom exact : "${organization.name}"`
    );

    if (confirmation !== organization.name) {
      alert("Le nom saisi ne correspond pas. Suppression annulée.");
      return;
    }

    const token = authStorage.getAccessToken();
    if (!token) return;

    setIsDeleting(true);
    try {
      await organizationService.delete(token, organization.id);
      setCurrentOrg(null);
      await refreshOrganizations();
      router.push("/organizations");
    } catch (err: unknown) {
      if (err instanceof Error) {
        alert(err.message);
      } else {
        alert("Erreur lors de la suppression de l'organisation.");
      }
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* General Settings */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-xl">
        <div className="flex items-center gap-2.5 pb-4 border-b border-slate-800">
          <Building2 className="h-5 w-5 text-indigo-400" />
          <h3 className="text-base font-semibold text-white">
            Paramètres de l'organisation
          </h3>
        </div>

        {successMessage && (
          <div className="mt-4 flex items-center gap-2.5 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3 text-xs text-emerald-300">
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
            <span>{successMessage}</span>
          </div>
        )}

        {errorMessage && (
          <div className="mt-4 flex items-center gap-2.5 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-300">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleUpdate} className="mt-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300">
              Nom de l'organisation
            </label>
            <input
              type="text"
              required
              disabled={!canEdit}
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1.5 w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300">
              Identifiant URL (Slug)
            </label>
            <input
              type="text"
              disabled
              value={organization.slug}
              className="mt-1.5 w-full cursor-not-allowed rounded-xl border border-slate-800 bg-slate-950/40 px-4 py-2 text-sm text-slate-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300">
              Formule / Plan actuel
            </label>
            <select
              disabled={!isOwner}
              value={plan}
              onChange={(e) => setPlan(e.target.value as OrganizationPlan)}
              className="mt-1.5 w-full rounded-xl border border-slate-800 bg-slate-950 px-4 py-2 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
            >
              <option value="FREE">Gratuit (FREE)</option>
              <option value="PRO">Professionnel (PRO)</option>
              <option value="ENTERPRISE">Entreprise (ENTERPRISE)</option>
            </select>
          </div>

          {canEdit && (
            <div className="pt-2">
              <button
                type="submit"
                disabled={isSaving}
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-600/30 hover:bg-indigo-500 disabled:opacity-50 transition"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    <span>Enregistrement...</span>
                  </>
                ) : (
                  <>
                    <Save className="h-3.5 w-3.5" />
                    <span>Enregistrer</span>
                  </>
                )}
              </button>
            </div>
          )}
        </form>
      </div>

      {/* Danger Zone: Only for OWNER */}
      {isOwner && (
        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-6 backdrop-blur-xl">
          <div className="flex items-center gap-2 text-rose-400">
            <AlertTriangle className="h-5 w-5" />
            <h4 className="text-sm font-semibold">Zone de danger</h4>
          </div>
          <p className="mt-2 text-xs text-slate-400 leading-relaxed">
            La suppression d'une organisation est irréversible et supprimera
            définitivement l'ensemble de ses membres et de ses données associées.
          </p>
          <div className="mt-4">
            <button
              type="button"
              disabled={isDeleting}
              onClick={handleDelete}
              className="inline-flex items-center gap-2 rounded-xl bg-rose-600/20 px-4 py-2 text-xs font-semibold text-rose-300 hover:bg-rose-600 hover:text-white transition disabled:opacity-50"
            >
              <Trash2 className="h-4 w-4" />
              <span>Supprimer définitivement cette organisation</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
