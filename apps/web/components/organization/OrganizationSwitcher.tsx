"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Building2,
  Check,
  ChevronDown,
  PlusCircle,
  Settings,
  Shield,
  Layers,
} from "lucide-react";
import { useOrganization } from "./OrganizationContext";
import { Organization } from "../../types/organization";

export function OrganizationSwitcher() {
  const { currentOrg, organizations, setCurrentOrg } = useOrganization();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (org: Organization) => {
    setCurrentOrg(org);
    setIsOpen(false);
    router.refresh();
  };

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-1.5 text-xs text-slate-200 transition hover:border-slate-700 hover:bg-slate-800"
      >
        <Building2 className="h-4 w-4 text-indigo-400 shrink-0" />
        <span className="max-w-[130px] truncate font-medium">
          {currentOrg ? currentOrg.name : "Sélectionner une organisation"}
        </span>
        {currentOrg?.user_role && (
          <span className="hidden sm:inline-block rounded-md bg-indigo-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-indigo-300 uppercase">
            {currentOrg.user_role}
          </span>
        )}
        <ChevronDown className="h-3 w-3 text-slate-400 ml-1" />
      </button>

      {isOpen && (
        <div className="absolute left-0 mt-2 w-64 rounded-2xl border border-slate-800 bg-slate-950 p-2 shadow-2xl backdrop-blur-xl z-50">
          <div className="px-3 py-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Mes Organisations
          </div>

          <div className="max-h-60 overflow-y-auto space-y-1">
            {organizations.length === 0 ? (
              <div className="px-3 py-2 text-xs text-slate-500">
                Aucune organisation trouvée.
              </div>
            ) : (
              organizations.map((org) => {
                const isSelected = currentOrg?.id === org.id;
                return (
                  <button
                    key={org.id}
                    type="button"
                    onClick={() => handleSelect(org)}
                    className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-xs transition ${
                      isSelected
                        ? "bg-indigo-600/20 text-white font-medium"
                        : "text-slate-300 hover:bg-slate-900 hover:text-white"
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <Layers className="h-3.5 w-3.5 text-indigo-400 shrink-0" />
                      <span className="truncate">{org.name}</span>
                    </div>
                    {isSelected && <Check className="h-4 w-4 text-indigo-400 shrink-0 ml-2" />}
                  </button>
                );
              })
            )}
          </div>

          <div className="mt-2 border-t border-slate-850 pt-2 space-y-1">
            <Link
              href="/organizations"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs text-slate-300 transition hover:bg-slate-900 hover:text-white"
            >
              <PlusCircle className="h-3.5 w-3.5 text-slate-400" />
              <span>Gérer les organisations</span>
            </Link>

            {currentOrg && (
              <Link
                href="/settings/organization"
                onClick={() => setIsOpen(false)}
                className="flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs text-slate-300 transition hover:bg-slate-900 hover:text-white"
              >
                <Settings className="h-3.5 w-3.5 text-slate-400" />
                <span>Paramètres de l&apos;organisation</span>
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
