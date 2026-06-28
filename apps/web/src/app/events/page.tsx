"use client";

import { motion } from "framer-motion";
import { Zap, Search, Filter, Clock, Bot, Shield, ArrowUpRight } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

const EVENTS = [
  { id: "evt-1", title: "AI Chip Shortage Impacts Cloud Infrastructure Spending Globally", status: "verified", severity: "high", confidence: 0.92, topic: "AI Semiconductors", agents: 5, evidence: 12, time: "2h ago", velocity: 8.4 },
  { id: "evt-2", title: "Central Bank Policy Shift in Emerging Markets Signals Rate Changes", status: "researching", severity: "critical", confidence: 0.78, topic: "Monetary Policy", agents: 3, evidence: 7, time: "4h ago", velocity: 6.2 },
  { id: "evt-3", title: "Renewable Energy Investment Surge in Southeast Asia Markets", status: "candidate", severity: "medium", confidence: 0.65, topic: "Clean Energy", agents: 1, evidence: 4, time: "6h ago", velocity: 4.8 },
  { id: "evt-4", title: "Supply Chain Disruption in European Manufacturing Sector", status: "verified", severity: "high", confidence: 0.88, topic: "Supply Chain", agents: 5, evidence: 15, time: "8h ago", velocity: 3.6 },
  { id: "evt-5", title: "Critical Cybersecurity Vulnerability in Global Financial Systems", status: "disputed", severity: "critical", confidence: 0.45, topic: "Cybersecurity", agents: 4, evidence: 9, time: "12h ago", velocity: 3.1 },
  { id: "evt-6", title: "Trade Negotiations Between Major Economies Resume", status: "candidate", severity: "medium", confidence: 0.58, topic: "Trade Relations", agents: 2, evidence: 5, time: "14h ago", velocity: 2.9 },
];

const statusColors: Record<string, string> = {
  verified: "status-verified",
  researching: "status-researching",
  candidate: "status-candidate",
  disputed: "status-disputed",
};

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } };

export default function EventsPage() {
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState<string | null>(null);

  const filtered = EVENTS.filter(e => {
    if (search && !e.title.toLowerCase().includes(search.toLowerCase())) return false;
    if (filterStatus && e.status !== filterStatus) return false;
    return true;
  });

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      <motion.div variants={item} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Zap className="w-6 h-6 text-primary" /> Active Events
          </h1>
          <p className="text-sm text-muted-foreground mt-1">{EVENTS.length} events detected across {new Set(EVENTS.map(e => e.topic)).size} topic clusters</p>
        </div>
      </motion.div>

      {/* Search & Filters */}
      <motion.div variants={item} className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search events..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary/50 transition-all"
          />
        </div>
        <div className="flex gap-2">
          {["verified", "researching", "candidate", "disputed"].map(s => (
            <button
              key={s}
              onClick={() => setFilterStatus(filterStatus === s ? null : s)}
              className={`px-3 py-2 rounded-lg text-xs font-medium capitalize transition-all ${
                filterStatus === s ? statusColors[s] + " ring-1 ring-current" : "bg-white/5 text-muted-foreground hover:text-foreground"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </motion.div>

      {/* Event Cards */}
      <div className="grid gap-4">
        {filtered.map((event) => (
          <Link key={event.id} href={`/events/${event.id}`}>
            <motion.div
              variants={item}
              whileHover={{ scale: 1.005, x: 4 }}
              className="glass-card p-5 cursor-pointer group"
            >
              <div className="flex items-start gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${statusColors[event.status]}`}>{event.status}</span>
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${
                      event.severity === 'critical' ? 'severity-critical' :
                      event.severity === 'high' ? 'severity-high' : 'severity-medium'
                    }`}>{event.severity}</span>
                  </div>
                  <h3 className="text-base font-semibold group-hover:text-primary transition-colors">{event.title}</h3>
                  <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1"><Bot className="w-3 h-3" /> {event.agents} agents</span>
                    <span className="flex items-center gap-1"><Shield className="w-3 h-3" /> {event.evidence} evidence</span>
                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {event.time}</span>
                    <span className="px-2 py-0.5 rounded bg-white/5">{event.topic}</span>
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <div className={`text-xl font-bold ${
                    event.confidence >= 0.8 ? 'text-emerald-400' :
                    event.confidence >= 0.6 ? 'text-amber-400' : 'text-red-400'
                  }`}>
                    {(event.confidence * 100).toFixed(0)}%
                  </div>
                  <div className="text-[10px] text-muted-foreground mt-1">confidence</div>
                  <div className="mt-2 flex items-center gap-1 text-xs">
                    <span className="text-primary font-medium">{event.velocity.toFixed(1)}</span>
                    <span className="text-muted-foreground">vel.</span>
                  </div>
                </div>
              </div>
            </motion.div>
          </Link>
        ))}
      </div>
    </motion.div>
  );
}
