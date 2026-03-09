import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "AI Intelligence Radar — Daily AI Ecosystem Intelligence",
  description:
    "Automated analysis of the global AI ecosystem. Daily intelligence reports, trending topics, research papers, and custom AI topic analysis.",
  keywords: [
    "AI",
    "artificial intelligence",
    "intelligence report",
    "AI trends",
    "LLM",
    "machine learning",
    "research",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}
