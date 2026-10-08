"use client";

import Link from "next/link";
import { Sparkles, Activity } from "lucide-react";
import { useHealth } from "../../hooks/useHealth";
import { useAuth } from "../auth/AuthProvider";
import { UserMenu } from "./UserMenu";
import { OrganizationSwitcher } from "../organization/OrganizationSwitcher";

export function Navbar() {
  const { data: health, isSuccess } = useHealth();
  const { isAuthenticated, isLoading } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-lg shadow-indigo-500/20">
            <Sparkles className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-bold tracking-tight text-white">
              AMANUS <span className="text-indigo-400">LEARN AI</span>
            </span>
            <span className="text-[10px] text-slate-400 font-medium">EdTech • RAG • LMS</span>
          </div>
        </Link>

        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-300">
          <Link href="/" className="transition hover:text-white">
            Accueil
          </Link>
          <Link href="/dashboard" className="transition hover:text-white">
            Tableau de bord
          </Link>
          {isAuthenticated && (
            <>
              <Link href="/organizations" className="transition hover:text-white">
                Organisations
              </Link>
              <Link href="/documents" className="transition hover:text-white">
                Documents
              </Link>
              <Link href="/courses" className="transition hover:text-white">
                Cours
              </Link>
              <Link href="/quizzes" className="transition hover:text-white">
                Quiz
              </Link>
              <Link
                href="/chat"
                className="flex items-center gap-1.5 rounded-lg border border-indigo-500/30 bg-indigo-950/40 px-2.5 py-1 text-xs font-semibold text-indigo-300 transition hover:border-indigo-400 hover:bg-indigo-900/50 hover:text-white"
              >
                <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
                <span>AI Tutor</span>
              </Link>
            </>
          )}
          <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1 text-xs">
            <Activity className={`h-3.5 w-3.5 ${isSuccess && health?.status === "ok" ? "text-emerald-400 animate-pulse" : "text-amber-400"}`} />
            <span className="text-slate-400">API:</span>
            <span className={isSuccess && health?.status === "ok" ? "text-emerald-400 font-semibold" : "text-amber-400 font-semibold"}>
              {isSuccess && health?.status === "ok" ? "En ligne (/api/v1/health)" : "Connexion..."}
            </span>
          </div>
        </nav>

        <div className="flex items-center gap-3">
          {isLoading ? (
            <div className="h-8 w-20 rounded-lg bg-slate-850 animate-pulse" />
          ) : isAuthenticated ? (
            <div className="flex items-center gap-3">
              <OrganizationSwitcher />
              <UserMenu />
            </div>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-lg px-4 py-2 text-sm font-medium text-slate-300 transition hover:bg-slate-900 hover:text-white"
              >
                Connexion
              </Link>
              <Link
                href="/register"
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-indigo-500 shadow-indigo-600/30"
              >
                Commencer
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

