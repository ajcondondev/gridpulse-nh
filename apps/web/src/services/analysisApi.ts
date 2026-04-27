import type { Dataset } from '../types/dataset'
import { apiClient, BASE_URL } from './apiClient'

export function getLatestJoin(): Promise<Dataset> {
  return apiClient.get<Dataset>('/analysis/weather-demand/latest')
}

export function createJoin(): Promise<Dataset> {
  return apiClient.post<Dataset>('/analysis/weather-demand/join')
}

export function joinDownloadUrl(joinId: string): string {
  return `${BASE_URL}/analysis/weather-demand/${joinId}/download`
}
