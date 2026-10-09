"use client";

import React, { useState, useEffect } from "react";
import { User, Mail, Globe, Save, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { ProtectedRoute } from "../../components/auth/ProtectedRoute";
import { useAuth } from "../../components/auth/AuthProvider";
import { useTranslation } from "../../lib/i18n/LanguageContext";

function ProfileContent() {
  const { t } = useTranslation();
  const { user, updateProfile } = useAuth();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [language, setLanguage] = useState("fr");
  const [isSaving, setIsSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setFirstName(user.first_name || "");
      setLastName(user.last_name || "");
      setLanguage(user.language || "fr");
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage(null);
    setErrorMessage(null);
    setIsSaving(true);

    try {
      await updateProfile({
        first_name: firstName,
        last_name: lastName,
        language,
      });
      setSuccessMessage("Profil mis à jour avec succès !");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("Erreur lors de la mise à jour du profil.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold tracking-tight text-white">{t("profile.title", "Mon Profil")}</h1>
        <p className="mt-1 text-sm text-slate-400">
          {t("profile.subtitle", "Gérez vos informations personnelles et vos préférences de plateforme.")}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
        {/* Left Card: Summary */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-xl">
          <div className="flex flex-col items-center text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-tr from-indigo-600 to-violet-500 text-2xl font-bold text-white shadow-xl shadow-indigo-600/30">
              {user?.first_name && user?.last_name
                ? `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
                : user?.email.slice(0, 2).toUpperCase()}
            </div>
            <h2 className="mt-4 text-base font-semibold text-white truncate max-w-full">
              {user?.first_name && user?.last_name
                ? `${user.first_name} ${user.last_name}`
                : t("profile.user", "Utilisateur")}
            </h2>
            <p className="text-xs text-slate-400 truncate max-w-full">{user?.email}</p>

            <div className="mt-6 w-full border-t border-slate-800 pt-4 text-left space-y-3 text-xs text-slate-400">
              <div className="flex justify-between">
                <span>{t("profile.status", "Statut :")}</span>
                <span className="font-semibold text-emerald-400">
                  {user?.is_active ? t("profile.active", "Actif") : t("profile.inactive", "Inactif")}
                </span>
              </div>
              <div className="flex justify-between">
                <span>{t("auth.preferredLanguage", "Langue :")}</span>
                <span className="font-semibold text-slate-200 uppercase">{user?.language}</span>
              </div>
              <div className="flex justify-between">
                <span>{t("profile.memberSince", "Membre depuis :")}</span>
                <span className="font-semibold text-slate-300">
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "--"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Card: Edit Form */}
        <div className="md:col-span-2 rounded-2xl border border-slate-800 bg-slate-900/60 p-8 backdrop-blur-xl">
          <h3 className="text-lg font-semibold text-white">{t("profile.generalInfo", "Informations Générales")}</h3>

          {successMessage && (
            <div className="mt-4 flex items-center gap-3 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3.5 text-xs text-emerald-300">
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
              <span>{successMessage}</span>
            </div>
          )}

          {errorMessage && (
            <div className="mt-4 flex items-center gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3.5 text-xs text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 space-y-5">
            <div>
              <label className="block text-xs font-medium text-slate-300">
                Adresse email (identifiant unique)
              </label>
              <div className="relative mt-1.5">
                <Mail className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-500" />
                <input
                  type="email"
                  disabled
                  value={user?.email || ""}
                  className="w-full cursor-not-allowed rounded-xl border border-slate-800 bg-slate-950/40 px-10 py-2.5 text-sm text-slate-400"
                />
              </div>
              <p className="mt-1 text-[11px] text-slate-500">
                L&apos;adresse email ne peut être modifiée pour des raisons de sécurité.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-medium text-slate-300">Prénom</label>
                <div className="relative mt-1.5">
                  <User className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    placeholder={t("auth.firstName", "Prénom")}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-10 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300">{t("auth.lastName", "Nom")}</label>
                <div className="relative mt-1.5">
                  <User className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    placeholder={t("auth.lastName", "Nom")}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-10 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300">{t("auth.preferredLanguage", "Langue préférée")}</label>
              <div className="relative mt-1.5">
                <Globe className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-500" />
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-10 py-2.5 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="fr">Français (fr)</option>
                  <option value="ar">العربية (ar)</option>
                  <option value="en">English (en)</option>
                </select>
              </div>
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={isSaving}
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 transition hover:bg-indigo-500 disabled:opacity-50"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>{t("profile.saving", "Enregistrement...")}</span>
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" />
                    <span>{t("profile.saveBtn", "Sauvegarder les modifications")}</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <ProfileContent />
    </ProtectedRoute>
  );
}
