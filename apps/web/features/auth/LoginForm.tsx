"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogIn, Lock, Mail, AlertCircle, Loader2 } from "lucide-react";
import { useAuth } from "../../components/auth/AuthProvider";
import { useTranslation } from "../../lib/i18n/LanguageContext";

export function LoginForm() {
  const { login } = useAuth();
  const { t } = useTranslation();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login({ email, password });
      router.push("/dashboard");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(t("auth.loginFailed"));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/60 p-8 shadow-2xl backdrop-blur-xl">
      <div className="text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-600/20 text-indigo-400">
          <LogIn className="h-6 w-6" />
        </div>
        <h2 className="mt-4 text-2xl font-bold tracking-tight text-white">{t("auth.loginTitle")}</h2>
        <p className="mt-2 text-xs text-slate-400">
          {t("auth.loginSub")}
        </p>
      </div>

      {error && (
        <div className="mt-6 flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3.5 text-xs text-rose-300">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        <div>
          <label className="block text-xs font-medium text-slate-300">{t("auth.email")}</label>
          <div className="relative mt-1.5">
            <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t("auth.emailPlaceholder")}
              className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-10 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300">{t("auth.password")}</label>
          <div className="relative mt-1.5">
            <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
            <input
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t("auth.passwordPlaceholder")}
              className="w-full rounded-xl border border-slate-800 bg-slate-950/80 px-10 py-2.5 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
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
              <span>{t("auth.submitting")}</span>
            </>
          ) : (
            <span>{t("auth.signInBtn")}</span>
          )}
        </button>
      </form>

      <p className="mt-6 text-center text-xs text-slate-500">
        {t("auth.noAccount")}{" "}
        <Link href="/register" className="text-indigo-400 hover:underline font-medium">
          {t("auth.signUpBtn")}
        </Link>
      </p>
    </div>
  );
}
