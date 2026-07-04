import { useEffect, useRef, useState } from 'react'

/** Recessive chart chrome shared by every story chart. */
export const INK_MUTED = '#898781'
export const INK_PRIMARY = '#0b0b0b'
export const GRID_HAIRLINE = '#e1e0d9'

/**
 * Fuel palette. The six real fuels were validated with the dataviz
 * six-checks script in stack-adjacency order (all PASS: chroma, CVD ΔE 23.8
 * worst adjacent, ≥3:1 contrast on white). "other" is a deliberate neutral
 * for the residual bucket (coal + storage + misc) and is directly labeled.
 */
export const FUEL_ORDER = [
  'nuclear',
  'hydro',
  'natural_gas',
  'wind',
  'solar',
  'oil',
  'other',
] as const

export type FuelKey = (typeof FUEL_ORDER)[number]

export const FUEL_COLORS: Record<FuelKey, string> = {
  nuclear: '#6d28d9',
  hydro: '#2a78d6',
  natural_gas: '#eb6834',
  wind: '#0891b2',
  solar: '#c98500',
  oil: '#b91c1c',
  other: '#6b7280',
}

export const FUEL_LABELS: Record<FuelKey, string> = {
  nuclear: 'Nuclear',
  hydro: 'Hydro',
  natural_gas: 'Natural gas',
  wind: 'Wind',
  solar: 'Solar',
  oil: 'Oil',
  other: 'Other',
}

/** Sequential blue ramp (light→dark) for magnitude encodings (heatmap). */
export const SEQ_BLUES = [
  '#cde2fb',
  '#9ec5f4',
  '#6da7ec',
  '#3987e5',
  '#256abf',
  '#184f95',
  '#0d366b',
]

/** Observe a container's width for responsive Plot re-renders. */
export function useContainerWidth(initial = 720) {
  const ref = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(initial)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const observer = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width
      if (w) setWidth(Math.round(w))
    })
    observer.observe(el)
    return () => observer.disconnect()
  }, [])
  return { ref, width }
}

export function formatLocalHour(tsUtc: string): string {
  return new Date(tsUtc).toLocaleString('en-US', {
    timeZone: 'America/New_York',
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
  })
}
