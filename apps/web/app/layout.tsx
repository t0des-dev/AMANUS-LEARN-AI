import "./globals.css";
import React from "react";
import { Navbar } from "../components/layout/Navbar";
import { Footer } from "../components/layout/Footer";
import { Providers } from "../components/Providers";

export const metadata = {
  title: "Amanus Learn AI — Plateforme SaaS EdTech / RAG / LMS",
  description:
    "Transformez vos documents pédagogiques et professionnels en expériences d'apprentissage interactives assistées par IA.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className="dark" suppressHydrationWarning>
      <body className="flex min-h-screen flex-col bg-slate-950 text-slate-100 antialiased selection:bg-indigo-500 selection:text-white" suppressHydrationWarning>
        <Providers>
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
