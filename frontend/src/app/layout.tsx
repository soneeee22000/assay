import type { Metadata } from "next";
import { Fira_Code, Fira_Sans } from "next/font/google";

import "./globals.css";

const firaSans = Fira_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
  variable: "--font-fira-sans",
});

const firaCode = Fira_Code({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
  variable: "--font-fira-code",
});

export const metadata: Metadata = {
  title: "Assay — RWA Fintech Reference Architecture",
  description:
    "Event-sourced ledger, on-chain certificates of authenticity, and custodian-backed escrow lifecycle. Read-only admin dashboard.",
  applicationName: "Assay",
  authors: [{ name: "Pyae Sone Kyaw", url: "https://pseonkyaw.dev" }],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${firaSans.variable} ${firaCode.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
