import type { Dataset, DatasetList, DatasetPreview } from '../types/dataset'
import { apiClient, BASE_URL } from './apiClient'

export function getDatasets(): Promise<DatasetList> {
  return apiClient.get<DatasetList>('/datasets')
}

export function getDataset(id: string): Promise<Dataset> {
  return apiClient.get<Dataset>(`/datasets/${id}`)
}

export function getDatasetPreview(id: string, rows = 50): Promise<DatasetPreview> {
  return apiClient.get<DatasetPreview>(`/datasets/${id}/preview?rows=${rows}`)
}

export function cleanedDownloadUrl(id: string): string {
  return `${BASE_URL}/datasets/${id}/download/cleaned`
}

export function rawDownloadUrl(id: string): string {
  return `${BASE_URL}/datasets/${id}/download/raw`
}
