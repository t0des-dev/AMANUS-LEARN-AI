"use client";

import React from "react";
import { useTranslation } from "../../lib/i18n/LanguageContext";

export function Footer() {
  const { t } = useTranslation();

  return (
    <footer className="border-t border-slate-800 bg-slate-950 py-8 text-center text-xs text-slate-500">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <p>© 2026 Amanus Learn AI. {t("footer.tagline")} {t("footer.rights")}</p>
        <p className="mt-2 text-slate-600">
          Architecture modulaire multi-tenant • Django REST Framework • Next.js • Celery • PostgreSQL + pgvector
        </p>
      </div>
    </footer>
  );
}
