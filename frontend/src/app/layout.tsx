import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import ErrorBoundary from "@/components/ErrorBoundary";
import BackendStatusBanner from "@/components/BackendStatusBanner";
import { ToastProvider } from "@/context/ToastContext";
import { CommandPalette } from "@/components/CommandPalette";
import { TemplateProvider } from "@/context/TemplateContext";
import ScrollToTop from "@/components/ScrollToTop";


const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Intelligent Outreach — AI-Powered Prospecting",
  description: "Find high-intent hiring managers, generate hyper-personalized LinkedIn messages, and manage your outreach pipeline — all powered by AI.",
  keywords: ["AI outreach", "cold email", "lead generation", "LinkedIn automation", "prospecting"],
  authors: [{ name: "AI Outreach System" }],
  openGraph: {
    title: "Intelligent Outreach — AI-Powered Prospecting",
    description: "Find high-intent hiring managers and generate personalized outreach at scale.",
    type: "website",
    siteName: "Intelligent Outreach",
  },
  twitter: {
    card: "summary_large_image",
    title: "Intelligent Outreach — AI-Powered Prospecting",
    description: "Find high-intent hiring managers and generate personalized outreach at scale.",
  },
  robots: {
    index: false,
    follow: false,
  },
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
                <ScrollToTop />
                <CommandPalette />
                <BackendStatusBanner />
                {/* SmoothScroll removed to support fixed app-layout with internal scrolling */}
                <div className="relative flex h-screen bg-background-dark overflow-hidden">
                {/* Global Noise Texture */}
                <div className="noise-overlay fixed inset-0 z-50 pointer-events-none opacity-[0.03]"></div>
                
                <Sidebar />
                <ErrorBoundary>
                  {children}
                </ErrorBoundary>
                </div>
          </TemplateProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
