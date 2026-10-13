"use client";

import React, { createContext, useContext, useState, useCallback, useMemo } from "react";
import {
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Info,
  X,
} from "lucide-react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface ToastOptions {
  title?: string;
  duration?: number;
}

export interface ToastItem {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration: number;
  createdAt: number;
}

interface ToastContextValue {
  show: (type: ToastType, message: string, options?: ToastOptions) => void;
  success: (message: string, options?: ToastOptions | string) => void;
  error: (message: string, options?: ToastOptions | string) => void;
  warning: (message: string, options?: ToastOptions | string) => void;
  info: (message: string, options?: ToastOptions | string) => void;
  dismiss: (id: string) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}

const ICONS: Record<ToastType, React.ElementType> = {
  success: CheckCircle2,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
};

const STYLES: Record<
  ToastType,
  {
    border: string;
    bg: string;
    glow: string;
    text: string;
    iconColor: string;
    progressBar: string;
  }
> = {
  success: {
    border: "border-emerald-500/30",
    bg: "bg-slate-900/95",
    glow: "shadow-emerald-500/10",
    text: "text-emerald-300",
    iconColor: "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20",
    progressBar: "bg-emerald-500",
  },
  error: {
    border: "border-rose-500/30",
    bg: "bg-slate-900/95",
    glow: "shadow-rose-500/10",
    text: "text-rose-300",
    iconColor: "text-rose-400 bg-rose-500/10 border border-rose-500/20",
    progressBar: "bg-rose-500",
  },
  warning: {
    border: "border-amber-500/30",
    bg: "bg-slate-900/95",
    glow: "shadow-amber-500/10",
    text: "text-amber-300",
    iconColor: "text-amber-400 bg-amber-500/10 border border-amber-500/20",
    progressBar: "bg-amber-500",
  },
  info: {
    border: "border-indigo-500/30",
    bg: "bg-slate-900/95",
    glow: "shadow-indigo-500/10",
    text: "text-indigo-300",
    iconColor: "text-indigo-400 bg-indigo-500/10 border border-indigo-500/20",
    progressBar: "bg-indigo-500",
  },
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const show = useCallback(
    (type: ToastType, message: string, options?: ToastOptions) => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      const duration = options?.duration ?? (type === "error" ? 6000 : 4500);

      const newToast: ToastItem = {
        id,
        type,
        title: options?.title,
        message,
        duration,
        createdAt: Date.now(),
      };

      setToasts((prev) => [...prev.slice(-4), newToast]); // Keep max 5 visible toasts

      if (duration > 0) {
        setTimeout(() => {
          dismiss(id);
        }, duration);
      }
    },
    [dismiss]
  );

  const normalizeOptions = (opts?: ToastOptions | string): ToastOptions | undefined => {
    if (typeof opts === "string") return { title: opts };
    return opts;
  };

  const success = useCallback(
    (message: string, options?: ToastOptions | string) =>
      show("success", message, normalizeOptions(options)),
    [show]
  );

  const error = useCallback(
    (message: string, options?: ToastOptions | string) =>
      show("error", message, normalizeOptions(options)),
    [show]
  );

  const warning = useCallback(
    (message: string, options?: ToastOptions | string) =>
      show("warning", message, normalizeOptions(options)),
    [show]
  );

  const info = useCallback(
    (message: string, options?: ToastOptions | string) =>
      show("info", message, normalizeOptions(options)),
    [show]
  );

  const contextValue = useMemo(
    () => ({ show, success, error, warning, info, dismiss }),
    [show, success, error, warning, info, dismiss]
  );

  return (
    <ToastContext.Provider value={contextValue}>
      {children}

      {/* Floating Toast Container */}
      <div
        role="region"
        aria-label="Notifications"
        className="fixed bottom-5 right-5 z-[9999] flex flex-col gap-2.5 max-w-sm sm:max-w-md w-full pointer-events-none px-4 sm:px-0"
      >
        {toasts.map((toast) => {
          const style = STYLES[toast.type];
          const Icon = ICONS[toast.type];

          return (
            <div
              key={toast.id}
              className={`pointer-events-auto relative overflow-hidden rounded-2xl border ${style.border} ${style.bg} ${style.glow} p-4 shadow-xl backdrop-blur-xl transition-all duration-300 animate-in slide-in-from-bottom-5 fade-in`}
            >
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-xl shrink-0 ${style.iconColor}`}>
                  <Icon className="w-4 h-4" />
                </div>

                <div className="flex-1 pt-0.5 min-w-0">
                  {toast.title && (
                    <h4 className="text-xs font-bold text-white mb-0.5 tracking-tight truncate">
                      {toast.title}
                    </h4>
                  )}
                  <p className="text-xs text-slate-200 leading-relaxed break-words">
                    {toast.message}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => dismiss(toast.id)}
                  className="shrink-0 p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
                  title="Fermer la notification"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Dismiss countdown progress bar */}
              {toast.duration > 0 && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-slate-800">
                  <div
                    className={`h-full ${style.progressBar} transition-all`}
                    style={{
                      animation: `shrinkWidth ${toast.duration}ms linear forwards`,
                    }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
};
