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

function Mark() {
  return (
    <div className="w-9 h-9 rounded-xl bg-accent flex items-center justify-center shrink-0 shadow-[0_2px_8px_-2px_rgba(161,0,255,0.5)]">
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
        <path d="M4 18L11 6" stroke="white" strokeWidth="2.75" strokeLinecap="round" />
        <path d="M11 18L18 6" stroke="white" strokeWidth="2.75" strokeLinecap="round" />
        <path d="M14.5 6H20V11.5" stroke="white" strokeWidth="2.75" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 shrink-0 border-r border-border bg-white flex flex-col h-screen sticky top-0 z-10">
      <div className="px-5 py-6 border-b border-border">
        <div className="flex items-center gap-2.5">
          <Mark />
          <div>
            <div className="font-bold leading-tight tracking-tight text-foreground">ControlPlane.ai</div>
            <div className="text-[11px] text-muted-2 leading-tight">AI Oversight System</div>
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
                active ? "text-accent-deep font-semibold" : "text-muted hover:bg-surface-2 hover:text-foreground font-medium"
              }`}
            >
              {active && (
                <motion.div
                  layoutId="nav-active"
                  className="absolute inset-0 bg-accent-tint border border-accent/20 rounded-xl"
                  transition={{ type: "spring", stiffness: 400, damping: 32 }}
                />
              )}
              <Icon size={17} strokeWidth={2.25} className="relative z-10 shrink-0" />
              <span className="relative z-10">{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="px-5 py-4 border-t border-border text-[11px] text-muted-2 leading-relaxed">
        Team StratAI · IIT Bombay
        <br />
        Accenture Innovation Challenge 2026
      </div>
    </aside>
  );
}
