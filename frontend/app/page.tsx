"use client";

import { useState, useEffect, useCallback } from "react";
import { apiService, Vendor, DashboardStats } from "@/lib/api";
import { VendorTable } from "@/components/VendorTable";
import { LoadingPulse } from "@/components/LoadingPulse";
import {
  Shield,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Wifi,
  WifiOff,
} from "lucide-react";

const AUTO_REFRESH_INTERVAL = 30000;

interface StatCardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  color: string;
  sub?: string;
}

function StatCard({ label, value, icon, color, sub }: StatCardProps) {
  return (
    <div className="bg-[#111827] rounded-xl border border-slate-700/50 p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{label}</span>
        <div className={`${color} opacity-80`}>{icon}</div>
      </div>
      <div>
        <span className={`text-3xl font-bold tracking-tight ${color}`}>{value}</span>
        {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [apiOnline, setApiOnline] = useState(true);
  const [countdown, setCountdown] = useState(30);

  const fetchData = useCallback(async () => {
    try {
      const [vendorData, statsData] = await Promise.all([
        apiService.getVendors(),
        apiService.getStats(),
      ]);
      setVendors(vendorData);
      setStats(statsData);
      setError(null);
      setApiOnline(true);
      setLastRefresh(new Date());
      setCountdown(30);
    } catch (err: any) {
      setError(err.message || "Failed to fetch data");
      setApiOnline(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh
  useEffect(() => {
    const interval = setInterval(fetchData, AUTO_REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Countdown timer
  useEffect(() => {
    const tick = setInterval(() => {
      setCountdown((c) => (c <= 1 ? 30 : c - 1));
    }, 1000);
    return () => clearInterval(tick);
  }, []);

  const handleScan = async () => {
    setScanning(true);
    try {
      await apiService.triggerScan();
      setTimeout(fetchData, 2000);
    } catch (err: any) {
      setError(err.message || "Scan failed");
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="min-h-screen">
      {/* Nav */}
      <nav className="border-b border-slate-700/50 bg-[#0f172a]/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Shield className="text-cyan-400" size={24} />
              <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-slate-100">Sentinel AI</h1>
              <p className="text-xs text-slate-500 leading-none">Real-Time Vendor Risk Intelligence</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* API Status */}
            <div className="flex items-center gap-1.5 text-xs">
              {apiOnline ? (
                <>
                  <Wifi size={12} className="text-emerald-400" />
                  <span className="text-emerald-400 font-mono">LIVE</span>
                </>
              ) : (
                <>
                  <WifiOff size={12} className="text-red-400" />
                  <span className="text-red-400 font-mono">OFFLINE</span>
                </>
              )}
            </div>

            {/* Refresh countdown */}
            {lastRefresh && (
              <div className="text-xs text-slate-500 font-mono hidden sm:block">
                Refresh in {countdown}s
              </div>
            )}

            {/* Manual refresh */}
            <button
              onClick={fetchData}
              className="p-2 rounded-lg hover:bg-slate-800 transition-colors text-slate-400 hover:text-slate-100"
              title="Refresh"
            >
              <RefreshCw size={15} />
            </button>

            {/* Scan button */}
            <button
              onClick={handleScan}
              disabled={scanning}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-150
                ${scanning
                  ? "bg-cyan-500/20 text-cyan-400 cursor-wait"
                  : "bg-cyan-500 hover:bg-cyan-400 text-slate-900 hover:shadow-lg hover:shadow-cyan-500/25"
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
                  Scan Now
                </>
              )}
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Error banner */}
        {error && (
          <div className="mb-6 flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
            <XCircle size={16} className="shrink-0" />
            <span className="text-sm">{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-400/60 hover:text-red-400 text-xs"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Header */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-100 mb-1">Security Operations Center</h2>
          <p className="text-slate-500 text-sm">
            Continuous monitoring of third-party vendor risk signals
          </p>
        </div>

        {/* Stats Grid */}
        {loading ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-[#111827] rounded-xl border border-slate-700/50 p-5 animate-pulse h-28" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard
              label="Total Vendors"
              value={stats?.total_vendors ?? 0}
              icon={<Shield size={18} />}
              color="text-cyan-400"
              sub="Monitored vendors"
            />
            <StatCard
              label="Healthy"
              value={stats?.healthy ?? 0}
              icon={<CheckCircle size={18} />}
              color="text-emerald-400"
              sub="No active alerts"
            />
            <StatCard
              label="Warnings"
              value={stats?.warnings ?? 0}
              icon={<AlertTriangle size={18} />}
              color="text-amber-400"
              sub="Requires attention"
            />
            <StatCard
              label="Critical"
              value={stats?.critical ?? 0}
              icon={<XCircle size={18} />}
              color="text-red-400"
              sub="Immediate action"
            />
          </div>
        )}

        {/* Vendor Table */}
        <div className="bg-[#111827] rounded-xl border border-slate-700/50 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-700/50 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-100">Vendor Risk Matrix</h3>
              <p className="text-xs text-slate-500 mt-0.5">Click a vendor to view detailed alerts</p>
            </div>
            {lastRefresh && (
              <span className="text-xs text-slate-600 font-mono">
                Updated {lastRefresh.toLocaleTimeString()}
              </span>
            )}
          </div>

          {loading ? (
            <LoadingPulse message="Loading vendor data..." />
          ) : (
            <VendorTable vendors={vendors} />
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-slate-600">
          <span className="font-mono">
            Sentinel AI v1.0 • Powered by Bright Data + OpenAI • Auto-refresh every 30s
          </span>
        </div>
      </main>
    </div>
  );
}
