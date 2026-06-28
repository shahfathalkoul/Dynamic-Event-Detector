"use client";
import { motion } from "framer-motion";
import { Brain } from "lucide-react";
const item = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } };
const TOPICS = [
  { id: "t1", label: "AI Semiconductors", keywords: ["chip", "GPU", "NVIDIA", "semiconductor", "supply"], articles: 42, coherence: 0.89 },
  { id: "t2", label: "Monetary Policy", keywords: ["central bank", "interest rate", "inflation", "fed"], articles: 28, coherence: 0.82 },
  { id: "t3", label: "Clean Energy", keywords: ["solar", "renewable", "investment", "wind", "green"], articles: 35, coherence: 0.76 },
  { id: "t4", label: "Supply Chain", keywords: ["logistics", "manufacturing", "disruption", "trade"], articles: 22, coherence: 0.71 },
  { id: "t5", label: "Cybersecurity", keywords: ["vulnerability", "breach", "financial", "attack"], articles: 18, coherence: 0.84 },
];
export default function TopicsPage() {
  return (
    <motion.div initial="hidden" animate="show" variants={{ hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } }} className="space-y-6">
      <motion.div variants={item}><h1 className="text-2xl font-bold flex items-center gap-2"><Brain className="w-6 h-6 text-violet-400" /> Topic Explorer</h1><p className="text-sm text-muted-foreground mt-1">BERTopic clusters with Sentence-BERT embeddings, UMAP, and HDBSCAN</p></motion.div>
      <div className="grid gap-4 md:grid-cols-2">
        {TOPICS.map(t => (
          <motion.div key={t.id} variants={item} className="glass-card p-5 hover:scale-[1.01] transition-transform">
            <h3 className="text-base font-semibold">{t.label}</h3>
            <div className="flex flex-wrap gap-1.5 mt-2">{t.keywords.map(k => <span key={k} className="text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary">{k}</span>)}</div>
            <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
              <span>{t.articles} articles</span>
              <span>Coherence: <strong className="text-foreground">{t.coherence.toFixed(2)}</strong></span>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
