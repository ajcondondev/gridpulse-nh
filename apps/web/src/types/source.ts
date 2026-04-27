export type SourceStatus =
  | 'active'
  | 'requires_key'
  | 'manual_import'
  | 'planned'
  | 'research'
  | 'not_implemented'
  | 'mock'

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
  requires_api_key?: boolean
  auth_type?: string
  access_method?: string
  data_geography?: string
  phase_added?: number
  last_verified?: string
  is_real_data?: boolean
  is_mock_data?: boolean
}

export interface SourceList {
  sources: Source[]
  total: number
}
