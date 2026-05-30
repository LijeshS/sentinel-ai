import axios, { AxiosInstance } from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "Unknown error occurred";
    return Promise.reject(new Error(message));
  }
);

export interface Vendor {
  id: number;
  name: string;
  status: string;
  last_checked: string | null;
  alert_count: number;
  highest_severity: string | null;
}

export interface RiskAlert {
  id: number;
  vendor_id: number;
  title: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  incident_type: string;
  summary: string;
  business_impact: string;
  recommended_action: string;
  source_url: string;
  created_at: string;
}

export interface VendorDetail extends Vendor {
  alerts: RiskAlert[];
}

export interface DashboardStats {
  total_vendors: number;
  healthy: number;
  warnings: number;
  critical: number;
  total_alerts: number;
}

export interface ScanResult {
  vendor: string;
  alerts_found: number;
  status: string;
  message: string;
}

export const apiService = {
  async getVendors(): Promise<Vendor[]> {
    const res = await api.get<Vendor[]>("/vendors");
    return res.data;
  },

  async getVendor(id: number): Promise<VendorDetail> {
    const res = await api.get<VendorDetail>(`/vendors/${id}`);
    return res.data;
  },

  async getAlerts(params?: {
    severity?: string;
    vendor_id?: number;
    limit?: number;
  }): Promise<RiskAlert[]> {
    const res = await api.get<RiskAlert[]>("/alerts", { params });
    return res.data;
  },

  async getStats(): Promise<DashboardStats> {
    const res = await api.get<DashboardStats>("/stats");
    return res.data;
  },

  async triggerScan(vendor_id?: number): Promise<ScanResult[]> {
    const res = await api.post<ScanResult[]>("/scan", null, {
      params: vendor_id ? { vendor_id } : undefined,
    });
    return res.data;
  },

  async checkHealth(): Promise<{ status: string; db_connected: boolean }> {
    const res = await api.get("/health");
    return res.data;
  },
};

export default apiService;
