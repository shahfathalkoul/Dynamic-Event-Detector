"use client";
import { motion } from "framer-motion";
import { Settings } from "lucide-react";
const item = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } };
const SECTIONS = [
  { title: "LLM Provider", desc: "Configure OpenAI / Anthropic API keys and model selection", value: "gpt-4o-mini" },
  { title: "Embedding Model", desc: "Sentence-BERT model for topic discovery and retrieval", value: "all-MiniLM-L6-v2" },
  { title: "Topic Discovery", desc: "UMAP, HDBSCAN, and BERTopic hyperparameters", value: "BERTopic v1" },
  { title: "Velocity Threshold", desc: "Anomaly score threshold for candidate event surfacing", value: "1.25" },
  { title: "Database", desc: "PostgreSQL connection and migration status", value: "Connected" },
  { title: "Vector Store", desc: "Qdrant connection and collection status", value: "6 collections" },
];
export default function SettingsPage() {
  return (
    <motion.div initial="hidden" animate="show" variants={{ hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } }} className="space-y-6">
      <motion.div variants={item}><h1 className="text-2xl font-bold flex items-center gap-2"><Settings className="w-6 h-6 text-gray-400" /> Settings</h1><p className="text-sm text-muted-foreground mt-1">Platform configuration and service status</p></motion.div>
      <div className="space-y-3">
        {SECTIONS.map(s => (
          <motion.div key={s.title} variants={item} className="glass-card p-5 flex items-center justify-between">
            <div><h3 className="text-sm font-semibold">{s.title}</h3><p className="text-xs text-muted-foreground mt-0.5">{s.desc}</p></div>
            <span className="text-xs font-mono px-3 py-1.5 rounded-lg bg-white/5 text-muted-foreground">{s.value}</span>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
