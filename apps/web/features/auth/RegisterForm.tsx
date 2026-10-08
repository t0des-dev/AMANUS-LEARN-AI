"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { UserPlus, Mail, Lock, User, AlertCircle, Loader2, Globe } from "lucide-react";
import { useAuth } from "../../components/auth/AuthProvider";

export function RegisterForm() {
  const { register } = useAuth();
  const router = useRouter();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [language, setLanguage] = useState("fr");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== passwordConfirm) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }

    if (password.length < 8) {
      setError("Le mot de passe doit comporter au moins 8 caractères.");
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        email,
        password,
        password_confirm: passwordConfirm,
        first_name: firstName,
        last_name: lastName,
        language,
      });
      router.push("/dashboard");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Impossible de créer le compte.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/60 p-8 shadow-2xl backdrop-blur-xl">
      <div className="text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-600/20 text-indigo-400">
          <UserPlus className="h-6 w-6" />
        </div>
        <h2 className="mt-4 text-2xl font-bold tracking-tight text-white">Créer un compte</h2>
        <p className="mt-2 text-xs text-slate-400">
          Rejoignez Amanus Learn AI pour transformer vos documents
        </p>
      </div>

      {error && (
        <div className="mt-6 flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3.5 text-xs text-rose-300">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-300">Prénom</label>
            <div className="relative mt-1">
              <input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="Jean"
                className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3.5 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300">Nom</label>
            <div className="relative mt-1">
              <input
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="Dupont"
                className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-3.5 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300">Adresse email</label>
          <div className="relative mt-1.5">
            <Mail className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-500" />
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="jean.dupont@organisation.com"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-10 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300">Langue préférée</label>
          <div className="relative mt-1.5">
            <Globe className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-500" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-10 py-2 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            >
              <option value="fr">Français (fr)</option>
              <option value="en">English (en)</option>
              <option value="es">Español (es)</option>
              <option value="ar">العربية (ar)</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300">Mot de passe</label>
          <div className="relative mt-1.5">
            <Lock className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-500" />
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min. 8 caractères"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-10 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300">Confirmer le mot de passe</label>
          <div className="relative mt-1.5">
            <Lock className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-500" />
            <input
              type="password"
              required
              minLength={8}
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
              placeholder="Répétez le mot de passe"
              className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-10 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 transition hover:bg-indigo-500 disabled:opacity-50"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Création du compte...</span>
            </>
          ) : (
            <span>Créer mon compte</span>
          )}
        </button>
      </form>

      <p className="mt-6 text-center text-xs text-slate-500">
        Vous avez déjà un compte ?{" "}
        <Link href="/login" className="text-indigo-400 hover:underline font-medium">
          Se connecter
        </Link>
      </p>
    </div>
  );
}
