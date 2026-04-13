import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Personal Brain | AI Outreach",
};

export default function BrainLayout({ children }: { children: React.ReactNode }) {
  return children;
}
