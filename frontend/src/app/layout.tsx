import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import { ToastProvider } from "@/context/ToastContext";
import { CommandPalette } from "@/components/CommandPalette";
import { TemplateProvider } from "@/context/TemplateContext";

import AuthGuard from "@/components/AuthGuard";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Intelligent Outreach - Calm Command Center",
  description: "AI-powered cold outreach with a calm, focused interface.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        <ToastProvider>
          <TemplateProvider>
            <AuthGuard>
                <CommandPalette />
                {/* SmoothScroll removed to support fixed app-layout with internal scrolling */}
                <div className="relative flex h-screen bg-background-dark overflow-hidden">
                {/* Global Noise Texture */}
                <div className="noise-overlay fixed inset-0 z-50 pointer-events-none opacity-[0.03]"></div>
                
                <Sidebar />
                {children}
                </div>
            </AuthGuard>
          </TemplateProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
