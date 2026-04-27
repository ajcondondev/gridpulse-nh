export interface Dataset {
  id: string
  source_id: string
  name: string
  fetched_at?: string
  row_count?: number
  columns?: string[]
  raw_path?: string
  cleaned_path?: string
  status: string
}

export interface DatasetList {
  datasets: Dataset[]
  total: number
}

export interface DatasetPreview {
  columns: string[]
  rows: Record<string, unknown>[]
  preview_row_count: number
  total_row_count: number | null
}
