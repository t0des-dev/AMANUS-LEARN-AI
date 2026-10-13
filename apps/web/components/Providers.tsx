"use client";

import React, { ReactNode, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./auth/AuthProvider";
import { OrganizationProvider } from "./organization/OrganizationContext";
import { LanguageProvider } from "../lib/i18n/LanguageContext";
import { ToastProvider } from "./toast/ToastProvider";
import { ConfirmDialogProvider } from "./dialog/ConfirmDialogProvider";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
            refetchOnWindowFocus: false,
            refetchOnReconnect: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <OrganizationProvider>
          <LanguageProvider>
            <ToastProvider>
              <ConfirmDialogProvider>{children}</ConfirmDialogProvider>
            </ToastProvider>
          </LanguageProvider>
        </OrganizationProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
