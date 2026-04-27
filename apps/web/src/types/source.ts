export type SourceStatus =
  | 'active'
  | 'requires_key'
  | 'manual_import'
  | 'planned'
  | 'research'
  | 'not_implemented'
  | 'test_fixture_only'

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
  api_key_env_var?: string
  auth_type?: string
  access_type?: string
  data_geography?: string
  connector_implemented?: boolean
  phase_added?: number
  last_verified?: string
  is_real_data?: boolean
  is_mock_data?: boolean
}

export interface SourceList {
  sources: Source[]
  total: number
}
