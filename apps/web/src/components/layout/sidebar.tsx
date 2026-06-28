"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  Activity, BarChart3, Bot, Brain, FileText, Globe,
  Home, MessageSquare, Newspaper, Radio, Settings,
  TrendingUp, Zap, ChevronLeft, ChevronRight
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", icon: Home, label: "Dashboard" },
  { href: "/events", icon: Zap, label: "Events" },
  { href: "/feed", icon: Newspaper, label: "News Feed" },
  { href: "/topics", icon: Brain, label: "Topics" },
  { href: "/velocity", icon: TrendingUp, label: "Velocity" },
  { href: "/map", icon: Globe, label: "World Map" },
  { href: "/agents", icon: Bot, label: "Agents" },
  { href: "/memory", icon: Radio, label: "Memory" },
  { href: "/reports", icon: FileText, label: "Reports" },
  { href: "/analytics", icon: BarChart3, label: "Analytics" },
  { href: "/chat", icon: MessageSquare, label: "Chat" },
  { href: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.aside
      animate={{ width: collapsed ? 72 : 260 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      className="glass-sidebar fixed left-0 top-0 z-40 h-screen flex flex-col"
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-6 border-b border-white/5">
        <div className="relative flex-shrink-0">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div className="absolute -top-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-400 border-2 border-[hsl(224,71%,4%)] animate-pulse" />
        </div>
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <h1 className="text-sm font-bold gradient-text">News Intel</h1>
            <p className="text-[10px] text-muted-foreground">Platform v1.0</p>
          </motion.div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto custom-scrollbar">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link key={item.href} href={item.href}>
              <motion.div
                whileHover={{ x: 2 }}
                whileTap={{ scale: 0.98 }}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                  isActive
                    ? "bg-primary/15 text-primary shadow-[0_0_20px_-6px_hsl(var(--primary)/0.3)]"
                    : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                )}
              >
                <item.icon className={cn("w-[18px] h-[18px] flex-shrink-0", isActive && "drop-shadow-[0_0_6px_hsl(var(--primary))]")} />
                {!collapsed && <span>{item.label}</span>}
                {isActive && !collapsed && (
                  <motion.div
                    layoutId="active-indicator"
                    className="ml-auto w-1.5 h-1.5 rounded-full bg-primary"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center py-4 border-t border-white/5 text-muted-foreground hover:text-foreground transition-colors"
      >
        {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
      </button>
    </motion.aside>
  );
}
