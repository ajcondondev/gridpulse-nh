export type SourceStatus = 'active' | 'unavailable' | 'mock' | 'planned'

export type SourceCategory =
  | 'electricity'
  | 'weather'
  | 'ev'
  | 'environmental'
  | 'resilience'
  | 'gis'
  | 'regulatory'

export interface Source {
  id: string
  name: string
  description: string
  category: SourceCategory
  status: SourceStatus
  url?: string
  update_frequency?: string
  data_format?: string
  notes?: string
}

export interface SourceList {
  sources: Source[]
  total: number
}
