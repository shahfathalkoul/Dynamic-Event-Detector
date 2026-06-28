"use client";
import { motion } from "framer-motion";
import { Radio } from "lucide-react";
const item = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } };
const MEMORIES = [
  { type: "event_summary", content: "AI chip supply event affected cloud infrastructure spending. Multiple sources confirmed semiconductor shortage extending into Q3.", confidence: 0.92, event: "AI Chip Shortage", time: "2h ago" },
  { type: "agent_reflection", content: "Verification confidence was initially low due to conflicting trade data. After cross-referencing GDELT and Reuters, upgraded to verified.", confidence: 0.85, event: "Supply Chain Disruption", time: "5h ago" },
  { type: "analyst_correction", content: "Analyst corrected severity from 'medium' to 'high' based on downstream industry impact analysis.", confidence: 1.0, event: "Energy Investment", time: "8h ago" },
  { type: "similar_event", content: "Pattern matches 2024 semiconductor shortage that lasted 4 months and led to 12% cloud pricing increase.", confidence: 0.78, event: "AI Chip Shortage", time: "1d ago" },
];
export default function MemoryPage() {
  return (
    <motion.div initial="hidden" animate="show" variants={{ hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } }} className="space-y-6">
      <motion.div variants={item}><h1 className="text-2xl font-bold flex items-center gap-2"><Radio className="w-6 h-6 text-violet-400" /> Memory Explorer</h1><p className="text-sm text-muted-foreground mt-1">Long-term agent memory: event summaries, reflections, corrections, and historical analogs</p></motion.div>
      <div className="space-y-4">
        {MEMORIES.map((m, i) => (
          <motion.div key={i} variants={item} className="glass-card p-5">
            <div className="flex items-center gap-2 mb-2">
              <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${m.type === 'event_summary' ? 'bg-blue-500/20 text-blue-400' : m.type === 'analyst_correction' ? 'bg-amber-500/20 text-amber-400' : m.type === 'similar_event' ? 'bg-violet-500/20 text-violet-400' : 'bg-emerald-500/20 text-emerald-400'}`}>{m.type.replace(/_/g, ' ')}</span>
              <span className="text-xs text-muted-foreground">{m.event} · {m.time}</span>
            </div>
            <p className="text-sm leading-relaxed">{m.content}</p>
            <div className="mt-2 text-xs text-muted-foreground">Confidence: <strong className={m.confidence >= 0.85 ? 'text-emerald-400' : 'text-amber-400'}>{(m.confidence * 100).toFixed(0)}%</strong></div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
