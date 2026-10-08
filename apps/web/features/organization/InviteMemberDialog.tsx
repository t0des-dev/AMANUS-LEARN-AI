"use client";

import React, { useState } from "react";
import { UserPlus, Mail, Shield, AlertCircle, Loader2, X } from "lucide-react";
import { authStorage } from "../../lib/authTokens";
import { organizationService } from "../../services/organizationService";

interface InviteMemberDialogProps {
  organizationId: string;
  isOpen: boolean;
  onClose: () => void;
  onMemberAdded: () => void;
}

export function InviteMemberDialog({
  organizationId,
  isOpen,
  onClose,
  onMemberAdded,
}: InviteMemberDialogProps) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"ADMIN" | "TEACHER" | "STUDENT">("STUDENT");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const token = authStorage.getAccessToken();
    if (!token) {
      setError("Vous devez être authentifié.");
      setIsSubmitting(false);
      return;
    }

    try {
      await organizationService.addMember(token, organizationId, {
        email,
        role,
      });
      setEmail("");
      setRole("STUDENT");
      onMemberAdded();
      onClose();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Impossible d'ajouter ce membre.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600/20 text-indigo-400">
              <UserPlus className="h-5 w-5" />
            </div>
            <h3 className="text-base font-semibold text-white">Ajouter un membre</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {error && (
          <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-xs text-rose-300">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-400 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300">
              Adresse email du membre
            </label>
            <div className="relative mt-1.5">
              <Mail className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="collaborateur@organisation.com"
                className="w-full rounded-xl border border-slate-800 bg-slate-950 px-10 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300">
              Rôle attribué
            </label>
            <div className="relative mt-1.5">
              <Shield className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-500" />
              <select
                value={role}
                onChange={(e) =>
                  setRole(e.target.value as "ADMIN" | "TEACHER" | "STUDENT")
                }
                className="w-full rounded-xl border border-slate-800 bg-slate-950 px-10 py-2 text-sm text-slate-100 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              >
                <option value="STUDENT">Apprenant / Étudiant (STUDENT)</option>
                <option value="TEACHER">Enseignant / Formateur (TEACHER)</option>
                <option value="ADMIN">Administrateur (ADMIN)</option>
              </select>
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl px-4 py-2 text-xs font-medium text-slate-400 hover:bg-slate-800 hover:text-white transition"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-md shadow-indigo-600/30 hover:bg-indigo-500 disabled:opacity-50 transition"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Ajout en cours...</span>
                </>
              ) : (
                <span>Ajouter à l'organisation</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
