"use client";
import { motion } from "framer-motion";
import { Globe } from "lucide-react";
const item = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } };
const REGIONS = [
  { name: "North America", events: 8, severity: "high" },
  { name: "Europe", events: 6, severity: "high" },
  { name: "East Asia", events: 5, severity: "medium" },
  { name: "Southeast Asia", events: 4, severity: "medium" },
  { name: "Middle East", events: 3, severity: "low" },
  { name: "Latin America", events: 2, severity: "low" },
];
export default function MapPage() {
  return (
    <motion.div initial="hidden" animate="show" variants={{ hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } }} className="space-y-6">
      <motion.div variants={item}><h1 className="text-2xl font-bold flex items-center gap-2"><Globe className="w-6 h-6 text-cyan-400" /> World Event Map</h1><p className="text-sm text-muted-foreground mt-1">Geographic distribution of detected events</p></motion.div>
      <motion.div variants={item} className="glass-card p-8 flex items-center justify-center min-h-[400px]">
        <div className="text-center"><Globe className="w-16 h-16 text-muted-foreground/30 mx-auto mb-4 animate-float" /><p className="text-sm text-muted-foreground">Interactive world map renders here with event markers</p><p className="text-xs text-muted-foreground/60 mt-1">Powered by react-simple-maps or Mapbox GL</p></div>
      </motion.div>
      <div className="grid gap-3 md:grid-cols-3">
        {REGIONS.map(r => (
          <motion.div key={r.name} variants={item} className="glass-card p-4">
            <div className="flex items-center justify-between"><span className="text-sm font-medium">{r.name}</span><span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${r.severity === 'high' ? 'severity-high' : r.severity === 'medium' ? 'severity-medium' : 'severity-low'}`}>{r.severity}</span></div>
            <p className="text-2xl font-bold mt-1">{r.events}</p><p className="text-xs text-muted-foreground">active events</p>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
