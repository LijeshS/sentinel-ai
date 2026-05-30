"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiService, VendorDetail } from "@/lib/api";
import { AlertCard } from "@/components/AlertCard";
import { LoadingPulse } from "@/components/LoadingPulse";
import {
  Shield,
  ArrowLeft,
  RefreshCw,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  XCircle,
} from "lucide-react";

const STATUS_CONFIG: Record<string, { text: string; icon: React.ReactNode; color: string; border: string }> = {
  Healthy: {
    text: "Healthy",
    icon: <CheckCircle size={16} />,
    color: "text-emerald-400",
    border: "border-emerald-500/30",
  },
  Warning: {
    text: "Warning",
    icon: <AlertTriangle size={16} />,
    color: "text-amber-400",
    border: "border-amber-500/30",
  },
  "High Alert": {
    text: "High Alert",
    icon: <AlertTriangle size={16} />,
    color: "text-orange-400",
    border: "border-orange-500/30",
  },
  Critical: {
    text: "Critical",
    icon: <XCircle size={16} />,
    color: "text-red-400",
    border: "border-red-500/30",
  },
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function VendorDetailPage() {
  const params = useParams();
  const router = useRouter();
  const vendorId = Number(params.id);

  const [vendor, setVendor] = useState<VendorDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchVendor = useCallback(async () => {
    try {
      const data = await apiService.getVendor(vendorId);
      setVendor(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to fetch vendor");
    } finally {
      setLoading(false);
    }
  }, [vendorId]);

  useEffect(() => {
    fetchVendor();
  }, [fetchVendor]);

  const handleScan = async () => {
    setScanning(true);
    try {
      await apiService.triggerScan(vendorId);
      setTimeout(fetchVendor, 2000);
    } catch (err: any) {
      setError(err.message || "Scan failed");
    } finally {
      setScanning(false);
    }
  };

  const statusCfg = vendor ? STATUS_CONFIG[vendor.status] || STATUS_CONFIG["Healthy"] : null;

  return (
    <div className="min-h-screen">
      {/* Nav */}
      <nav className="border-b border-slate-700/50 bg-[#0f172a]/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => router.push("/")}
              className="flex items-center gap-2 text-slate-400 hover:text-slate-100 transition-colors text-sm"
            >
              <ArrowLeft size={16} />
              <span>Dashboard</span>
            </button>
            <span className="text-slate-700">/</span>
            <div className="flex items-center gap-2">
              <Shield className="text-cyan-400" size={18} />
              <span className="font-semibold text-slate-100">
                {vendor?.name || "Loading..."}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchVendor}
              className="p-2 rounded-lg hover:bg-slate-800 transition-colors text-slate-400 hover:text-slate-100"
            >
              <RefreshCw size={15} />
            </button>
            <button
              onClick={handleScan}
              disabled={scanning}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all
                ${scanning
                  ? "bg-cyan-500/20 text-cyan-400 cursor-wait"
                  : "bg-cyan-500 hover:bg-cyan-400 text-slate-900"
                }
              `}
            >
              {scanning ? (
                <>
                  <Activity size={14} className="animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <Activity size={14} />
                  Scan Vendor
                </>
              )}
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* Error */}
        {error && (
          <div className="mb-6 flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
            <XCircle size={16} />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {loading ? (
          <LoadingPulse message="AI Investigating..." />
        ) : vendor ? (
          <>
            {/* Vendor Header */}
            <div className={`bg-[#111827] rounded-xl border p-6 mb-8 ${statusCfg?.border || "border-slate-700/50"}`}>
              <div className="flex items-start justify-between flex-wrap gap-4">
                <div className="flex items-center gap-4">
                  <div
                    className={`w-14 h-14 rounded-xl flex items-center justify-center text-lg font-bold text-slate-100 bg-slate-800 border ${statusCfg?.border || "border-slate-700"}`}
                  >
                    {vendor.name.substring(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-slate-100">{vendor.name}</h2>
                    <div className={`flex items-center gap-1.5 mt-1 ${statusCfg?.color}`}>
                      {statusCfg?.icon}
                      <span className="text-sm font-semibold">{vendor.status}</span>
                    </div>
                  </div>
                </div>

                <div className="flex gap-6">
                  <div className="text-right">
                    <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Total Alerts</p>
                    <p className="text-2xl font-bold text-slate-100">{vendor.alert_count}</p>
                  </div>
                  {vendor.last_checked && (
                    <div className="text-right">
                      <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Last Scanned</p>
                      <div className="flex items-center gap-1.5 text-slate-400 text-sm font-mono">
                        <Clock size={12} />
                        {formatDate(vendor.last_checked)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Alerts Timeline */}
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                Alert Timeline
              </h3>
              <span className="text-xs text-slate-600 font-mono">{vendor.alerts.length} events</span>
            </div>

            {vendor.alerts.length === 0 ? (
              <div className="flex flex-col items-center py-20 text-slate-600">
                <CheckCircle className="mb-3 opacity-40" size={40} />
                <p className="text-sm font-medium text-slate-500">No risk alerts detected</p>
                <p className="text-xs text-slate-600 mt-1">
                  This vendor appears clean. Scans run every 5 minutes.
                </p>
              </div>
            ) : (
              <div className="grid gap-4">
                {vendor.alerts.map((alert) => (
                  <AlertCard key={alert.id} alert={alert} />
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-20 text-slate-500">
            <Shield className="mx-auto mb-3 opacity-30" size={40} />
            <p>Vendor not found</p>
          </div>
        )}
      </main>
    </div>
  );
}
