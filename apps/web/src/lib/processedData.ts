/**
 * Typed access to the committed pipeline artifacts in data/processed
 * (aliased as @data). These are static imports: the story pages work with
 * zero backend and zero API keys.
 */
import metaJson from '@data/meta.json'
import tempDemandJson from '@data/temp_demand_daily.json'

export interface TempDemandDay {
  date: string
  peak_mw: number
  avg_mw: number
  temp_avg_f: number
  temp_min_f: number
  temp_max_f: number
  hdd: number
  cdd: number
}

export interface ProcessedMeta {
  generated_at: string
  region: string
  coverage: { start: string; end: string; days: number }
  sources: {
    id: string
    name: string
    url: string
    license_note: string
    caveat: string
  }[]
  disclaimer: string
}

export type Season = 'winter' | 'spring' | 'summer' | 'fall'

export function seasonOf(dateIso: string): Season {
  const month = Number(dateIso.slice(5, 7))
  if (month === 12 || month <= 2) return 'winter'
  if (month <= 5) return 'spring'
  if (month <= 8) return 'summer'
  return 'fall'
}

export const meta = metaJson as ProcessedMeta

export const tempDemandDaily: (TempDemandDay & { season: Season })[] = (
  tempDemandJson as TempDemandDay[]
).map((d) => ({ ...d, season: seasonOf(d.date) }))
