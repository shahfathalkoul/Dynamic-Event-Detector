"use client";

import { motion } from "framer-motion";
import {
  Activity, AlertTriangle, BarChart3, Bot, Brain,
  FileText, TrendingUp, Zap, ArrowUpRight, ArrowDownRight,
  Clock, Shield
} from "lucide-react";
import Link from "next/link";

// ── Mock data (replaced by React Query in production) ───────────────

const STATS = [
  { label: "Active Events", value: "24", change: "+3", trend: "up", icon: Zap, color: "from-blue-500 to-cyan-400" },
  { label: "Topics Tracked", value: "156", change: "+12", trend: "up", icon: Brain, color: "from-violet-500 to-purple-400" },
  { label: "Velocity Spikes", value: "7", change: "+2", trend: "up", icon: TrendingUp, color: "from-amber-500 to-orange-400" },
  { label: "Reports Generated", value: "89", change: "+5", trend: "up", icon: FileText, color: "from-emerald-500 to-green-400" },
];

const RECENT_EVENTS = [
  { id: "evt-1", title: "AI Chip Shortage Impacts Cloud Infrastructure", status: "verified", severity: "high", confidence: 0.92, time: "2h ago", agents: 5 },
  { id: "evt-2", title: "Central Bank Policy Shift in Emerging Markets", status: "researching", severity: "critical", confidence: 0.78, time: "4h ago", agents: 3 },
  { id: "evt-3", title: "Renewable Energy Investment Surge in Southeast Asia", status: "candidate", severity: "medium", confidence: 0.65, time: "6h ago", agents: 1 },
  { id: "evt-4", title: "Supply Chain Disruption in European Manufacturing", status: "verified", severity: "high", confidence: 0.88, time: "8h ago", agents: 5 },
  { id: "evt-5", title: "Cybersecurity Vulnerability in Financial Systems", status: "disputed", severity: "critical", confidence: 0.45, time: "12h ago", agents: 4 },
];

const AGENT_ACTIVITY = [
  { name: "Research Agent", event: "AI Chip Shortage", status: "completed", time: "2m ago", latency: "3.2s" },
  { name: "Fact Verification", event: "Central Bank Policy", status: "running", time: "now", latency: "—" },
  { name: "Risk Assessment", event: "Supply Chain Disruption", status: "completed", time: "5m ago", latency: "2.1s" },
  { name: "Executive Summary", event: "Energy Investment", status: "completed", time: "8m ago", latency: "4.5s" },
];

const VELOCITY_DATA = [
  { topic: "AI Semiconductors", velocity: 8.4, trend: "accelerating" },
  { topic: "Monetary Policy", velocity: 6.2, trend: "accelerating" },
  { topic: "Clean Energy", velocity: 4.8, trend: "stable" },
  { topic: "Cybersecurity", velocity: 3.1, trend: "decaying" },
  { topic: "Trade Relations", velocity: 2.9, trend: "stable" },
];

// ── Animation variants ──────────────────────────────────────────────

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
} as const;

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" as const } },
};

// ── Components ──────────────────────────────────────────────────────

function StatCard({ stat }: { stat: typeof STATS[0] }) {
  return (
    <motion.div variants={item} className="glass-card p-5 group hover:scale-[1.02] transition-transform duration-200">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{stat.label}</p>
          <p className="text-3xl font-bold mt-1">{stat.value}</p>
          <div className="flex items-center gap-1 mt-2">
            {stat.trend === "up" ? (
              <ArrowUpRight className="w-3.5 h-3.5 text-emerald-400" />
            ) : (
              <ArrowDownRight className="w-3.5 h-3.5 text-red-400" />
            )}
            <span className={`text-xs font-medium ${stat.trend === "up" ? "text-emerald-400" : "text-red-400"}`}>
              {stat.change} today
            </span>
          </div>
        </div>
        <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
          <stat.icon className="w-5 h-5 text-white" />
        </div>
      </div>
    </motion.div>
  );
}

function EventRow({ event }: { event: typeof RECENT_EVENTS[0] }) {
  const statusColors: Record<string, string> = {
    verified: "bg-emerald-400",
    researching: "bg-blue-400 animate-pulse",
    candidate: "bg-amber-400",
    disputed: "bg-red-400",
  };

  return (
    <Link href={`/events/${event.id}`}>
      <motion.div
        variants={item}
        whileHover={{ x: 4 }}
        className="flex items-center gap-4 px-4 py-3.5 rounded-lg hover:bg-white/5 transition-colors cursor-pointer group"
      >
        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${statusColors[event.status] || "bg-gray-400"}`} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">{event.title}</p>
          <div className="flex items-center gap-3 mt-1">
            <span className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded ${
              event.severity === 'critical' ? 'severity-critical' :
              event.severity === 'high' ? 'severity-high' : 'severity-medium'
            }`}>
              {event.severity}
            </span>
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Bot className="w-3 h-3" /> {event.agents} agents
            </span>
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <div className={`text-sm font-semibold ${
            event.confidence >= 0.8 ? 'text-emerald-400' :
            event.confidence >= 0.6 ? 'text-amber-400' : 'text-red-400'
          }`}>
            {(event.confidence * 100).toFixed(0)}%
          </div>
          <div className="text-[10px] text-muted-foreground flex items-center gap-1 mt-0.5">
            <Clock className="w-2.5 h-2.5" /> {event.time}
          </div>
        </div>
      </motion.div>
    </Link>
  );
}

function VelocityBar({ topic, velocity, trend }: { topic: string; velocity: number; trend: string }) {
  const maxVelocity = 10;
  const width = Math.min((velocity / maxVelocity) * 100, 100);
  const color =
    trend === "accelerating" ? "from-red-500 to-orange-400" :
    trend === "stable" ? "from-blue-500 to-cyan-400" :
    "from-gray-500 to-gray-400";

  return (
    <motion.div variants={item} className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium">{topic}</span>
        <span className="text-xs text-muted-foreground">{velocity.toFixed(1)}</span>
      </div>
      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${width}%` }}
          transition={{ duration: 0.8, ease: "easeOut" as const, delay: 0.2 }}
          className={`h-full rounded-full bg-gradient-to-r ${color}`}
        />
      </div>
    </motion.div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────

export default function DashboardPage() {
  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-8">
      {/* Header */}
      <motion.div variants={item} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Intelligence Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time event detection and multi-agent analysis
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-medium text-emerald-400">Live</span>
          </div>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {STATS.map((stat) => (
          <StatCard key={stat.label} stat={stat} />
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Events Panel — 2 columns */}
        <motion.div variants={item} className="lg:col-span-2 glass-card">
          <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-primary" />
              <h2 className="text-sm font-semibold">Active Events</h2>
            </div>
            <Link href="/events" className="text-xs text-primary hover:text-primary/80 transition-colors flex items-center gap-1">
              View all <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-white/5">
            {RECENT_EVENTS.map((event) => (
              <EventRow key={event.id} event={event} />
            ))}
          </div>
        </motion.div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Velocity Panel */}
          <motion.div variants={item} className="glass-card">
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-amber-400" />
                <h2 className="text-sm font-semibold">Semantic Velocity</h2>
              </div>
              <Link href="/velocity" className="text-xs text-primary hover:text-primary/80 transition-colors">
                Details
              </Link>
            </div>
            <div className="p-5 space-y-4">
              {VELOCITY_DATA.map((v) => (
                <VelocityBar key={v.topic} {...v} />
              ))}
            </div>
          </motion.div>

          {/* Agent Activity */}
          <motion.div variants={item} className="glass-card">
            <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-violet-400" />
                <h2 className="text-sm font-semibold">Agent Activity</h2>
              </div>
              <Link href="/agents" className="text-xs text-primary hover:text-primary/80 transition-colors">
                Details
              </Link>
            </div>
            <div className="p-4 space-y-3">
              {AGENT_ACTIVITY.map((a, i) => (
                <div key={i} className="flex items-center gap-3 text-xs">
                  <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${a.status === 'running' ? 'bg-blue-400 animate-pulse' : 'bg-emerald-400'}`} />
                  <div className="flex-1 min-w-0">
                    <span className="font-medium">{a.name}</span>
                    <span className="text-muted-foreground"> · {a.event}</span>
                  </div>
                  <span className="text-muted-foreground">{a.latency}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
