"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Radio,
  TrendingUp,
  Briefcase,
  UserCheck,
  FlaskConical,
  Play,
  ShieldCheck,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/live", label: "Live Feed", icon: Radio },
  { href: "/trends", label: "Trends", icon: TrendingUp },
  { href: "/impact", label: "Business Impact", icon: Briefcase },
  { href: "/review-queue", label: "Review Queue", icon: UserCheck },
  { href: "/playground", label: "Policy Playground", icon: FlaskConical },
  { href: "/try-it", label: "Try It Live", icon: Play },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 shrink-0 border-r border-border bg-surface/60 backdrop-blur-xl flex flex-col h-screen sticky top-0 z-10">
      <div className="px-5 py-6 border-b border-border/80">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent to-accent-2 flex items-center justify-center shadow-[0_4px_16px_-4px_var(--accent-soft)]">
            <ShieldCheck size={18} className="text-white" strokeWidth={2.25} />
          </div>
          <div>
            <div className="font-display font-semibold leading-tight tracking-tight">ControlPlane.ai</div>
            <div className="text-[11px] text-muted leading-tight">AI Oversight System</div>
          </div>
        </div>
      </div>
      <nav className="flex-1 py-4 px-3 space-y-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors duration-150 ${
                active ? "text-white" : "text-muted hover:bg-surface-2 hover:text-foreground"
              }`}
            >
              {active && (
                <motion.div
                  layoutId="nav-active"
                  className="absolute inset-0 bg-gradient-to-r from-accent/25 to-accent/5 border border-accent/40 rounded-xl"
                  transition={{ type: "spring", stiffness: 400, damping: 32 }}
                />
              )}
              <Icon size={17} strokeWidth={2} className="relative z-10 shrink-0" />
              <span className="relative z-10 font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="px-5 py-4 border-t border-border/80 text-[11px] text-muted-2 leading-relaxed">
        Team StratAI · IIT Bombay
        <br />
        Accenture Innovation Challenge 2026
      </div>
    </aside>
  );
}
