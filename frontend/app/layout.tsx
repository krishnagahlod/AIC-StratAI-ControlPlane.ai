import type { Metadata } from "next";
import { Geist, Geist_Mono, Space_Grotesk } from "next/font/google";
import Sidebar from "@/components/Sidebar";
import PageTransition from "@/components/PageTransition";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

export const metadata: Metadata = {
  title: "ControlPlane.ai",
  description: "Real-time AI oversight: performance, cost, and responsibility risk for enterprise AI.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${spaceGrotesk.variable} h-full antialiased overflow-x-hidden`}
    >
      <body className="min-h-full flex bg-background text-foreground overflow-x-hidden">
        <Sidebar />
        <div className="flex-1 min-w-0 relative">
          <div className="mesh-backdrop" aria-hidden="true" />
          <main className="relative p-6 md:p-8 max-w-[1600px] mx-auto">
            <PageTransition>{children}</PageTransition>
          </main>
        </div>
      </body>
    </html>
  );
}
