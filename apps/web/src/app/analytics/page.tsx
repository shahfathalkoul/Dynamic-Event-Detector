"use client";
import { motion } from "framer-motion";
import { BarChart3, TrendingUp, Zap, DollarSign, Clock, Bot } from "lucide-react";
const item = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } };
const METRICS = [
  { label: "Events Detected (24h)", value: "24", icon: Zap, color: "from-blue-500 to-cyan-400" },
  { label: "Reports Generated (24h)", value: "12", icon: TrendingUp, color: "from-violet-500 to-purple-400" },
  { label: "Agent Runs (24h)", value: "156", icon: Bot, color: "from-amber-500 to-orange-400" },
  { label: "Total LLM Cost (24h)", value: "$2.84", icon: DollarSign, color: "from-emerald-500 to-green-400" },
  { label: "Avg Latency", value: "3.2s", icon: Clock, color: "from-pink-500 to-rose-400" },
  { label: "Citation Precision", value: "94%", icon: BarChart3, color: "from-indigo-500 to-blue-400" },
];
export default function AnalyticsPage() {
  return (
    <motion.div initial="hidden" animate="show" variants={{ hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } }} className="space-y-6">
      <motion.div variants={item}><h1 className="text-2xl font-bold flex items-center gap-2"><BarChart3 className="w-6 h-6 text-indigo-400" /> Analytics</h1><p className="text-sm text-muted-foreground mt-1">Platform performance, cost tracking, and quality metrics</p></motion.div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {METRICS.map(m => (
          <motion.div key={m.label} variants={item} className="glass-card p-5">
            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${m.color} flex items-center justify-center mb-3`}><m.icon className="w-5 h-5 text-white" /></div>
            <p className="text-2xl font-bold">{m.value}</p>
            <p className="text-xs text-muted-foreground mt-1">{m.label}</p>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
