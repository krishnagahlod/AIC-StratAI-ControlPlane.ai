import type { Metadata } from "next";
import { Geist_Mono, Public_Sans } from "next/font/google";
import Sidebar from "@/components/Sidebar";
import PageTransition from "@/components/PageTransition";
import { ConnectionBanner } from "@/components/ConnectionStatus";
import "./globals.css";

const publicSans = Public_Sans({
  variable: "--font-public-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ControlPlane.ai",
  description: "Real-time AI oversight: performance, cost, and responsibility risk for enterprise AI.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${publicSans.variable} ${geistMono.variable} h-full antialiased overflow-x-hidden`}
    >
      <body className="min-h-full flex bg-page-plane text-foreground overflow-x-hidden">
        <Sidebar />
        <ConnectionBanner />
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
