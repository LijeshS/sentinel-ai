import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Sentinel AI — Vendor Risk Intelligence",
  description: "Real-Time Third-Party Vendor Risk Monitoring Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${mono.variable}`}>
      <body className="bg-[#0f172a] text-slate-100 font-sans antialiased min-h-screen">
        {/* Subtle grid background */}
        <div
          className="fixed inset-0 pointer-events-none"
          style={{
            backgroundImage: `
              linear-gradient(rgba(148, 163, 184, 0.02) 1px, transparent 1px),
              linear-gradient(90deg, rgba(148, 163, 184, 0.02) 1px, transparent 1px)
            `,
            backgroundSize: "32px 32px",
          }}
        />
        {/* Top glow accent */}
        <div className="fixed top-0 left-1/2 -translate-x-1/2 w-full max-w-2xl h-px bg-gradient-to-r from-transparent via-cyan-500/40 to-transparent" />
        <div className="relative z-10">{children}</div>
      </body>
    </html>
  );
}
