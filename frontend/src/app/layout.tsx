import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import SmoothScroll from "@/components/SmoothScroll";
import { ToastProvider } from "@/context/ToastContext";
import { CommandPalette } from "@/components/CommandPalette";
import { TemplateProvider } from "@/context/TemplateContext";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Cold Emailing - Calm Command Center",
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
            <CommandPalette />
            <SmoothScroll>
              <div className="relative flex min-h-screen bg-background-dark">
                <Sidebar />
                {children}
              </div>
            </SmoothScroll>
          </TemplateProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
