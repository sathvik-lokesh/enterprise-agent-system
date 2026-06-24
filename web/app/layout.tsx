import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Enterprise Multi-Agent System — Sathvik Lokesh",
  description:
    "A hierarchical multi-agent system that automates internal enterprise workflows, built with Microsoft Agent Framework, PostgreSQL, and the Model Context Protocol (MCP). Live demo + architecture.",
  openGraph: {
    title: "Enterprise Multi-Agent System",
    description:
      "Hierarchical orchestration · 4 specialized agents · 14 tools · text-to-SQL · MCP. Try the live demo.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
