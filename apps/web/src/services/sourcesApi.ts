import type { Source, SourceList } from '../types/source'
import { apiClient } from './apiClient'

export function getSources(): Promise<SourceList> {
  return apiClient.get<SourceList>('/sources')
}

export function getSource(id: string): Promise<Source> {
  return apiClient.get<Source>(`/sources/${id}`)
}

export function fetchSource(id: string): Promise<unknown> {
  return apiClient.post(`/sources/${id}/fetch`)
}
