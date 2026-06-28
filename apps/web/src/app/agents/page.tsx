"use client";

import { motion } from "framer-motion";
import { Bot, CheckCircle, Clock, XCircle, Cpu, Zap, DollarSign } from "lucide-react";

const AGENTS = [
  { name: "Research Agent", event: "AI Chip Shortage Impacts Cloud Infrastructure", status: "completed", latency: 3200, model: "gpt-4o-mini", cost: 0.0034, time: "2m ago", confidence: 0.92 },
  { name: "Fact Verification Agent", event: "Central Bank Policy Shift in Emerging Markets", status: "running", latency: null, model: "gpt-4o-mini", cost: 0, time: "now", confidence: null },
  { name: "Trend Evolution Agent", event: "AI Chip Shortage Impacts Cloud Infrastructure", status: "completed", latency: 2100, model: "gpt-4o-mini", cost: 0.0021, time: "3m ago", confidence: 0.78 },
  { name: "Business Impact Agent", event: "Supply Chain Disruption in European Manufacturing", status: "completed", latency: 4500, model: "gpt-4o", cost: 0.0089, time: "5m ago", confidence: 0.85 },
  { name: "Risk Assessment Agent", event: "Supply Chain Disruption in European Manufacturing", status: "completed", latency: 2800, model: "gpt-4o-mini", cost: 0.0028, time: "5m ago", confidence: 0.81 },
  { name: "Executive Summary Agent", event: "Renewable Energy Investment Surge", status: "completed", latency: 4200, model: "gpt-4o", cost: 0.0076, time: "8m ago", confidence: 0.88 },
  { name: "Reflection Agent", event: "Renewable Energy Investment Surge", status: "completed", latency: 1900, model: "gpt-4o-mini", cost: 0.0018, time: "8m ago", confidence: 0.90 },
  { name: "Research Agent", event: "Cybersecurity Vulnerability in Financial Systems", status: "failed", latency: 5000, model: "gpt-4o-mini", cost: 0.0041, time: "12m ago", confidence: null },
];

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export default function AgentsPage() {
  const totalCost = AGENTS.reduce((sum, a) => sum + a.cost, 0);
  const avgLatency = AGENTS.filter(a => a.latency).reduce((sum, a) => sum + (a.latency || 0), 0) / AGENTS.filter(a => a.latency).length;
  const successRate = (AGENTS.filter(a => a.status === "completed").length / AGENTS.length * 100);

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      <motion.div variants={item}>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Bot className="w-6 h-6 text-violet-400" /> Agent Activity
        </h1>
        <p className="text-sm text-muted-foreground mt-1">LangGraph multi-agent workflow monitoring and reasoning traces</p>
      </motion.div>

      {/* Agent Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Total Cost", value: `$${totalCost.toFixed(4)}`, icon: DollarSign, color: "from-emerald-500 to-green-400" },
          { label: "Avg Latency", value: `${(avgLatency / 1000).toFixed(1)}s`, icon: Clock, color: "from-blue-500 to-cyan-400" },
          { label: "Success Rate", value: `${successRate.toFixed(0)}%`, icon: Zap, color: "from-violet-500 to-purple-400" },
        ].map(stat => (
          <motion.div key={stat.label} variants={item} className="glass-card p-4 flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${stat.color} flex items-center justify-center`}>
              <stat.icon className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">{stat.label}</p>
              <p className="text-lg font-bold">{stat.value}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Agent Timeline */}
      <motion.div variants={item} className="glass-card">
        <div className="px-5 py-4 border-b border-white/5">
          <h2 className="text-sm font-semibold">Execution Timeline</h2>
        </div>
        <div className="divide-y divide-white/5">
          {AGENTS.map((agent, i) => (
            <motion.div
              key={i}
              variants={item}
              className="flex items-center gap-4 px-5 py-4 hover:bg-white/[0.02] transition-colors"
            >
              <div className="flex-shrink-0">
                {agent.status === "completed" ? (
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                ) : agent.status === "running" ? (
                  <div className="w-5 h-5 rounded-full border-2 border-blue-400 border-t-transparent animate-spin" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-400" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold">{agent.name}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-muted-foreground flex items-center gap-1">
                    <Cpu className="w-2.5 h-2.5" /> {agent.model}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5 truncate">{agent.event}</p>
              </div>
              <div className="text-right flex-shrink-0 space-y-0.5">
                <div className="text-xs font-medium">{agent.latency ? `${(agent.latency / 1000).toFixed(1)}s` : '—'}</div>
                <div className="text-[10px] text-muted-foreground">${agent.cost.toFixed(4)}</div>
              </div>
              {agent.confidence && (
                <div className={`text-sm font-bold flex-shrink-0 w-12 text-right ${
                  agent.confidence >= 0.85 ? 'text-emerald-400' : 'text-amber-400'
                }`}>
                  {(agent.confidence * 100).toFixed(0)}%
                </div>
              )}
              <div className="text-[10px] text-muted-foreground flex-shrink-0 w-14 text-right">{agent.time}</div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}
