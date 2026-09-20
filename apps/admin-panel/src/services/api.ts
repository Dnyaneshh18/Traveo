/**
 * Traveo Admin API Client — Operations & Dashboard Service
 * Connects Admin Panel to FastAPI Admin Endpoints
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

class AdminApiService {
  private token: string | null = null;

  setAuthToken(token: string) {
    this.token = token;
  }

  private getHeaders() {
    return {
      'Content-Type': 'application/json',
      ...(this.token ? { Authorization: `Bearer ${this.token}` } : {}),
    };
  }

  // 1. Get Dashboard KPIs
  async getDashboardKPIs() {
    const response = await fetch(`${API_BASE_URL}/admin/dashboard/kpis`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    return await response.json();
  }

  // 2. Driver Review / Approval
  async reviewDriver(driverId: string, status: 'approved' | 'rejected', notes?: string) {
    const response = await fetch(`${API_BASE_URL}/admin/drivers/${driverId}/review`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ status, notes }),
    });
    return await response.json();
  }

  // 3. System Configuration Update
  async updateConfig(key: string, value: string, description?: string) {
    const response = await fetch(`${API_BASE_URL}/admin/configuration`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ key, value, description }),
    });
    return await response.json();
  }

  // 4. Audit Logs
  async getAuditLogs() {
    const response = await fetch(`${API_BASE_URL}/admin/audit-logs`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    return await response.json();
  }
}

export const adminApiService = new AdminApiService();
