"use client";

import { motion } from "framer-motion";
import { TrendingUp } from "lucide-react";

const VELOCITY_HISTORY = [
  { topic: "AI Semiconductors", data: [1.2, 1.8, 2.4, 3.1, 4.5, 6.2, 7.8, 8.4], trend: "accelerating", anomaly: 3.2 },
  { topic: "Monetary Policy", data: [2.1, 2.3, 2.5, 3.0, 3.8, 4.5, 5.6, 6.2], trend: "accelerating", anomaly: 2.4 },
  { topic: "Clean Energy", data: [3.2, 3.4, 3.8, 4.0, 4.2, 4.5, 4.6, 4.8], trend: "stable", anomaly: 1.3 },
  { topic: "Supply Chain", data: [5.8, 5.2, 4.8, 4.4, 4.0, 3.8, 3.6, 3.6], trend: "decaying", anomaly: 0.8 },
  { topic: "Cybersecurity", data: [2.0, 2.2, 2.8, 3.4, 3.6, 3.4, 3.2, 3.1], trend: "decaying", anomaly: 0.9 },
  { topic: "Trade Relations", data: [2.4, 2.5, 2.6, 2.7, 2.8, 2.8, 2.9, 2.9], trend: "stable", anomaly: 1.1 },
];

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.08 } } };
const item = { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } };

function Sparkline({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const width = 200;
  const height = 40;

  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * height;
    return `${x},${y}`;
  }).join(" ");

  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id={`grad-${color}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline fill="none" stroke={color} strokeWidth="2" points={points} strokeLinecap="round" strokeLinejoin="round" />
      <polygon fill={`url(#grad-${color})`} points={`0,${height} ${points} ${width},${height}`} />
      <circle cx={(data.length - 1) / (data.length - 1) * width} cy={height - ((data[data.length - 1] - min) / range) * height} r="3" fill={color} />
    </svg>
  );
}

export default function VelocityPage() {
  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      <motion.div variants={item}>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-amber-400" /> Semantic Velocity
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Topic attention acceleration and anomaly detection</p>
      </motion.div>

      <div className="grid gap-4">
        {VELOCITY_HISTORY.map((topic) => {
          const sparkColor =
            topic.trend === "accelerating" ? "#f97316" :
            topic.trend === "stable" ? "#3b82f6" : "#6b7280";
          const current = topic.data[topic.data.length - 1];

          return (
            <motion.div key={topic.topic} variants={item} className="glass-card p-5">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-base font-semibold">{topic.topic}</h3>
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                      topic.trend === 'accelerating' ? 'bg-orange-500/20 text-orange-400' :
                      topic.trend === 'stable' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {topic.trend}
                    </span>
                    {topic.anomaly > 2 && (
                      <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 animate-pulse">
                        SPIKE
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                    <span>Velocity: <strong className="text-foreground">{current.toFixed(1)}</strong></span>
                    <span>Anomaly: <strong className={topic.anomaly > 2 ? 'text-red-400' : 'text-foreground'}>{topic.anomaly.toFixed(1)}x</strong></span>
                  </div>
                </div>
                <Sparkline data={topic.data} color={sparkColor} />
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}
