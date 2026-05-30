"use client";

import { RiskAlert } from "@/lib/api";
import { ExternalLink, AlertTriangle, Shield, Info, Zap } from "lucide-react";

const SEVERITY_CONFIG = {
  LOW: {
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30",
    text: "text-emerald-400",
    badge: "bg-emerald-500/20 text-emerald-300",
    icon: Info,
    glow: "shadow-emerald-500/10",
  },
  MEDIUM: {
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    text: "text-amber-400",
    badge: "bg-amber-500/20 text-amber-300",
    icon: AlertTriangle,
    glow: "shadow-amber-500/10",
  },
  HIGH: {
    bg: "bg-orange-500/10",
    border: "border-orange-500/30",
    text: "text-orange-400",
    badge: "bg-orange-500/20 text-orange-300",
    icon: Shield,
    glow: "shadow-orange-500/10",
  },
  CRITICAL: {
    bg: "bg-red-500/10",
    border: "border-red-500/30",
    text: "text-red-400",
    badge: "bg-red-500/20 text-red-300",
    icon: Zap,
    glow: "shadow-red-500/20",
  },
};

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function truncateUrl(url: string, max = 60): string {
  if (url.length <= max) return url;
  try {
    const u = new URL(url);
    return u.hostname + (u.pathname.length > 20 ? u.pathname.substring(0, 20) + "…" : u.pathname);
  } catch {
    return url.substring(0, max) + "…";
  }
}

interface AlertCardProps {
  alert: RiskAlert;
}

export function AlertCard({ alert }: AlertCardProps) {
  const config = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.MEDIUM;
  const Icon = config.icon;

  return (
    <div
      className={`
        relative rounded-xl border p-5 transition-all duration-200
        hover:scale-[1.01] hover:shadow-lg
        ${config.bg} ${config.border} ${config.glow}
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className={`mt-0.5 shrink-0 ${config.text}`}>
            <Icon size={18} />
          </div>
          <h3 className="text-sm font-semibold text-slate-100 leading-snug line-clamp-2">
            {alert.title}
          </h3>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold tracking-wide ${config.badge}`}>
            {alert.severity}
          </span>
        </div>
      </div>

      {/* Incident Type */}
      <div className="mb-3">
        <span className={`text-xs font-medium uppercase tracking-wider ${config.text}`}>
          {alert.incident_type}
        </span>
      </div>

      {/* Summary */}
      <div className="mb-4">
        <p className="text-xs text-slate-400 leading-relaxed">{alert.summary}</p>
      </div>

      {/* Business Impact */}
      <div className="mb-3 p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
        <p className="text-xs text-slate-500 uppercase tracking-wide font-medium mb-1">
          Business Impact
        </p>
        <p className="text-xs text-slate-300 leading-relaxed">{alert.business_impact}</p>
      </div>

      {/* Recommended Action */}
      <div className="mb-4 p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
        <p className="text-xs text-slate-500 uppercase tracking-wide font-medium mb-1">
          Recommended Action
        </p>
        <p className="text-xs text-slate-300 leading-relaxed">{alert.recommended_action}</p>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-slate-700/50">
        <span className="text-xs text-slate-500 font-mono">{formatDate(alert.created_at)}</span>
        <a
          href={alert.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className={`flex items-center gap-1.5 text-xs ${config.text} hover:underline transition-colors`}
        >
          <span className="max-w-[180px] truncate">{truncateUrl(alert.source_url)}</span>
          <ExternalLink size={11} className="shrink-0" />
        </a>
      </div>
    </div>
  );
}
