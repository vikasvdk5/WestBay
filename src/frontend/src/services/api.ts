import axios, { AxiosInstance } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

class APIService {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 300000, // 5 minutes
    })
  }

  // Submit report requirements
  async submitRequirements(userRequest: string, requirements: any) {
    const response = await this.client.post('/submit-requirements', {
      user_request: userRequest,
      requirements,
    })
    return response.data
  }

  // Get cost estimate
  async getCostEstimate(sessionId: string) {
    const response = await this.client.get(`/cost-estimate/${sessionId}`)
    return response.data
  }

  // Get report structure preview
  async getReportStructure(sessionId: string) {
    const response = await this.client.get(`/preview-structure/${sessionId}`)
    return response.data
  }

  // Generate report
  async generateReport(sessionId: string, confirmedStructure?: any) {
    const response = await this.client.post('/generate-report', {
      session_id: sessionId,
      confirmed_structure: confirmedStructure,
    })
    return response.data
  }

  // Get report status
  async getReportStatus(sessionId: string) {
    const response = await this.client.get(`/report-status/${sessionId}`)
    return response.data
  }

  // Get final report
  async getReport(sessionId: string) {
    const response = await this.client.get(`/report/${sessionId}`)
    return response.data
  }

  // Download PDF
  getPdfDownloadUrl(sessionId: string): string {
    return `${API_BASE_URL}/report/${sessionId}/pdf`
  }
}

export const apiService = new APIService()
export default apiService

