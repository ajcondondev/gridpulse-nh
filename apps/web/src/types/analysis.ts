export interface JoinedRow {
  date: string
  region: string | null
  daily_peak_mw: number | null
  temp_avg_f: number | null
  hdd: number | null
  cdd: number | null
  demand_source: string | null
  weather_source: string | null
  created_at: string | null
}
