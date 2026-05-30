"use client";

import { Vendor } from "@/lib/api";
import { useRouter } from "next/navigation";
import { ChevronRight, Clock, AlertCircle } from "lucide-react";

const STATUS_CONFIG: Record<string, { dot: string; text: string; bg: string }> = {
  Healthy: {
    dot: "bg-emerald-400 shadow-emerald-400/50",
    text: "text-emerald-400",
    bg: "bg-emerald-500/10",
  },
  Warning: {
    dot: "bg-amber-400 shadow-amber-400/50",
    text: "text-amber-400",
    bg: "bg-amber-500/10",
  },
  "High Alert": {
    dot: "bg-orange-400 shadow-orange-400/50 animate-pulse",
    text: "text-orange-400",
    bg: "bg-orange-500/10",
  },
  Critical: {
    dot: "bg-red-400 shadow-red-400/50 animate-pulse",
    text: "text-red-400",
    bg: "bg-red-500/10",
  },
};

const SEVERITY_COLORS: Record<string, string> = {
  LOW: "text-emerald-400 bg-emerald-500/10",
  MEDIUM: "text-amber-400 bg-amber-500/10",
  HIGH: "text-orange-400 bg-orange-500/10",
  CRITICAL: "text-red-400 bg-red-500/10",
};

function formatRelativeTime(iso: string | null): string {
  if (!iso) return "Never";
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h ago`;
  return `${Math.floor(diffH / 24)}d ago`;
}

interface VendorTableProps {
  vendors: Vendor[];
  loading?: boolean;
}

export function VendorTable({ vendors, loading }: VendorTableProps) {
  const router = useRouter();

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-700/50 overflow-hidden">
        <table className="w-full">
          <thead>
            <TableHead />
          </thead>
          <tbody>
            {[...Array(7)].map((_, i) => (
              <tr key={i} className="border-t border-slate-700/30">
                {[...Array(4)].map((_, j) => (
                  <td key={j} className="px-6 py-4">
                    <div className="h-4 bg-slate-700/60 rounded animate-pulse" />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-700/50 overflow-hidden">
      <table className="w-full">
        <thead>
          <TableHead />
        </thead>
        <tbody>
          {vendors.map((vendor, idx) => {
            const statusCfg = STATUS_CONFIG[vendor.status] || STATUS_CONFIG["Healthy"];
            const severityColor = vendor.highest_severity
              ? SEVERITY_COLORS[vendor.highest_severity]
              : "";

            return (
              <tr
                key={vendor.id}
                onClick={() => router.push(`/vendors/${vendor.id}`)}
                className={`
                  border-t border-slate-700/30 cursor-pointer
                  transition-all duration-150
                  hover:bg-slate-800/60
                  ${idx % 2 === 0 ? "bg-slate-900/20" : "bg-transparent"}
                `}
              >
                {/* Vendor Name */}
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold text-slate-100 ${statusCfg.bg}`}
                    >
                      {vendor.name.substring(0, 2).toUpperCase()}
                    </div>
                    <span className="text-sm font-semibold text-slate-100">{vendor.name}</span>
                  </div>
                </td>

                {/* Status */}
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-block w-2 h-2 rounded-full shadow-sm ${statusCfg.dot}`}
                    />
                    <span className={`text-sm font-medium ${statusCfg.text}`}>{vendor.status}</span>
                  </div>
                </td>

                {/* Last Checked */}
                <td className="px-6 py-4">
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <Clock size={13} />
                    <span className="text-sm font-mono">{formatRelativeTime(vendor.last_checked)}</span>
                  </div>
                </td>

                {/* Risk Level */}
                <td className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {vendor.alert_count > 0 && (
                        <div className="flex items-center gap-1.5">
                          <AlertCircle size={13} className="text-slate-400" />
                          <span className="text-sm text-slate-400">{vendor.alert_count} alerts</span>
                        </div>
                      )}
                      {vendor.highest_severity && (
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-bold ${severityColor}`}
                        >
                          {vendor.highest_severity}
                        </span>
                      )}
                      {!vendor.highest_severity && (
                        <span className="text-sm text-slate-500">—</span>
                      )}
                    </div>
                    <ChevronRight size={16} className="text-slate-600 ml-4" />
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {vendors.length === 0 && (
        <div className="text-center py-16 text-slate-500">
          <AlertCircle className="mx-auto mb-3 opacity-40" size={32} />
          <p className="text-sm">No vendors found</p>
        </div>
      )}
    </div>
  );
}

function TableHead() {
  return (
    <tr className="bg-slate-800/60">
      {["Vendor", "Status", "Last Checked", "Risk Level"].map((h) => (
        <th
          key={h}
          className="px-6 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider"
        >
          {h}
        </th>
      ))}
    </tr>
  );
}
