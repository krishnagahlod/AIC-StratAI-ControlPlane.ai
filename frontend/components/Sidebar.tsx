"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Overview", icon: "◱" },
  { href: "/live", label: "Live Feed", icon: "⦿" },
  { href: "/trends", label: "Trends", icon: "📈" },
  { href: "/impact", label: "Business Impact", icon: "💼" },
  { href: "/review-queue", label: "Review Queue", icon: "👤" },
  { href: "/playground", label: "Policy Playground", icon: "🧪" },
  { href: "/try-it", label: "Try It Live", icon: "▶" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 shrink-0 border-r border-border bg-surface flex flex-col h-screen sticky top-0">
      <div className="px-5 py-6 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center font-bold text-white">
            C
          </div>
          <div>
            <div className="font-semibold leading-tight">ControlPlane.ai</div>
            <div className="text-xs text-muted leading-tight">AI Oversight System</div>
          </div>
        </div>
      </div>
      <nav className="flex-1 py-4 px-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                active
                  ? "bg-accent/15 text-white border border-accent/40"
                  : "text-muted hover:bg-surface-2 hover:text-foreground border border-transparent"
              }`}
            >
              <span className="w-5 text-center">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="px-5 py-4 border-t border-border text-xs text-muted">
        Team StratAI · IIT Bombay
        <br />
        Accenture Innovation Challenge 2026
      </div>
    </aside>
  );
}
