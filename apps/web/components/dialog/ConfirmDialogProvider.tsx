"use client";

import React, {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  useEffect,
  ReactNode,
} from "react";
import { AlertTriangle, AlertCircle, Info, X } from "lucide-react";

export type ConfirmVariant = "danger" | "warning" | "info" | "primary";

export interface ConfirmOptions {
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  variant?: ConfirmVariant;
  /** If specified, user must type this exact text before the confirm button is enabled */
  inputMatch?: string;
  inputPlaceholder?: string;
}

export interface PromptOptions {
  title?: string;
  message: string;
  defaultValue?: string;
  placeholder?: string;
  confirmText?: string;
  cancelText?: string;
}

interface DialogState {
  isOpen: boolean;
  type: "confirm" | "prompt";
  title: string;
  message: string;
  confirmText: string;
  cancelText: string;
  variant: ConfirmVariant;
  inputMatch?: string;
  inputPlaceholder?: string;
  inputValue: string;
  resolve: ((val: any) => void) | null;
}

interface ConfirmContextType {
  confirm: (options: ConfirmOptions | string) => Promise<boolean>;
  prompt: (options: PromptOptions | string) => Promise<string | null>;
}

const ConfirmContext = createContext<ConfirmContextType | undefined>(undefined);

export function ConfirmDialogProvider({ children }: { children: ReactNode }) {
  const [dialog, setDialog] = useState<DialogState>({
    isOpen: false,
    type: "confirm",
    title: "",
    message: "",
    confirmText: "Confirmer",
    cancelText: "Annuler",
    variant: "danger",
    inputValue: "",
    resolve: null,
  });

  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (dialog.isOpen && (dialog.type === "prompt" || dialog.inputMatch)) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [dialog.isOpen, dialog.type, dialog.inputMatch]);

  const confirm = useCallback(
    (options: ConfirmOptions | string): Promise<boolean> => {
      return new Promise<boolean>((resolve) => {
        const opts: ConfirmOptions =
          typeof options === "string" ? { message: options } : options;

        setDialog({
          isOpen: true,
          type: "confirm",
          title: opts.title || (opts.variant === "warning" ? "Confirmation requise" : opts.variant === "info" ? "Information" : "Confirmer la suppression"),
          message: opts.message,
          confirmText: opts.confirmText || (opts.variant === "danger" ? "Supprimer" : "Confirmer"),
          cancelText: opts.cancelText || "Annuler",
          variant: opts.variant || "danger",
          inputMatch: opts.inputMatch,
          inputPlaceholder: opts.inputPlaceholder,
          inputValue: "",
          resolve: (val: boolean) => resolve(val),
        });
      });
    },
    []
  );

  const prompt = useCallback(
    (options: PromptOptions | string): Promise<string | null> => {
      return new Promise<string | null>((resolve) => {
        const opts: PromptOptions =
          typeof options === "string" ? { message: options } : options;

        setDialog({
          isOpen: true,
          type: "prompt",
          title: opts.title || "Confirmation",
          message: opts.message,
          confirmText: opts.confirmText || "Valider",
          cancelText: opts.cancelText || "Annuler",
          variant: "danger",
          inputPlaceholder: opts.placeholder,
          inputValue: opts.defaultValue || "",
          resolve: (val: string | null) => resolve(val),
        });
      });
    },
    []
  );

  const handleClose = useCallback(
    (confirmed: boolean) => {
      if (!dialog.isOpen || !dialog.resolve) return;

      if (dialog.type === "confirm") {
        dialog.resolve(confirmed);
      } else {
        dialog.resolve(confirmed ? dialog.inputValue : null);
      }

      setDialog((prev) => ({ ...prev, isOpen: false, resolve: null }));
    },
    [dialog]
  );

  // Keyboard navigation: Escape cancels, Enter confirms if eligible
  useEffect(() => {
    if (!dialog.isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        handleClose(false);
      } else if (e.key === "Enter" && !e.shiftKey) {
        if (dialog.inputMatch && dialog.inputValue !== dialog.inputMatch) {
          return;
        }
        e.preventDefault();
        handleClose(true);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [dialog.isOpen, dialog.inputValue, dialog.inputMatch, handleClose]);

  const canConfirm =
    !dialog.inputMatch || dialog.inputValue === dialog.inputMatch;

  return (
    <ConfirmContext.Provider value={{ confirm, prompt }}>
      {children}

      {dialog.isOpen && (
        <div
          className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-200"
          onClick={() => handleClose(false)}
        >
          <div
            className={`relative w-full max-w-md rounded-2xl border p-6 shadow-2xl transition-all scale-100 ${
              dialog.variant === "danger"
                ? "bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950 border-red-500/30 shadow-red-950/40"
                : dialog.variant === "warning"
                ? "bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950 border-amber-500/30 shadow-amber-950/40"
                : "bg-gradient-to-b from-slate-900 via-slate-950 to-slate-950 border-indigo-500/30 shadow-indigo-950/40"
            }`}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            {/* Top Close Button */}
            <button
              onClick={() => handleClose(false)}
              className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
              aria-label="Fermer"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Header with Icon */}
            <div className="flex items-start gap-4">
              <div
                className={`p-3 rounded-xl shrink-0 ${
                  dialog.variant === "danger"
                    ? "bg-red-500/15 text-red-400 border border-red-500/30"
                    : dialog.variant === "warning"
                    ? "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                    : "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30"
                }`}
              >
                {dialog.variant === "danger" ? (
                  <AlertTriangle className="w-6 h-6 animate-pulse" />
                ) : dialog.variant === "warning" ? (
                  <AlertCircle className="w-6 h-6" />
                ) : (
                  <Info className="w-6 h-6" />
                )}
              </div>

              <div className="flex-1 min-w-0 pr-4">
                <h3 className="text-lg font-semibold text-white tracking-tight">
                  {dialog.title}
                </h3>
                <p className="mt-1.5 text-sm text-slate-300 leading-relaxed whitespace-pre-line">
                  {dialog.message}
                </p>
              </div>
            </div>

            {/* Input field (if prompt or required match) */}
            {(dialog.type === "prompt" || dialog.inputMatch) && (
              <div className="mt-4">
                <input
                  ref={inputRef}
                  type="text"
                  value={dialog.inputValue}
                  onChange={(e) =>
                    setDialog((prev) => ({ ...prev, inputValue: e.target.value }))
                  }
                  placeholder={
                    dialog.inputPlaceholder ||
                    (dialog.inputMatch ? `Tapez "${dialog.inputMatch}" pour confirmer` : "")
                  }
                  className="w-full px-3.5 py-2.5 rounded-xl text-sm bg-slate-900 border border-slate-700 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 text-white placeholder-slate-500 outline-none transition-all"
                />
              </div>
            )}

            {/* Footer buttons */}
            <div className="mt-6 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => handleClose(false)}
                className="px-4 py-2.5 rounded-xl text-sm font-medium text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 transition-all focus:outline-none"
              >
                {dialog.cancelText}
              </button>

              <button
                type="button"
                disabled={!canConfirm}
                onClick={() => handleClose(true)}
                className={`px-5 py-2.5 rounded-xl text-sm font-medium text-white shadow-lg transition-all focus:outline-none disabled:opacity-40 disabled:cursor-not-allowed ${
                  dialog.variant === "danger"
                    ? "bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 shadow-red-500/25 active:scale-98"
                    : dialog.variant === "warning"
                    ? "bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 shadow-amber-500/25 active:scale-98"
                    : "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 shadow-indigo-500/25 active:scale-98"
                }`}
              >
                {dialog.confirmText}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

export function useConfirm() {
  const context = useContext(ConfirmContext);
  if (!context) {
    throw new Error("useConfirm must be used within a ConfirmDialogProvider");
  }
  return context;
}
