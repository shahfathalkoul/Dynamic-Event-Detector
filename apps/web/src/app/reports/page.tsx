"use client";
import { motion } from "framer-motion";
import { FileText, Clock, Shield, ArrowUpRight } from "lucide-react";
import Link from "next/link";

const REPORTS = [
  { id: "rpt-1", title: "Executive Brief: AI Chip Supply Constraint Analysis", type: "event_analysis", confidence: 0.92, citations: 12, event: "AI Chip Shortage", time: "2h ago", status: "published" },
  { id: "rpt-2", title: "Risk Assessment: European Manufacturing Disruption", type: "risk_assessment", confidence: 0.88, citations: 15, event: "Supply Chain Disruption", time: "5h ago", status: "approved" },
  { id: "rpt-3", title: "Trend Analysis: Renewable Energy Investment Patterns", type: "trend_analysis", confidence: 0.78, citations: 8, event: "Energy Investment", time: "8h ago", status: "draft" },
  { id: "rpt-4", title: "Daily Intelligence Briefing — June 28, 2026", type: "daily_brief", confidence: 0.85, citations: 24, event: "Multiple", time: "12h ago", status: "published" },
  { id: "rpt-5", title: "Central Bank Policy Impact — Emerging Markets Q2", type: "impact_analysis", confidence: 0.72, citations: 10, event: "Central Bank Policy", time: "1d ago", status: "review" },
];

const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export default function ReportsPage() {
  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      <motion.div variants={item}>
        <h1 className="text-2xl font-bold flex items-center gap-2"><FileText className="w-6 h-6 text-emerald-400" /> Executive Reports</h1>
        <p className="text-sm text-muted-foreground mt-1">AI-generated intelligence reports with source-grounded citations</p>
      </motion.div>
      <div className="grid gap-4">
        {REPORTS.map((report) => (
          <motion.div key={report.id} variants={item} whileHover={{ scale: 1.005, x: 4 }} className="glass-card p-5 cursor-pointer group">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                    report.status === 'published' ? 'bg-emerald-500/20 text-emerald-400' :
                    report.status === 'approved' ? 'bg-blue-500/20 text-blue-400' :
                    report.status === 'review' ? 'bg-amber-500/20 text-amber-400' :
                    'bg-white/10 text-muted-foreground'
                  }`}>{report.status}</span>
                  <span className="text-[10px] text-muted-foreground">{report.type.replace(/_/g, ' ')}</span>
                </div>
                <h3 className="text-base font-semibold group-hover:text-primary transition-colors">{report.title}</h3>
                <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1"><Shield className="w-3 h-3" /> {report.citations} citations</span>
                  <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {report.time}</span>
                  <span className="px-2 py-0.5 rounded bg-white/5">{report.event}</span>
                </div>
              </div>
              <div className={`text-lg font-bold ${report.confidence >= 0.85 ? 'text-emerald-400' : report.confidence >= 0.7 ? 'text-amber-400' : 'text-red-400'}`}>
                {(report.confidence * 100).toFixed(0)}%
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
