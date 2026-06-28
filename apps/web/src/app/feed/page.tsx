"use client";
import { motion } from "framer-motion";
import { Newspaper, Clock, ExternalLink } from "lucide-react";
const item = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };
const FEED = [
  { title: "NVIDIA Reports Record Q2 Revenue Amid AI Chip Demand", source: "Reuters", time: "12m ago", category: "Technology", url: "#" },
  { title: "Federal Reserve Signals Pause in Rate Hike Cycle", source: "Bloomberg", time: "25m ago", category: "Finance", url: "#" },
  { title: "European Automakers Face New Supply Chain Challenges", source: "FT", time: "38m ago", category: "Manufacturing", url: "#" },
  { title: "Solar Energy Installations Hit Record in ASEAN Region", source: "Asia Times", time: "1h ago", category: "Energy", url: "#" },
  { title: "Major Bank Reports Cyberattack Affecting Online Services", source: "WSJ", time: "1.5h ago", category: "Cybersecurity", url: "#" },
  { title: "US-China Trade Talks Resume with New Framework", source: "AP", time: "2h ago", category: "Geopolitics", url: "#" },
  { title: "Global Semiconductor Shortage Expected to Ease in Q4", source: "Nikkei", time: "3h ago", category: "Technology", url: "#" },
  { title: "Inflation Expectations Fall in Eurozone Survey", source: "ECB", time: "4h ago", category: "Economics", url: "#" },
];
export default function FeedPage() {
  return (
    <motion.div initial="hidden" animate="show" variants={{ hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.04 } } }} className="space-y-6">
      <motion.div variants={item}><h1 className="text-2xl font-bold flex items-center gap-2"><Newspaper className="w-6 h-6 text-cyan-400" /> Live News Feed</h1><p className="text-sm text-muted-foreground mt-1">Real-time article ingestion from RSS, News API, and GDELT</p></motion.div>
      <div className="space-y-2">
        {FEED.map((a, i) => (
          <motion.div key={i} variants={item} whileHover={{ x: 4 }} className="glass-card px-5 py-4 flex items-center gap-4 group cursor-pointer">
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-medium group-hover:text-primary transition-colors">{a.title}</h3>
              <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
                <span className="font-medium text-foreground/70">{a.source}</span>
                <span className="px-1.5 py-0.5 rounded bg-white/5">{a.category}</span>
                <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{a.time}</span>
              </div>
            </div>
            <ExternalLink className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
