"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Building2, ArrowLeft, Loader2, PlusCircle } from "lucide-react";
import { ProtectedRoute } from "../../../components/auth/ProtectedRoute";
import { useOrganization } from "../../../components/organization/OrganizationContext";
import { OrganizationSettings } from "../../../features/organization/OrganizationSettings";
import { MemberList } from "../../../features/organization/MemberList";

function SettingsOrganizationContent() {
  const { currentOrg, isLoading, setCurrentOrg } = useOrganization();
  const [activeTab, setActiveTab] = useState<"general" | "members">("general");

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
      </div>
    );
  }

  if (!currentOrg) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 text-center">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-12">
          <Building2 className="mx-auto h-12 w-12 text-slate-500" />
          <h2 className="mt-4 text-lg font-bold text-white">
            Aucune organisation active sélectionnée
          </h2>
          <p className="mt-2 text-xs text-slate-400 max-w-sm mx-auto">
            Veuillez sélectionner ou créer une organisation pour configurer ses paramètres.
          </p>
          <div className="mt-6">
            <Link
              href="/organizations"
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white hover:bg-indigo-500 transition"
            >
              <PlusCircle className="h-4 w-4" />
              <span>Gérer les organisations</span>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <Link
              href="/organizations"
              className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
              title="Retour aux organisations"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Paramètres : {currentOrg.name}
            </h1>
          </div>
          <p className="mt-1 text-xs text-slate-400 ml-9">
            Gérez la configuration globale, les membres et les droits d&apos;accès de l&apos;organisation.
          </p>
        </div>

        {/* Tab switchers */}
        <div className="flex rounded-xl border border-slate-800 bg-slate-900/80 p-1 text-xs font-medium">
          <button
            type="button"
            onClick={() => setActiveTab("general")}
            className={`rounded-lg px-4 py-1.5 transition ${
              activeTab === "general"
                ? "bg-indigo-600 text-white font-semibold shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Général
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("members")}
            className={`rounded-lg px-4 py-1.5 transition ${
              activeTab === "members"
                ? "bg-indigo-600 text-white font-semibold shadow-sm"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Membres & Rôles
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === "general" ? (
        <OrganizationSettings
          organization={currentOrg}
          onUpdated={(updated) => setCurrentOrg(updated)}
        />
      ) : (
        <MemberList organization={currentOrg} />
      )}
    </div>
  );
}

export default function SettingsOrganizationPage() {
  return (
    <ProtectedRoute>
      <SettingsOrganizationContent />
    </ProtectedRoute>
  );
}
