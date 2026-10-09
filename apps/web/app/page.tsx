"use client";

import React from "react";
import Link from "next/link";
import {
  FileText,
  BrainCircuit,
  GraduationCap,
  Sparkles,
  Layers,
  ArrowRight,
  ShieldCheck,
  Headphones,
  SlidersHorizontal,
} from "lucide-react";
import { useTranslation } from "../lib/i18n/LanguageContext";

export default function HomePage() {
  const { t, isRTL } = useTranslation();

  const capabilities = [
    {
      icon: <FileText className="h-6 w-6 text-indigo-400" />,
      title: t("home.cap1Title"),
      description: t("home.cap1Desc"),
    },
    {
      icon: <BrainCircuit className="h-6 w-6 text-violet-400" />,
      title: t("home.cap2Title"),
      description: t("home.cap2Desc"),
    },
    {
      icon: <GraduationCap className="h-6 w-6 text-sky-400" />,
      title: t("home.cap3Title"),
      description: t("home.cap3Desc"),
    },
    {
      icon: <Headphones className="h-6 w-6 text-emerald-400" />,
      title: t("home.cap4Title"),
      description: t("home.cap4Desc"),
    },
    {
      icon: <Layers className="h-6 w-6 text-amber-400" />,
      title: t("home.cap5Title"),
      description: t("home.cap5Desc"),
    },
    {
      icon: <ShieldCheck className="h-6 w-6 text-teal-400" />,
      title: t("home.cap6Title"),
      description: t("home.cap6Desc"),
    },
  ];

  return (
    <div className="relative isolate overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80">
        <div className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-indigo-500 to-violet-600 opacity-20 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]" />
      </div>

      <section className="mx-auto max-w-7xl px-4 pt-20 pb-16 sm:px-6 lg:px-8">
        <div className="text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-4 py-1.5 text-xs font-semibold text-indigo-300 backdrop-blur-md">
            <Sparkles className="h-3.5 w-3.5 text-indigo-400" />
            <span>{t("home.badge")}</span>
          </div>

          <h1 className="mt-6 text-4xl font-extrabold tracking-tight text-white sm:text-6xl">
            {t("home.heroTitle1")}{" "}
            <span className="bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent">
              {t("home.heroHighlight")}
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-400 leading-relaxed">
            {t("home.heroSubtitle")}
          </p>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 transition hover:bg-indigo-500"
            >
              <span>{t("home.ctaStart")}</span>
              <ArrowRight className={`h-4 w-4 ${isRTL ? "rotate-180" : ""}`} />
            </Link>

            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900/80 px-6 py-3 text-sm font-semibold text-slate-200 transition hover:border-slate-600 hover:bg-slate-800"
            >
              <SlidersHorizontal className="h-4 w-4" />
              <span>{t("nav.dashboard")}</span>
            </Link>
          </div>
        </div>

        {/* Feature grid */}
        <div className="mt-24 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {capabilities.map((item, idx) => (
            <div
              key={idx}
              className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-6 backdrop-blur-sm transition hover:border-slate-700 hover:bg-slate-900/70"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800/80">
                {item.icon}
              </div>
              <h3 className="mt-4 text-base font-semibold text-white">{item.title}</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">{item.description}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
