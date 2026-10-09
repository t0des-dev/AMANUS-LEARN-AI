"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { User, LogOut, LayoutDashboard, Settings, ChevronDown } from "lucide-react";
import { useAuth } from "../auth/AuthProvider";
import { useTranslation } from "../../lib/i18n/LanguageContext";

export function UserMenu() {
  const { user, logout } = useAuth();
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!user) return null;

  const initials =
    user.first_name && user.last_name
      ? `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
      : user.email.slice(0, 2).toUpperCase();

  const handleLogout = async () => {
    setIsOpen(false);
    await logout();
    router.push("/");
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2.5 rounded-full border border-slate-800 bg-slate-900/80 py-1.5 pl-2 pr-3 text-xs text-slate-200 transition hover:border-slate-700 hover:bg-slate-850"
      >
        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-tr from-indigo-600 to-violet-500 font-bold text-white shadow-sm">
          {initials}
        </div>
        <span className="max-w-[120px] truncate font-medium text-slate-200">
          {user.first_name || user.email.split("@")[0]}
        </span>
        <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-slate-800 bg-slate-950 p-2 shadow-2xl backdrop-blur-xl z-50">
          <div className="border-b border-slate-850 px-3 py-2">
            <p className="text-xs font-semibold text-white truncate">
              {user.first_name && user.last_name
                ? `${user.first_name} ${user.last_name}`
                : t("common.user")}
            </p>
            <p className="text-[11px] text-slate-400 truncate">{user.email}</p>
          </div>

          <div className="py-1">
            <Link
              href="/dashboard"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-slate-300 transition hover:bg-slate-900 hover:text-white"
            >
              <LayoutDashboard className="h-4 w-4 text-slate-400" />
              <span>{t("nav.dashboard")}</span>
            </Link>

            <Link
              href="/profile"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-slate-300 transition hover:bg-slate-900 hover:text-white"
            >
              <Settings className="h-4 w-4 text-slate-400" />
              <span>{t("nav.profile")}</span>
            </Link>
          </div>

          <div className="border-t border-slate-850 pt-1">
            <button
              type="button"
              onClick={handleLogout}
              className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-medium text-rose-400 transition hover:bg-rose-500/10 hover:text-rose-300"
            >
              <LogOut className="h-4 w-4" />
              <span>{t("nav.logout")}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
